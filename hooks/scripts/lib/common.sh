#!/bin/bash
# Vellum hook shared library.
# Adapted from oh-story-claudecode/skills/story-setup/references/templates/hooks/lib/common.sh - MIT.
# Changes: translated to English; dropped the Chinese active-book discovery logic; kept
# CLAUDE_PROJECT_DIR -> git-root -> cwd resolution and the LC_ALL=C byte-matching lessons as
# comments; added vellum_py() interpreter resolution (spec section 1), drive-letter path
# normalization, the shared gate-1 predicate, and frontmatter/current-chapter helpers.

# LC_ALL=C everywhere (oh-story lesson, their issue #164): this library runs byte-stable
# matching (case patterns, sed, grep) on paths and file content that may be UTF-8. Under a
# non-UTF-8 locale (cp936/GBK on Chinese Windows) sed/grep decode each line as multibyte and
# every literal-vs-byte comparison silently fails. Forcing C locale makes matching byte-based
# and stable. Never rely on locale-dependent character classes with non-ASCII input.

export LC_ALL=C

# ---------------------------------------------------------------------------
# Never export the tool payload (oh-story E2BIG lesson): Write/Edit/MultiEdit
# hook payloads carry whole chapters (MultiEdit also carries old_string +
# new_string). Exporting the payload into the environment of every subprocess
# makes execve fail with E2BIG (128 KiB per env var on Linux, ~1 MiB total on
# macOS) long before the guard reaches its decision - the blocking gate then
# dies as a "non-blocking error" and lets the write through. All hooks in this
# plugin keep the payload in a shell variable and pipe it to the interpreter
# via stdin only where it is needed.
# ---------------------------------------------------------------------------

# Plugin layout: this file lives at <plugin>/hooks/scripts/lib/common.sh.
#   COMMON_DIR         = .../plugin/hooks/scripts/lib
#   HOOKS_SCRIPTS      = .../plugin/hooks/scripts  (prose_core.py lives here)
#   VELLUM_SCRIPTS_DIR = .../plugin/scripts       (the engine entry + vellum_lib)
# Going up three from lib/: lib -> scripts -> hooks -> plugin, then back down to scripts/.
COMMON_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
HOOKS_SCRIPTS_DIR="$(cd "$COMMON_DIR/.." && pwd)"
VELLUM_SCRIPTS_DIR="$(cd "$COMMON_DIR/../../.." && pwd)/scripts"
VELLUM_ENGINE="${VELLUM_ENGINE_OVERRIDE:-$VELLUM_SCRIPTS_DIR/vellum}"
VELLUM_PROSE_CORE="${VELLUM_PROSE_CORE_OVERRIDE:-$HOOKS_SCRIPTS_DIR/prose_core.py}"

# project_root - stable resolution of the author's project root.
# Prefer CLAUDE_PROJECT_DIR (injected by Claude Code), then the git root, then
# cwd. Always prints an absolute path so a hook spawned from a nested cwd
# cannot misread or miswrite state.
project_root() {
  if [ -n "${CLAUDE_PROJECT_DIR:-}" ] && [ -d "$CLAUDE_PROJECT_DIR" ]; then
    (cd "$CLAUDE_PROJECT_DIR" 2>/dev/null && pwd -P) && return
  fi
  local git_root
  git_root=$(git rev-parse --show-toplevel 2>/dev/null || true)
  if [ -n "$git_root" ] && [ -d "$git_root" ]; then
    (cd "$git_root" 2>/dev/null && pwd -P) && return
  fi
  pwd -P
}

# normalize_target <path> - print a normalized absolute path.
# Portability lessons (oh-story issue #184): on Windows + Git Bash, Claude Code
# may pass drive-letter absolute paths (C:/work/... or C:\work\...). Matching
# only /* treats them as relative and joins them onto $ROOT, pointing the gate
# at a nonexistent directory (open gate on the wrong path). So:
#   - unify backslashes to forward slashes first
#   - [A-Za-z]:[/] prefix is absolute (drive-letter branch)
#   - leading / is absolute
#   - anything else is resolved against the project root
normalize_target() {
  local path="$1"
  path="${path//\\//}"
  path="${path%\"}"; path="${path#\"}"
  path="${path%\'}"; path="${path#\'}"
  case "$path" in
    /*) printf '%s\n' "$path" ;;
    [A-Za-z]:[/]*) printf '%s\n' "$path" ;;
    "") return 1 ;;
    *)
      # Reject clearly non-path values (variables, command substitution) - fail open.
      case "$path" in
        '$'*|'`'*) return 1 ;;
      esac
      printf '%s/%s\n' "$(project_root)" "$path" ;;
  esac
}

# Single source of truth for the engine interpreter (spec section 1).
# Tries python3, python, "py -3"; each candidate must pass a >= 3.8 probe.
# "py -3" is a two-word command: it must be probed and later invoked WITHOUT
# word-splitting into a single executable name (a quoted "$py" with
# py="py -3" looks for an executable literally named "py -3"). Use vellum_run
# for invocation; it handles the two-word candidate.
vellum_py() {
  local c
  for c in python3 python "py -3"; do
    if command -v ${c% *} >/dev/null 2>&1; then
      if vellum_run "$c" -c 'import sys; sys.exit(0 if sys.version_info >= (3,8) else 1)' 2>/dev/null; then
        printf '%s\n' "$c"
        return 0
      fi
    fi
  done
  return 1
}

# vellum_run <interpreter-string> <args...> - run args with the resolved
# interpreter, handling the two-word "py -3" candidate (Windows py launcher).
vellum_run() {
  local py="$1"
  shift
  if [ "$py" = "py -3" ]; then
    py -3 "$@"
  else
    "$py" "$@"
  fi
}

# read_hook_input - consume the hook JSON payload from stdin into HOOK_INPUT.
# Deliberately NOT exported (see E2BIG comment above). Also captures
# transcript_path into HOOK_TRANSCRIPT_PATH for subagent detection.
read_hook_input() {
  HOOK_INPUT=""
  HOOK_TRANSCRIPT_PATH=""
  if [ ! -t 0 ]; then
    HOOK_INPUT="$(cat)"
    HOOK_TRANSCRIPT_PATH="$(extract_payload_field transcript_path 2>/dev/null || true)"
  fi
}

# extract_payload_field <key> - pure-bash JSON string extraction fallback.
# Claude Code hook payloads are JSON.stringify output: non-ASCII paths stay raw
# UTF-8 (no \uXXXX), Windows drive paths carry \\ escapes. Grab the first
# string value for the key and unescape the two escapes that matter for paths.
extract_payload_field() {
  local key="$1" val
  val="$(printf '%s' "${HOOK_INPUT:-}" \
    | grep -oE "\"$key\"[[:space:]]*:[[:space:]]*\"([^\"\\\\]|\\\\.)*\"" \
    | head -n1 \
    | sed -E "s/^\"$key\"[[:space:]]*:[[:space:]]*\"//; s/\"\$//")"
  [ -n "$val" ] || return 1
  val="${val//\\\"/\"}"   # \" -> "
  val="${val//\\\\/\\}"   # \\ -> \
  printf '%s\n' "$val"
}

# fm_field <file> <field> - print a scalar frontmatter value ("" if absent).
# Tolerates a UTF-8 BOM and CRLF endings (H's hook tests cover both), and
# strips an inline comment (`approved: true   # author acceptance ...`) so the
# shipped outline contract's commented fields parse as their bare value.
# Comment stripping respects single/double-quoted values.
fm_field() {
  awk -v field="$2" '
    NR==1 { sub(/^\xef\xbb\xbf/, "") }
    NR==1 && /^---[[:space:]]*\r?$/ { infm=1; next }
    infm==1 {
      if (/^---[[:space:]]*\r?$/) { exit }
      idx = index($0, ":")
      if (idx > 0) {
        key = $0
        sub(/:.*/, "", key)
        gsub(/^[[:space:]]+|[[:space:]]+$/, "", key)
        if (key == field) {
          val = substr($0, idx + 1)
          # strip inline comments outside quotes
          out = ""
          in_s = 0; in_d = 0
          n = length(val)
          for (i = 1; i <= n; i++) {
            c = substr(val, i, 1)
            if (c == "\x27" && !in_d) { in_s = !in_s; out = out c }
            else if (c == "\"" && !in_s) { in_d = !in_d; out = out c }
            else if (c == "#" && !in_s && !in_d) { break }
            else out = out c
          }
          gsub(/^[[:space:]]+|[[:space:]]+$/, "", out)
          print out
          exit
        }
      }
    }
  ' "$1" 2>/dev/null
}

# strip_frontmatter <file> - print the body (everything after the closing ---).
# Unclosed or absent frontmatter prints the whole file (fail open).
strip_frontmatter() {
  awk '
    NR==1 { sub(/^\xef\xbb\xbf/, "") }
    { lines[NR] = $0 }
    END {
      n = NR
      showfrom = 1
      if (n >= 1 && lines[1] ~ /^---[[:space:]]*\r?$/) {
        for (i = 2; i <= n; i++) {
          if (lines[i] ~ /^---[[:space:]]*\r?$/) { showfrom = i + 1; break }
        }
      }
      for (i = showfrom; i <= n; i++) print lines[i]
    }
  ' "$1" 2>/dev/null
}

# current_chapter - print the highest-numbered manuscript chapter path ("" if none).
# Chapters order by frontmatter number, but for the "latest" pointer the file
# number is a safe proxy (ledger check flags filename/number mismatches).
current_chapter() {
  local root best="" bestnum=-1 n f
  root=$(project_root)
  for f in "$root"/manuscript/chapters/chapter-*.md; do
    [ -e "$f" ] || continue
    n=$(basename "$f" | sed -n 's/^chapter-0*\([0-9][0-9]*\)\.md$/\1/p')
    [ -n "$n" ] || continue
    n=$((10#$n))
    if [ "$n" -gt "$bestnum" ]; then bestnum="$n"; best="$f"; fi
  done
  printf '%s\n' "$best"
}

# json_escape <text> - escape a string for embedding in a JSON document.
# Strips CR (CRLF files), escapes backslash/quote/tab (the tab is replaced via
# a literal tab in the pattern — some sed builds ignore \x09), removes any
# remaining raw control bytes (a raw control char inside a JSON string is
# invalid), joins lines with \n.
json_escape() {
  printf '%s' "$1" | tr -d '\r' \
    | sed -e 's/\\/\\\\/g' -e 's/"/\\"/g' -e 's/\t/\\t/g' \
    | tr -d '\000-\010\013\014\016-\037' \
    | awk '{ printf "%s\\n", $0 }' | sed 's/\\n$//'
}

# is_subagent_context - tri-state session-context detection.
# The hook payload's transcript_path points at the session transcript; in a
# subagent transcript the JSONL records carry "isSidechain":true. Returns:
#   0 - spawned subagent confirmed
#   1 - main session confirmed ("isSidechain":false seen)
#   3 - UNKNOWN (no transcript path, unreadable file, or no marker in the
#       transcript head) — callers decide fail-open vs fail-closed per path
#       (gate_input_block_reason fails closed for the protected gate inputs).
is_subagent_context() {
  local tp="$1" line
  [ -n "$tp" ] && [ -f "$tp" ] || return 3
  # Only the head of the transcript matters: a sidechain transcript opens
  # with isSidechain:true records; the main transcript opens with false.
  line=$(head -c 4096 "$tp" 2>/dev/null | grep -om1 '"isSidechain":[[:space:]]*[a-z]*' || true)
  case "$line" in
    '"isSidechain":true'|'"isSidechain": true')  return 0 ;;
    '"isSidechain":false'|'"isSidechain": false') return 1 ;;
  esac
  return 3
}

# gate_input_block_reason <abs-path> [<write-text>] - prints ONE block
# sentence when a subagent tries to write a gate input; prints nothing
# otherwise (and never blocks main-session writes - the muse persists the
# verdicts).
#
# Scope (gate-input protection without strangling the pipeline):
#   - work/critique-reports/ and work/cold-reads/: every subagent write is
#     blocked - verdict transcription and cold-read persistence belong to the
#     muse (the readers have no Write anyway).
#   - work/outline/: blocked only when the write would set the gate flags
#     (`approved: true` / `pivotal: true`) - the author records outline
#     acceptance through the muse, never through a spawned agent. The
#     outliner legitimately creates and edits outlines whose flags are
#     false; chapter-loop step 1 must not be blocked by its own protection.
#     <write-text> is the Write/Edit payload or the Bash command; YAML
#     colons and spaces survive JSON encoding byte-for-byte, so the text can
#     be scanned directly. Fail-open: no text or no match never blocks.
gate_input_block_reason() {
  local abs="$1" text="${2:-}" ctx why
  is_subagent_context "${HOOK_TRANSCRIPT_PATH:-}"; ctx=$?
  if [ "$ctx" -eq 1 ]; then
    return 0  # main session confirmed: the muse may persist the artifacts
  fi
  if [ "$ctx" -eq 3 ]; then
    # Ambiguous context (unreadable/missing transcript): fail CLOSED for the
    # protected gate inputs — these artifacts are the three hard gates'
    # inputs, and a sniffing failure must not silently remove the only
    # mechanical barrier. The writer is told to report back instead.
    case "$abs" in
      */work/critique-reports/*|*/work/cold-reads/*)
        printf '%s\n' "Blocked (gate-input protection): the session context could not be verified for this write to work/critique-reports/ or work/cold-reads/ - verdict transcription and cold-read persistence belong to the muse. Report your result back and let the muse persist it."
        return 0
        ;;
      */work/outline/*)
        if _text_sets_gate_flags "$text"; then
          printf '%s\n' "Blocked (gate-input protection): the session context could not be verified and this write would set approved: true or pivotal: true in work/outline/ - the author records outline acceptance through the muse. Report back and let the muse persist it with the flags false."
          return 0
        fi
        ;;
    esac
    return 0
  fi
  case "$abs" in
    */work/critique-reports/*|*/work/cold-reads/*)
      printf '%s\n' "Blocked (gate-input protection): spawned agents never write work/critique-reports/ or work/cold-reads/ - verdict transcription and cold-read persistence belong to the muse. Report your result back and let the muse persist it."
      ;;
    */work/outline/*)
      if _text_sets_gate_flags "$text"; then
        printf '%s\n' "Blocked (gate-input protection): spawned agents never set approved: true or pivotal: true in work/outline/ - the author records outline acceptance through the muse. Report your outline and let the muse persist it with the flags false."
      fi
      ;;
  esac
  return 0
}

# _text_sets_gate_flags <text> - true when the write text would set a gate
# flag (`approved: true` / `pivotal: true`).
_text_sets_gate_flags() {
  local text="$1"
  [ -n "$text" ] || return 1
  printf '%s' "$text" | grep -qE 'approved:[[:space:]]*true|pivotal:[[:space:]]*true' 2>/dev/null
}

# prose_gate_block_reason <abs-chapter-path> - the shared gate-1 predicate.
# Prints ONE block sentence (stdout) when a prose write to
# manuscript/chapters/chapter-NN.md must be blocked; prints nothing when the
# write may proceed. Always returns 0; the caller decides via output.
#
# Checks (spec 6.2):
#   (1) work/outline/chapter-NN.md exists and frontmatter has approved: true
#   (2) vellum state check exits 0 (only when an interpreter resolves;
#       otherwise one advisory line on stderr and continue - the bash
#       predicate above still gates. Fail-open doctrine: better to miss
#       than mis-block.)
#   (3) rewriting an existing draft chapter re-checks only (2)
prose_gate_block_reason() {
  local abs="$1" root base num chdir exists="" status="" outline="" f fnum
  root=$(project_root)
  base=$(basename "$abs")
  case "$base" in
    chapter-*.md) ;;
    *) return 0 ;;
  esac
  num=$(printf '%s' "$base" | sed -n 's/^chapter-0*\([0-9][0-9]*\)\.md$/\1/p')
  [ -n "$num" ] || return 0
  chdir=$(dirname "$abs")
  case "$chdir" in
    */manuscript/chapters) ;;
    *) return 0 ;;
  esac

  exists=""
  [ -f "$abs" ] && exists=1
  status=""
  [ -n "$exists" ] && status=$(fm_field "$abs" status)

  # (3) rewriting an existing draft chapter: re-check state only.
  local skip_outline=""
  if [ -n "$exists" ] && [ "$status" = "draft" ]; then
    skip_outline=1
  fi

  if [ -z "$skip_outline" ]; then
    if [ -d "$root/work/outline" ]; then
      # Tolerate zero-pad differences: match by integer chapter number.
      for f in "$root/work/outline"/chapter-*.md; do
        [ -e "$f" ] || continue
        fnum=$(basename "$f" | sed -n 's/^chapter-0*\([0-9][0-9]*\)\.md$/\1/p')
        if [ "$fnum" = "$num" ]; then outline="$f"; break; fi
      done
    fi
    if [ -z "$outline" ]; then
      printf '%s\n' "Blocked by gate 1 (outline before prose): chapter $num has no outline at work/outline/chapter-$(printf '%02d' "$num" 2>/dev/null || printf '%s' "$num").md - draft one via /vellum:write-chapter (muse spawns @outliner) and get the author's approval before writing prose."
      return 0
    fi
    local approved
    approved=$(fm_field "$outline" approved)
    if [ "$approved" != "true" ]; then
      printf '%s\n' "Blocked by gate 1 (outline before prose): work/outline/$(basename "$outline") is not marked approved: true - record the author's outline approval before writing chapter $num prose."
      return 0
    fi
  fi

  # (2) transactional state check - an additional precondition, skipped with a
  # one-line advisory when no interpreter resolves (gate never dies without
  # Python). The write target is passed so the engine can scope its
  # transactional invariants to new-chapter starts: an edit to an existing
  # chapter file is that chapter's own transaction (revision, or the
  # accepted->final close-out), never a start.
  local py rc reason first
  if py=$(vellum_py); then
    reason=$(cd "$root" && vellum_run "$py" "$VELLUM_ENGINE" state check "$abs" 2>&1)
    rc=$?
    if [ "$rc" -eq 2 ]; then
      # Exit 2 per the engine contract: an actual state-check failure. Block,
      # embedding the engine's one-line reason.
      first=$(printf '%s' "$reason" | awk 'NF{print; exit}')
      printf '%s\n' "Blocked by gate 1 (chapter transaction): ${first:-state check failed} - complete the chapter close-out with your Python interpreter (python3 / python / py -3 scripts/vellum state rebuild), or run /vellum:write-chapter, and retry."
      return 0
    elif [ "$rc" -ne 0 ]; then
      # Anything else (missing engine, crash, exit 1): fail open on uncertainty.
      printf '%s\n' "vellum: state check could not run (engine unavailable or error); this write passed the outline gate only." >&2
    fi
  else
    printf '%s\n' "vellum: no Python interpreter found - state check skipped for this write; the outline gate is still enforced." >&2
  fi
  return 0
}

# ---------------------------------------------------------------------------
# Shared hard-signal patterns + truncation predicate.
# Single source of truth for session-stop.sh (opt-in stop gate) and
# check-prose-after-write.sh (post-write net): both previously carried
# near-identical copies, and a pattern fix applied to only one silently
# desynchronized the Stop gate from the post-write net. Keep only the
# emit/exit behavior local to each hook.
# ---------------------------------------------------------------------------

# Terminal punctuation: ASCII class + multibyte UTF-8 tails (em-dash, ellipsis,
# curly quotes) checked on the final 3 bytes — under LC_ALL=C the multibyte
# characters degenerate to per-byte matching inside a bracket class.
TERM_PUNCT='[.!?")-]$'

# Truncation: the last line must end in terminal punctuation. The ASCII class
# lives in a variable: Git Bash grep mis-parses a backslash-escaped ] inside a
# bracket class when the pattern is inline, and a raw double quote in a
# case-pattern word opens a quoted context - both silently break the check.
# Multibyte punctuation (em-dash, ellipsis, curly quotes) is checked
# separately on the final 3 UTF-8 bytes: under LC_ALL=C the multibyte
# characters degenerate to per-byte matching inside a bracket class, and an
# em-dash — a legitimate fiction ending for interrupted dialogue — would
# never match the ASCII class at all.
# A closing scene-break marker (* * *, ---, - - -, ...) is a terminal ending:
# a chapter legitimately ends on a scene break or separator, and flagging it
# as "truncation" forces a rewrite loop on a stylistic choice.
ends_with_terminal_punct() {
  local s="$1" tail3
  case "$s" in
    *[![:space:]]*) ;;
    *) return 1 ;;
  esac
  if printf '%s\n' "$s" | grep -qE '^([*_=-])[[:space:]]*(\1[[:space:]]*){2,}$'; then
    return 0  # scene-break / hr marker as the closing line
  fi
  if printf '%s' "$s" | grep -qE "$TERM_PUNCT"; then
    return 0
  fi
  tail3="$(printf '%s' "$s" | tail -c 3)"
  case "$tail3" in
    $'\xe2\x80\x9d'|$'\xe2\x80\x99'|$'\xe2\x80\x92'|$'\xe2\x80\xa6'|$'\xe2\x80\x94') return 0 ;;
  esac
  return 1
}

# Model-refusal / AI self-reference patterns. Apostrophes are matched with .?
# (any single char, optional) so the source contains no curly or straight
# quote bytes - those break bash parsing when they appear inside character
# classes across the double-quoted pattern string. can.t covers cant.
REFUSAL_PATTERN="as an?\\s+(AI|artificial intelligence)|AI\\s+(language\\s+)?model|cannot\\s+(fulfill|assist|provide)|unable to (fulfill|assist)|I (cannot|can.t) (provide|generate|create)|my (training|knowledge)"
APOLOGY_PATTERN="I .?m .?(sorry|unable)|I (apologize|apologise)|I (cannot|can.t) continue|unable to continue"
AI_CONTEXT_PATTERN="as an?\\s+(AI|artificial intelligence)|AI\\s+(language\\s+)?model|language model|my (training|knowledge)"

# refusal_hits <body-text> - prints matching lines (grep -n style) for refusal
# markers; apology-shaped lines ('I'm sorry', 'I apologize', 'I cannot
# continue') are ordinary character dialogue in fiction, so they are flagged
# only when an AI-context phrase co-occurs in the body ('as an AI', 'language
# model', 'my training') - otherwise the net fires on most chapters with an
# apology and desensitizes the author.
refusal_hits() {
  local body="$1" hits apology
  hits="$(printf '%s' "$body" | grep -nEi -e "$REFUSAL_PATTERN" 2>/dev/null || true)"
  apology="$(printf '%s' "$body" | grep -nEi -e "$APOLOGY_PATTERN" 2>/dev/null || true)"
  if [ -n "$apology" ] && [ -n "$(printf '%s' "$body" | grep -nEi -e "$AI_CONTEXT_PATTERN" 2>/dev/null || true)" ]; then
    hits+="${NL:-$'\n'}${apology}"
  fi
  printf '%s\n' "$hits"
}
