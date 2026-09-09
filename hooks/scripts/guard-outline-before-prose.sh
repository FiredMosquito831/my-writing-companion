#!/bin/bash
# guard-outline-before-prose.sh - PreToolUse(Write|Edit|MultiEdit) blocking gate 1.
# Adapted from oh-story-claudecode/skills/story-setup/references/templates/hooks/guard-outline-before-prose.sh - MIT.
# Changes: rewritten for the vellum layout (manuscript/chapters/chapter-NN.md + work/outline
# approved-outline frontmatter + vellum state check); Node core replaced by prose_core.py
# (Python) with a pure-bash fallback; fail-open doctrine kept.
#
# BLOCKING: prose writes to manuscript/chapters/ require an author-approved outline
# (approved: true) and a clean vellum state check. Parse failure or target ambiguity
# exits 0 (fail open - better to miss than mis-block). On block: exit 2, stderr is
# exactly one sentence naming the missing precondition and the exact command to fix it.
set -u

HOOK_DIR="$(cd "$(dirname "$0")" && pwd)"
source "$HOOK_DIR/lib/common.sh"

read_hook_input

# Extract the target file path. Prefer prose_core.py (Python, UTF-8 safe); fall back to
# pure-bash JSON extraction when Python is absent or extraction fails.
TARGET=""
if VPY=$(vellum_py) && [ -f "$VELLUM_PROSE_CORE" ]; then
  TARGET="$(printf '%s' "$HOOK_INPUT" | vellum_run "$VPY" "$VELLUM_PROSE_CORE" extract-target 2>/dev/null || true)"
fi
[ -z "$TARGET" ] && TARGET="$(extract_payload_field file_path 2>/dev/null || true)"
[ -z "$TARGET" ] && TARGET="$(extract_payload_field path 2>/dev/null || true)"

ABS="$(normalize_target "${TARGET:-}" 2>/dev/null || true)"
if [ -z "$ABS" ]; then
  # No resolvable target - fail open.
  exit 0
fi

# Gate-input protection: spawned agents never write work/critique-reports/ or
# work/cold-reads/, and never set the outline gate flags (approved: true /
# pivotal: true) in work/outline/ — those belong to the muse. The payload is
# passed so outline drafting that leaves the flags false passes (the
# outliner's chapter-loop step 1).
GIREASON="$(gate_input_block_reason "$ABS" "$HOOK_INPUT" 2>/dev/null || true)"
if [ -n "$GIREASON" ]; then
  printf '%s\n' "$GIREASON" >&2
  exit 2
fi

# Only gate prose files under manuscript/chapters/.
case "$ABS" in
  */manuscript/chapters/chapter-*.md) ;;
  *) exit 0 ;;
esac

# Run the shared gate-1 predicate. It prints one block sentence to stdout when
# the write must be blocked, nothing otherwise; advisory lines (state check
# skipped / engine unavailable) go to stderr and must SURVIVE (the author sees
# why the transactional precondition did not run) — so only the predicate's
# stdout is captured, its stderr passes through.
ADVISORY="$(mktemp "${TMPDIR:-/tmp}/vellum-adv.XXXXXX")" || ADVISORY=""
if [ -n "$ADVISORY" ]; then
  REASON="$(prose_gate_block_reason "$ABS" 2>"$ADVISORY" || true)"
  [ -s "$ADVISORY" ] && cat "$ADVISORY" >&2
  rm -f "$ADVISORY" 2>/dev/null || true
else
  REASON="$(prose_gate_block_reason "$ABS" || true)"
fi
if [ -n "$REASON" ]; then
  printf '%s\n' "$REASON" >&2
  exit 2
fi
exit 0
