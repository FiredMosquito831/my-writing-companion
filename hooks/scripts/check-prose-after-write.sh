#!/bin/bash
# check-prose-after-write.sh - PostToolUse(Write|Edit|MultiEdit) advisory prose net.
# Adapted from oh-story-claudecode/skills/story-setup/references/templates/hooks/check-prose-after-write.sh - MIT.
# Changes: rewritten for the vellum layout; Node prose-net core replaced by prose_core.py
# (Python) with a pure-bash fallback; writes work/voice-debt.json; honors <!-- voice:skip -->.
#
# Advisory only - exit 0 always; silent when clean. Emits a PostToolUse additionalContext
# JSON block with one line per finding. Hard signals (truncation, model refusal,
# placeholders, engineering words, [VERIFY] remnants) are scanned in bash; the style
# tier net runs via prose_core.py scan, falling back to an embedded tier-1 grep pattern
# when Python is absent. The Romanian tense/person morphology scan (ADD-6;
# `vellum style stats <file> --morphology`) also runs as part of this advisory
# post-write pass when the engine is available: report-only suggestion-severity
# findings (JSON lines, grep-filtered below), no exit-code change, silent when
# the chapter is clean. A chapter-level <!-- voice:skip --> suppresses tier-1
# debt accrual and the morphology scan for deliberate tense play (the net's
# tier-1 findings and hard signals still surface); a per-line <!-- tense:skip -->
# valve is honored inside the scanner (style-guardrails/resources/structural-caps.md). The
# scan is skipped without a Python interpreter, like every engine path here.
set -u

HOOK_DIR="$(cd "$(dirname "$0")" && pwd)"
source "$HOOK_DIR/lib/common.sh"

read_hook_input

TARGET=""
if VPY=$(vellum_py) && [ -f "$VELLUM_PROSE_CORE" ]; then
  TARGET="$(printf '%s' "$HOOK_INPUT" | vellum_run "$VPY" "$VELLUM_PROSE_CORE" extract-target 2>/dev/null || true)"
fi
[ -z "$TARGET" ] && TARGET="$(extract_payload_field file_path 2>/dev/null || true)"
[ -z "$TARGET" ] && TARGET="$(extract_payload_field path 2>/dev/null || true)"

ABS="$(normalize_target "${TARGET:-}" 2>/dev/null || true)"
[ -z "$ABS" ] && exit 0
case "$ABS" in
  */manuscript/chapters/chapter-*.md) ;;
  *) exit 0 ;;
esac
[ -f "$ABS" ] || exit 0

ROOT=$(project_root)
REL="${ABS#$ROOT/}"
NL=$'\n'
OUT=""

# --- Hard signal: near-empty file (truncation / failed write) ---
BYTES=$(wc -c < "$ABS" 2>/dev/null | tr -d ' ')
case "$BYTES" in ''|*[!0-9]*) BYTES=0 ;; esac
if [ "$BYTES" -lt 200 ]; then
  OUT+="truncation: chapter is only ${BYTES} bytes (likely truncated or failed to save) - review and resave.${NL}"
fi

# --- Hard signal: last line not ending in terminal punctuation (truncation) ---
# TERM_PUNCT / ends_with_terminal_punct / refusal patterns are shared with
# session-stop.sh (lib/common.sh) so the Stop gate and this net cannot drift.
BODY="$(strip_frontmatter "$ABS" 2>/dev/null || true)"
LAST_LINE="$(printf '%s\n' "$BODY" | sed '/^[[:space:]]*$/d' | tail -n1)"
if [ -n "$LAST_LINE" ] && ! ends_with_terminal_punct "$LAST_LINE"; then
  OUT+="truncation: last line does not end in terminal punctuation - '${LAST_LINE:0:40}'${NL}"
fi

# --- Hard signal: model-refusal phrases ---
REFUSAL="$(refusal_hits "$BODY" 2>/dev/null || true)"
if [ -n "$REFUSAL" ]; then
  OUT+="refusal/AI self-reference markers left in prose:${NL}${REFUSAL}${NL}"
fi

# --- Hard signal: placeholder / TODO / INVENTED remnants ---
PLACEHOLDER="$(printf '%s' "$BODY" | grep -nEi -e '\[TODO' -e '\[INVENTED\]' -e '\[INSERT' -e '\[PLACEHOLDER' -e '\[TBD' -e '\[FIXME' -e 'TODO:' -e '<insert ' 2>/dev/null || true)"
if [ -n "$PLACEHOLDER" ]; then
  # Stronger note if the chapter is already accepted.
  CH_STATUS="$(fm_field "$ABS" status 2>/dev/null || true)"
  if [ "$CH_STATUS" = "accepted" ] || [ "$CH_STATUS" = "final" ]; then
    OUT+="placeholder remnants in an ${CH_STATUS} chapter (must clear before acceptance):${NL}${PLACEHOLDER}${NL}"
  else
    OUT+="placeholder remnants:${NL}${PLACEHOLDER}${NL}"
  fi
fi

# --- Hard signal: engineering/outline words leaked into prose ---
ENGINEERING="$(printf '%s' "$BODY" | grep -nEi -e 'word target|word-target|beat quota|scene brief|story value|value charge|chapter hook|outline beat|word budget|open loop|frontmatter|approved-outline|schema-version|tracking.state' 2>/dev/null || true)"
if [ -n "$ENGINEERING" ]; then
  OUT+="engineering/outline words in prose (move to kb/outline, or cut):${NL}${ENGINEERING}${NL}"
fi

# --- Hard signal: [VERIFY] remnants (extract to kb/questions before acceptance) ---
VERIFY="$(printf '%s' "$BODY" | grep -nEi -e '\[VERIFY\]' 2>/dev/null || true)"
if [ -n "$VERIFY" ]; then
  OUT+="[VERIFY] remnants left in prose - extract the open questions into kb/questions before accepting the chapter:${NL}${VERIFY}${NL}"
fi

# --- Style tier net (engine path) ---
VOICE_SKIP=""
case "$BODY" in *'<!-- voice:skip -->'*) VOICE_SKIP=1 ;; esac

if VPY=$(vellum_py) && [ -f "$VELLUM_PROSE_CORE" ]; then
  # prose_core.py prints text findings, one per line; --debt updates voice-debt.json.
  if [ -n "$VOICE_SKIP" ]; then
    SCAN="$(vellum_run "$VPY" "$VELLUM_PROSE_CORE" scan "$ABS" --format text 2>/dev/null || true)"
  else
    SCAN="$(vellum_run "$VPY" "$VELLUM_PROSE_CORE" scan "$ABS" --format text --debt "$ROOT" --project_root "$ROOT" 2>/dev/null || true)"
  fi
  [ -n "$SCAN" ] && OUT+="${SCAN}${NL}"
else
  # Pure-bash fallback: embedded tier-1 grep table (kept in sync with prose_core.py TIER1).
  PATTERN='(delv\w*|tapestr\w*|realm|embark\w*|testament to|beacon|meticul\w*|seamless\w*|game.chang\w*|hit different\w*|nestl\w*|vibrant|thriv\w*|bustl\w*|intricat\w*|ever.evolv\w*|daunting|holistic\w*|actionable|impactful|symphon\w*|palpable|unwaver\w*|ethereal|gossamer|shiver\w* down|couldn.?t help but|the air was thick|a chorus of|painted (across|over|onto)|unprecedented|unparalleled)'
  GREP_HITS="$(printf '%s' "$BODY" | grep -nEi -e "$PATTERN" 2>/dev/null | head -n20 || true)"
  if [ -n "$GREP_HITS" ]; then
    OUT+="tier-1 AI phrasing (bash fallback - install Python for the full net):${NL}${GREP_HITS}${NL}"
  fi
fi

# --- Tense/person morphology scan (advisory, report-only) ---
# Runs as part of the advisory post-write pass (see header comment): only the
# scanner's JSON finding lines are surfaced (the text distribution report is
# for the CLI); silent when the chapter is clean; skipped for a chapter-level
# voice:skip carve-out and without a Python interpreter.
if [ -z "$VOICE_SKIP" ] && VPY=$(vellum_py) && [ -f "$VELLUM_ENGINE" ]; then
  MORPH="$(cd "$ROOT" && vellum_run "$VPY" "$VELLUM_ENGINE" style stats "$ABS" --morphology 2>/dev/null \
    | grep '^{' || true)"
  [ -n "$MORPH" ] && OUT+="${MORPH}${NL}"
fi

# --- Acceptance close-out (mechanical half of the chapter transaction) ---
# When this edit leaves the chapter at `accepted`/`final`, run the
# deterministic chapter transaction: wordcount --write, ledger check, state
# rebuild. This makes the chapter transaction fire on acceptance (the edit
# that sets `status: accepted`/`final`), per write-time-capture.md. The
# mechanical close-out is silent on success; findings are written to stderr
# which surfaces in the author's context. Missing engine or a parse failure
# degrades to a one-line advisory (the gate never dies without the runtime).
CH_STATUS="$(fm_field "$ABS" status 2>/dev/null || true)"
if [ "$CH_STATUS" = "accepted" ] || [ "$CH_STATUS" = "final" ]; then
  VELLUM_CLOSED_OUT=0
  if VPY=$(vellum_py) && vellum_run "$VPY" "$VELLUM_ENGINE" --version >/dev/null 2>&1; then
    WC_RC=0
    WC="$(cd "$ROOT" && vellum_run "$VPY" "$VELLUM_ENGINE" wordcount --write "$ABS" 2>&1)" || WC_RC=$?
    # wordcount exit 1 = band findings (advisory report); only >= 2 is a failure.
    if [ "$WC_RC" -ge 2 ]; then
      printf '%s\n' "chapter-maintenance: 'vellum wordcount --write' failed for ${REL}:" >&2
      printf '%s\n' "$WC" >&2
      VELLUM_CLOSED_OUT=1
    fi
    if [ "$VELLUM_CLOSED_OUT" -eq 0 ]; then
      # ledger check exit 1 = findings (advisory report, printed below); the
      # state rebuild still runs so the state card never goes stale.
      LEDGER_RC=0
      LEDGER="$(cd "$ROOT" && vellum_run "$VPY" "$VELLUM_ENGINE" ledger check 2>&1)" || LEDGER_RC=$?
      if [ "$LEDGER_RC" -ge 2 ]; then
        printf '%s\n' "chapter-maintenance: 'vellum ledger check' failed for ${REL}:" >&2
        printf '%s\n' "$LEDGER" >&2
        VELLUM_CLOSED_OUT=1
      elif [ "$LEDGER_RC" -eq 1 ]; then
        printf '%s\n' "chapter-maintenance: ledger check findings for ${REL}:" >&2
        printf '%s\n' "$LEDGER" >&2
      fi
    fi
    if [ "$VELLUM_CLOSED_OUT" -eq 0 ]; then
      REBUILD="$(cd "$ROOT" && vellum_run "$VPY" "$VELLUM_ENGINE" state rebuild 2>&1)" || {
        printf '%s\n' "chapter-maintenance: 'vellum state rebuild' failed for ${REL}:" >&2
        printf '%s\n' "$REBUILD" >&2
        VELLUM_CLOSED_OUT=1
      }
    fi
    [ "$VELLUM_CLOSED_OUT" -eq 0 ] || true  # advisory already emitted
  else
    printf '%s\n' "vellum: no Python interpreter found - skipped the mechanical chapter close-out for ${REL} (install Python >= 3.8 to run wordcount/ledger/state on acceptance)." >&2
  fi
fi

[ -z "$OUT" ] && exit 0

# Emit PostToolUse additionalContext. Must be valid JSON, so escape the body.
# The header and detail are escaped separately and joined with a JSON \n escape
# (a raw newline inside the printf format would break the JSON string).
ESCAPED="$(json_escape "vellum post-write prose net (${REL}):")"
DETAIL="$(json_escape "$OUT")"
printf '{"hookSpecificOutput":{"hookEventName":"PostToolUse","additionalContext":"%s\\n%s"}}\n' "$ESCAPED" "$DETAIL"
exit 0
