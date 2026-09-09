#!/bin/bash
# guard-bash-prose-writes.sh - PreToolUse(Bash) blocking gate 1, alternate path.
# Adapted from oh-story-claudecode/skills/story-setup/references/templates/hooks (MIT) -
# Bash-guard concept (their prose-command-guard): scan the Bash command for
# redirection/heredoc/tee/cp/mv writing into manuscript/chapters/ and run the same
# outline predicate; an outline-copy detector blocks >90% similar copies.
# Changes: rewritten for the vellum layout; pure-bash command scanning (no Node core);
# fail-open on uncertainty; interpreter-embedded writes (sed -i, perl -i,
# python -c open(...), touch, dd) gated via path-like token extraction when a
# write indicator is present — read-only commands are never gated.
#
# BLOCKING - gate 1, alternate path. Uncertain cases exit 0.
set -u

HOOK_DIR="$(cd "$(dirname "$0")" && pwd)"
source "$HOOK_DIR/lib/common.sh"

read_hook_input

COMMAND=""
COMMAND="$(extract_payload_field command 2>/dev/null || true)"
[ -z "$COMMAND" ] && exit 0

# Detect a write into manuscript/chapters/ via redirection, heredoc, tee, cp, mv.
# We extract candidate target tokens and normalize each; any that resolve to a prose
# chapter file is gated. Fail open when no candidate resolves.
candidates_from_command() {
  local cmd="$1" tok qtok rest targets="" frag
  # Strip a leading `bash -c '...'` style wrapper so inner redirections surface.
  rest="$cmd"

  # Redirection targets: > file, >> file, 2> file, &> file, >"file", >'file'.
  # Scan the WHOLE command: after extracting a target, remove only that
  # matched fragment and keep scanning the remaining tail, so later
  # redirections in a compound command are gated too.
  while true; do
    frag="$(printf '%s' "$rest" | grep -oE '[&12]*>>?[[:space:]]*(\"[^\"]*\"|'"'"'[^'"'"']*'"'"'|[^[:space:];|&<>()]+)' | head -n1 || true)"
    [ -n "$frag" ] || break
    tok="${frag#>>}"; tok="${frag#>}"; tok="${tok#>}"; tok="${tok#2>}"; tok="${tok#&>}"
    tok="${tok#>}"; tok="${tok#>}"; tok="${tok#>}"; tok="${tok#>}"; tok="${tok#>}"
    tok="$(printf '%s' "$tok" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')"
    tok="${tok#\"}"; tok="${tok%\"}"; tok="${tok#\'}"; tok="${tok%\'}"
    [ -n "$tok" ] && targets="$targets
$tok"
    # Remove exactly this occurrence (literal match, first occurrence) and
    # continue scanning; truncating from the fragment onward would silently
    # skip every later redirect in a compound command.
    rest="${rest/"$frag"/}"
  done

  # tee targets: tee [-a] file [file ...]
  local teetargets
  teetargets="$(printf '%s' "$cmd" | grep -oE '\btee[[:space:]]+(-a[[:space:]]+)?[^;|&;()]+' || true)"
  if [ -n "$teetargets" ]; then
    for tok in $teetargets; do
      case "$tok" in tee|-a) ;; *) targets="$targets
$tok" ;; esac
    done
  fi

  # cp/mv last operand is the target: cp [-flags] src... dst. Every cp/mv
  # fragment contributes its final operand — a compound command with several
  # copies must gate each target, not just the first.
  local copyfrag
  for copyfrag in cp mv; do
    local c frags fraglast
    frags="$(printf '%s' "$cmd" | grep -oE "\b$copyfrag[[:space:]]+(-[A-Za-z-]+[[:space:]]+)*[^;|&;()]+" || true)"
    if [ -n "$frags" ]; then
      while IFS= read -r c; do
        [ -n "$c" ] || continue
        local toks="" last="" t2
        for t2 in $c; do
          case "$t2" in "$copyfrag") ;; -*) ;; *) last="$t2" ;; esac
        done
        [ -n "$last" ] && targets="$targets
$last"
      done <<FRAGS
$frags
FRAGS
    fi
  done

  # Interpreter-embedded writes (sed -i, perl -i, python/py -3 -c open(...),
  # node -e, touch, dd): no redirect/tee/cp/mv shape surfaces them, but they
  # write files. When the command carries one of those write indicators,
  # extract every path-like token naming the manuscript or a work/ directory
  # and let the predicates decide. Plain reads (rg/cat/grep) carry no
  # indicator and are never gated. Residual gap (fail-open doctrine):
  # targets built from variables or obfuscated paths are not extractable.
  if printf '%s' "$cmd" | grep -qE '(^|[;&|[[:space:]])sed[[:space:]].*-i([^A-Za-z-]|$)|perl[[:space:]].*-i([^A-Za-z-]|$)|python3?[[:space:]]+(-3[[:space:]]+)?-c|py[[:space:]]+-3[[:space:]]+-c|node[[:space:]]+-e|(^|[;&|[[:space:]])touch[[:space:]]|dd[[:space:]]'; then
    local pathlike tok2
    pathlike="$(printf '%s' "$cmd" | tr '\\' '/' | grep -oE '(manuscript|work)/[A-Za-z0-9_./-]+' || true)"
    if [ -n "$pathlike" ]; then
      while IFS= read -r tok2; do
        [ -n "$tok2" ] || continue
        targets="$targets
$tok2"
      done <<PATHTOKS
$pathlike
PATHTOKS
    fi
  fi

  printf '%s\n' "$targets"
}

# Outline-copy detector: a NEW chapter file whose source is >90% line-identical
# to an existing chapter. The detector is mechanism-agnostic (spec: "prior
# chapter of near-identical byte size"), so the source can be:
#   - the cp/mv src operand,
#   - any EXISTING chapter named in the command (`cat prior.md > new.md` —
#     the redirect target passes gate 1 if the new chapter has an approved
#     outline, so the copy must be caught here), or
#   - the heredoc body itself duplicating a prior chapter's prose.
similarity_block() {
  local target="$1" cmd="$2" root base num
  root=$(project_root)
  base=$(basename "$target")
  case "$base" in chapter-*.md) ;; *) return 1 ;; esac
  [ -f "$target" ] && return 1  # existing file: not a copy-in, gate 1 predicate handles it

  # Find the cp/mv fragment whose DESTINATION (last operand) is this target;
  # the copy source is that fragment's penultimate operand. Every fragment is
  # considered so a compound command's later copies are detected too.
  local src="" c frags frag dstlast toks t2 prev
  for c in cp mv; do
    frags="$(printf '%s' "$cmd" | grep -oE "\b$c[[:space:]]+(-[A-Za-z-]+[[:space:]]+)*[^;|&;()]+" || true)"
    [ -n "$frags" ] || continue
    while IFS= read -r frag; do
      [ -n "$frag" ] || continue
      dstlast=""
      prev=""
      toks=""
      for t2 in $frag; do
        case "$t2" in "$c") ;; -*) ;; *) prev="$toks"; toks="$t2"; dstlast="$t2" ;; esac
      done
      # Compare on normalized tokens: the command may use forward slashes
      # while $target is absolute with backslashes (or vice versa).
      dstbase="$(basename "$dstlast" 2>/dev/null || printf '%s' "$dstlast")"
      dstnorm="$(printf "%s" "$dstlast" | tr "\\" "/" 2>/dev/null || printf "%s" "$dstlast")"
      target_norm="$(printf "%s" "$target" | tr "\\" "/")"
      if [ "$dstbase" = "$(basename "$target")" ] || [ "$dstnorm" = "$target_norm" ]; then
        src="$prev"
        break
      fi
    done <<FRAGS
$frags
FRAGS
    [ -n "$src" ] && break
  done

  # No cp/mv source: an existing chapter named in the command is the source
  # (`cat manuscript/chapters/chapter-07.md > new.md`), else the heredoc body
  # itself is the content being written.
  local heredoc_tmp=""
  if [ -z "$src" ]; then
    local tok toknorm
    while IFS= read -r tok; do
      [ -n "$tok" ] || continue
      toknorm="$(printf '%s' "$tok" | tr '\\' '/')"
      case "$toknorm" in
        /*) ;; [A-Za-z]:[/]*) ;; *) toknorm="$root/$toknorm" ;;
      esac
      [ -f "$toknorm" ] || continue
      [ "$toknorm" = "$target" ] && continue
      case "$toknorm" in
        */manuscript/chapters/*)
          src="$toknorm"
          break
          ;;
      esac
    done <<TOKS
$(printf '%s' "$cmd" | grep -oE '(manuscript/chapters/chapter-[0-9]+\.md)' || true)
TOKS
  fi
  if [ -z "$src" ]; then
    # Heredoc body: extract the first heredoc's body into a temp file and use
    # it as the similarity source. Fail-open when there is no heredoc or the
    # body is empty.
    local body
    body="$(_extract_heredoc_body "$cmd" 2>/dev/null || true)"
    if [ -n "$body" ]; then
      heredoc_tmp="$(mktemp "${TMPDIR:-/tmp}/vellum-heredoc-XXXXXX" 2>/dev/null || true)"
      if [ -n "$heredoc_tmp" ]; then
        printf '%s\n' "$body" > "$heredoc_tmp" 2>/dev/null || true
        src="$heredoc_tmp"
      fi
    fi
  fi
  [ -n "$src" ] || return 1

  # Unify separators before the absolute-path tests (Windows commands may
  # carry backslash paths even under Git Bash).
  src="$(printf "%s" "$src" | tr "\\" "/")"
  case "$src" in
    /*) ;; [A-Za-z]:[/]*) ;; *) src="$root/$src" ;;
  esac
  if [ ! -f "$src" ]; then
    [ -n "$heredoc_tmp" ] && rm -f "$heredoc_tmp" 2>/dev/null || true
    return 1
  fi

  # If the copy source is itself an existing chapter (chapter-NN.md inside the
  # chapters dir), the new chapter is by construction 100% line-identical to a
  # prior chapter - block. Non-chapter scratch files (chapter-14-src.md etc.)
  # in the same directory are not chapters and fall through to the peer scan.
  # (The heredoc temp file is not a chapter and never takes this branch.)
  src_base=$(basename "$src")
  src_num=$(printf '%s' "$src_base" | sed -n 's/^chapter-0*\([0-9][0-9]*\)\.md$/\1/p')
  case "$src" in
    */manuscript/chapters/*)
      if [ -n "$src_num" ]; then
        printf '%s\n' "Blocked by gate 1 (outline-copy detector): new chapter $(basename "$target") copies existing chapter $src_base - write original prose via /vellum:write-chapter instead of copying."
        return 0
      fi
      ;;
  esac

  # Compare against existing chapters of near-identical byte size. A heredoc
  # source carries prose only (no frontmatter), so the chapter's frontmatter
  # is stripped before the size/line comparison in that case — body vs body.
  local src_size
  src_size=$(wc -c < "$src" 2>/dev/null | tr -d ' ')
  local d blocked=1
  for d in "$root"/manuscript/chapters/chapter-*.md; do
    [ -e "$d" ] || continue
    [ "$d" = "$target" ] && continue
    # Skip the cp/mv source itself (when it lives in the same directory) - a file
    # is trivially 100% similar to itself and that is not a copy violation.
    [ "$d" = "$src" ] && continue
    local ds d_lines
    if [ -n "$heredoc_tmp" ]; then
      ds=$(strip_frontmatter "$d" 2>/dev/null | wc -c | tr -d ' ')
      d_lines=$(strip_frontmatter "$d" 2>/dev/null | wc -l | tr -d ' ')
    else
      ds=$(wc -c < "$d" 2>/dev/null | tr -d ' ')
      d_lines=$(wc -l < "$d" 2>/dev/null | tr -d ' ')
    fi
    # Near-identical byte size (within 10%) is the cheap pre-filter.
    if [ "$src_size" -gt 0 ] 2>/dev/null; then
      local lo hi
      lo=$((src_size * 90 / 100)); hi=$((src_size * 110 / 100))
      [ "$ds" -ge "$lo" ] && [ "$ds" -le "$hi" ] || continue
    fi
    # Line-level similarity via comm on sorted lines. (The process
    # substitutions must live directly in this shell context — routing them
    # through a command substitution closes the /dev/fd before comm reads.)
    local total common src_lines
    src_lines=$(wc -l < "$src" 2>/dev/null | tr -d ' ')
    total=$((src_lines + d_lines))
    if [ -n "$heredoc_tmp" ]; then
      common=$(comm -12 <(LC_ALL=C sort "$src") \
        <(strip_frontmatter "$d" | LC_ALL=C sort) 2>/dev/null | wc -l | tr -d ' ')
    else
      common=$(comm -12 <(LC_ALL=C sort "$src") \
        <(LC_ALL=C sort "$d") 2>/dev/null | wc -l | tr -d ' ')
    fi
    case "$total" in ''|*[!0-9]*) total=0 ;; esac
    case "$common" in ''|*[!0-9]*) common=0 ;; esac
    if [ "$total" -gt 0 ]; then
      local pct=$((common * 200 / total))  # shared lines as % of the union-ish total
      if [ "$pct" -ge 90 ]; then
        printf '%s\n' "Blocked by gate 1 (outline-copy detector): new chapter $(basename "$target") is >90% identical to existing $(basename "$d") - write original prose via /vellum:write-chapter instead of copying."
        blocked=0
        break
      fi
    fi
  done
  [ -n "$heredoc_tmp" ] && rm -f "$heredoc_tmp" 2>/dev/null || true
  return $blocked
}

# _extract_heredoc_body <command> - print the body of the first heredoc in
# the command text (lines between the <<[-]DELIM line and the terminator
# line DELIM). Quoted and unquoted delimiters are handled the same way: the
# body bytes are what they are, and only exact-line similarity matters here.
# Hook payloads carry JSON string escapes: extract_payload_field leaves \n as
# a literal two-character sequence, so literal \r\n / \n are first converted
# to real newlines (harmless for the similarity heuristic; fail-open anyway).
_extract_heredoc_body() {
  local cmd="$1" delim
  cmd="$(printf '%s' "$cmd" | sed 's/\\r\\n/\n/g; s/\\n/\n/g')"
  delim="$(printf '%s\n' "$cmd" | sed -nE 's/.*<<-?[[:space:]]*["'"'"']?([A-Za-z_][A-Za-z0-9_]*)["'"'"']?.*/\1/p' | head -n1)"
  [ -n "$delim" ] || return 1
  printf '%s\n' "$cmd" | awk -v d="$delim" '
    body != 1 { if ($0 ~ /<<-?[[:space:]]*["'"'"']?/ && $0 ~ d) { body = 1 } ; next }
    body == 1 && $0 == d { exit }
    body == 1 { print }
  '
}

# Main: collect candidate targets, gate each.
FOUND=0
while IFS= read -r cand; do
  [ -n "$cand" ] || continue
  ABS="$(normalize_target "$cand" 2>/dev/null || true)"
  [ -z "$ABS" ] && continue
  # Gate-input protection for shell-written files too (subagent writes only).
  # The command text is passed so an outline write that leaves the gate flags
  # false passes; a command that would set approved:/pivotal: true is blocked
  # by gate_input_block_reason itself.
  GIREASON="$(gate_input_block_reason "$ABS" "$COMMAND" 2>/dev/null || true)"
  SUBAGENT_CTX=0
  is_subagent_context "${HOOK_TRANSCRIPT_PATH:-}" || SUBAGENT_CTX=$?
  if [ -z "$GIREASON" ] && [ "$SUBAGENT_CTX" -eq 0 ]; then
    case "$ABS" in
      */work/outline/*)
        # A copy/move between outlines launders an approval: the source's
        # approved: true lands in the target. Two work/outline/ references
        # in one command mean a copy/move between outlines (subagent
        # writes only — the muse may move outlines).
        n_out="$(printf '%s' "$COMMAND" | grep -o 'work/outline/' | wc -l | tr -d ' ')"
        case "$n_out" in ''|*[!0-9]*) n_out=0 ;; esac
        if [ "$n_out" -gt 1 ]; then
          GIREASON="Blocked (gate-input protection): spawned agents never copy or move files inside work/outline/ - one outline's approval flags must never be reproduced into another. Report your outline and let the muse persist it."
        fi
        ;;
    esac
  fi
  if [ -n "$GIREASON" ]; then
    printf '%s\n' "$GIREASON" >&2
    exit 2
  fi
  case "$ABS" in
    */manuscript/chapters/chapter-*.md) ;;
    *) continue ;;
  esac
  FOUND=1
  REASON="$(prose_gate_block_reason "$ABS" 2>/dev/null || true)"
  if [ -n "$REASON" ]; then
    printf '%s\n' "$REASON" >&2
    exit 2
  fi
  if SIM="$(similarity_block "$ABS" "$COMMAND" 2>/dev/null)"; then
    printf '%s\n' "$SIM" >&2
    exit 2
  fi
done <<CANDIDATES
$(candidates_from_command "$COMMAND")
CANDIDATES

[ "$FOUND" -eq 0 ] && exit 0
exit 0
