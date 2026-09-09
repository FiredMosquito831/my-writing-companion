#!/bin/bash
# session-stop.sh - Stop: pending-capture reminder + opt-in stop gate.
# Adapted from oh-story-claudecode/skills/story-setup/references/templates/hooks/session-end.sh - MIT.
# Changes: rewritten for the vellum layout (_tracking-state.json pending_capture flag);
# added the opt-in stop_gate (project-config.json) that blocks on truncation/refusal markers.
#
# Default behavior: if state/_tracking-state.json has pending_capture: true, print one
# reminder line naming the close-out command; otherwise silent. If kb/project-config.json
# has stop_gate: true, also run the post-write hard-signal scan on the current chapter and
# block (exit 2) on truncation/refusal markers only. Default config never blocks.
set -u

HOOK_DIR="$(cd "$(dirname "$0")" && pwd)"
source "$HOOK_DIR/lib/common.sh"

read_hook_input

ROOT=$(project_root)

# --- Pending-capture reminder ---
if [ -f "$ROOT/state/_tracking-state.json" ]; then
  PENDING="$(grep -oE '"pending_capture"[[:space:]]*:[[:space:]]*true' "$ROOT/state/_tracking-state.json" 2>/dev/null || true)"
  if [ -n "$PENDING" ]; then
    printf '%s\n' "vellum: a chapter is accepted but its transaction is not closed (pending_capture: true). Complete the close-out: route @kb-lead for capture, offer demolition, set status: final, then run the engine close-out with your Python interpreter (python3 / python / py -3 scripts/vellum state rebuild) - or just /vellum:write-chapter maintenance."
  fi
fi

# --- Opt-in stop gate (project-config stop_gate: true) ---
if [ -f "$ROOT/kb/project-config.json" ]; then
  STOP_GATE="$(grep -oE '"stop_gate"[[:space:]]*:[[:space:]]*true' "$ROOT/kb/project-config.json" 2>/dev/null || true)"
  [ -n "$STOP_GATE" ] || exit 0
else
  exit 0
fi

CH="$(current_chapter 2>/dev/null || true)"
[ -n "$CH" ] || exit 0
[ -f "$CH" ] || exit 0

# Hard-signal scan on the current chapter: truncation + refusal markers only.
# Patterns and the terminal-punctuation predicate are shared with the
# post-write net (lib/common.sh) so the two stay in sync.
NL=$'\n'
SIGNALS=""
LAST_LINE="$(strip_frontmatter "$CH" 2>/dev/null | sed '/^[[:space:]]*$/d' | tail -n1)"
if [ -n "$LAST_LINE" ] && ! ends_with_terminal_punct "$LAST_LINE"; then
  SIGNALS+="truncation: last line does not end in terminal punctuation - '${LAST_LINE:0:40}'${NL}"
fi
REFUSAL="$(refusal_hits "$(strip_frontmatter "$CH" 2>/dev/null || true)" 2>/dev/null || true)"
[ -n "$REFUSAL" ] && SIGNALS+="refusal/AI self-reference markers in current chapter:${NL}${REFUSAL}${NL}"

if [ -n "$SIGNALS" ]; then
  # Block once per chapter: the same signal re-firing on every Stop drives a
  # loop (a stylistic fragment ending can never be "fixed"). The signal is
  # recorded in work/.stop-gate-signaled; a later real regression on the same
  # chapter is caught by the post-write net and the author's own read.
  SIGNALED_FILE="$ROOT/work/.stop-gate-signaled"
  CH_BASE="$(basename "$CH")"
  if [ -f "$SIGNALED_FILE" ] && grep -qxF "$CH_BASE" "$SIGNALED_FILE" 2>/dev/null; then
    exit 0
  fi
  mkdir -p "$ROOT/work" 2>/dev/null || true
  printf '%s\n' "$CH_BASE" >> "$SIGNALED_FILE" 2>/dev/null || true
  printf '%s\n' "Blocked by stop gate (kb/project-config.json stop_gate: true): hard signals in $(basename "$CH"):" >&2
  printf '%s\n' "$SIGNALS" >&2
  exit 2
fi
exit 0
