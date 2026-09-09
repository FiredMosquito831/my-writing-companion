#!/bin/bash
# session-start.sh - SessionStart (startup|resume|clear|compact) advisory resume card.
# Adapted from oh-story-claudecode/skills/story-setup/references/templates/hooks/session-start.sh - MIT.
# Changes: rewritten for the vellum layout (state/state-card.md 7-section card instead of the
# Chinese 上下文.md); reads the vellum project layout; advisory and silent when nothing to show.
#
# If state/state-card.md exists: print the card + last 5 work/ issue lines + pending
# [VERIFY] count + a resume pointer (current chapter and its outline status). Otherwise:
# one line suggesting /vellum:status. Advisory (no blocking).
set -u

HOOK_DIR="$(cd "$(dirname "$0")" && pwd)"
source "$HOOK_DIR/lib/common.sh"

read_hook_input

ROOT=$(project_root)
NL=$'\n'
OUTPUT=""

# Only act on projects that look like a vellum project.
if [ ! -d "$ROOT/manuscript" ] && [ ! -d "$ROOT/kb" ] && [ ! -f "$ROOT/state/state-card.md" ]; then
  exit 0
fi

if [ -f "$ROOT/state/state-card.md" ]; then
  CARD="$(cat "$ROOT/state/state-card.md" 2>/dev/null || true)"
  [ -n "$CARD" ] && OUTPUT+="${CARD}${NL}${NL}"
fi

# Card-over-cap staleness signal: when the 12KB card cap forced a rebuild
# refusal, the printed card is frozen and may lag kb/ — say so instead of
# silently serving stale content.
if [ -f "$ROOT/state/_tracking-state.json" ]; then
  OVER_CAP="$(grep -oE '"card_over_cap"[[:space:]]*:[[:space:]]*"[^"]+"' "$ROOT/state/_tracking-state.json" 2>/dev/null | head -n1 || true)"
  [ -n "$OVER_CAP" ] && OUTPUT+="WARNING: the state card above is frozen (rebuild refused: over the 12KB cap, ${OVER_CAP#*:}). Cut prose in the ledger sources (kb/) and run 'vellum state rebuild' — the card may not reflect current story state.${NL}${NL}"
fi

# Last 5 work/ issue lines (from the most recent cold-read issues ledger, if any).
ISSUES_FILE=""
if [ -d "$ROOT/work/cold-reads" ]; then
  ISSUES_FILE="$(LC_ALL=C ls -1d "$ROOT"/work/cold-reads/*/issues.md 2>/dev/null | tail -n1 || true)"
fi
if [ -n "$ISSUES_FILE" ] && [ -f "$ISSUES_FILE" ]; then
  LAST_ISSUES="$(tail -n5 "$ISSUES_FILE" 2>/dev/null || true)"
  [ -n "$LAST_ISSUES" ] && OUTPUT+="Recent issues (last 5):${NL}${LAST_ISSUES}${NL}${NL}"
fi

# Pending [VERIFY] count across manuscript chapters.
VERIFY_COUNT=0
if [ -d "$ROOT/manuscript/chapters" ]; then
  VERIFY_COUNT="$(grep -rEi -e '\[VERIFY\]' "$ROOT"/manuscript/chapters/chapter-*.md 2>/dev/null | wc -l | tr -d ' ' || true)"
  case "$VERIFY_COUNT" in ''|*[!0-9]*) VERIFY_COUNT=0 ;; esac
fi
[ "$VERIFY_COUNT" -gt 0 ] && OUTPUT+="Pending [VERIFY] markers: ${VERIFY_COUNT} (extract to kb/questions before acceptance).${NL}${NL}"

# Resume pointer: current chapter + outline status.
CH="$(current_chapter 2>/dev/null || true)"
if [ -n "$CH" ]; then
  CH_NUM="$(basename "$CH" | sed -n 's/^chapter-0*\([0-9][0-9]*\)\.md$/\1/p')"
  CH_STATUS="$(fm_field "$CH" status 2>/dev/null || true)"
  OUTLINE="$ROOT/work/outline/chapter-$(printf '%02d' "$CH_NUM" 2>/dev/null || printf '%s' "$CH_NUM").md"
  OUTLINE_STATUS="no outline"
  if [ -f "$OUTLINE" ]; then
    OA="$(fm_field "$OUTLINE" approved 2>/dev/null || true)"
    case "$OA" in
      true)  OUTLINE_STATUS="outline approved" ;;
      false) OUTLINE_STATUS="outline not yet approved" ;;
      *)     OUTLINE_STATUS="outline present (approved flag missing)" ;;
    esac
  fi
  OUTPUT+="Resume: manuscript/chapters/chapter-$(printf '%02d' "$CH_NUM").md (status: ${CH_STATUS:-unknown}; ${OUTLINE_STATUS}).${NL}"
fi

if [ -n "$OUTPUT" ]; then
  printf '%s' "$OUTPUT"
  exit 0
fi

# Nothing on disk yet - a single advisory line.
printf '%s\n' "vellum: no project state found. Run /vellum:status for a full status card."
exit 0
