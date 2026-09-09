#!/bin/bash
# pre-compact.sh - PreCompact: snapshot state into work/snapshots/compact-<timestamp>/.
# Adapted from oh-story-claudecode/skills/story-setup/references/templates/hooks/pre-compact.sh - MIT.
# Changes: rewritten for the vellum layout (state card + kb registry _index heads + current
# chapter path + last 40 issue lines); no git operations; silent on success.
#
# Compact discards the running context. This hook preserves the machine-authoritative
# resume state so the next session can rebuild from artifacts on disk. No git ops by
# design (the author may not be in a repo, or may have uncommitted work).
set -u

HOOK_DIR="$(cd "$(dirname "$0")" && pwd)"
source "$HOOK_DIR/lib/common.sh"

read_hook_input

ROOT=$(project_root)
TS="$(date +%Y%m%d-%H%M%S 2>/dev/null || date +%Y%m%d%H%M%S)"
SNAP="$ROOT/work/snapshots/compact-$TS"

# Only snapshot if there is a state card to preserve.
[ -f "$ROOT/state/state-card.md" ] || exit 0

mkdir -p "$SNAP/indices" "$SNAP/state" 2>/dev/null || true

cp "$ROOT/state/state-card.md" "$SNAP/state/state-card.md" 2>/dev/null || true

# Ledger/registry _index heads (the deterministic registries rebuilt by bible reindex).
if [ -d "$ROOT/kb" ]; then
  while IFS= read -r idx; do
    REL="${idx#$ROOT/}"
    mkdir -p "$SNAP/indices/$(dirname "$REL")" 2>/dev/null || true
    # Keep only the head (first 40 lines) - these are index files, small by nature.
    head -n40 "$idx" > "$SNAP/indices/$REL" 2>/dev/null || true
  done < <(find "$ROOT/kb" -name "_index.md" -type f 2>/dev/null || true)
fi

# Current chapter path pointer.
CH="$(current_chapter 2>/dev/null || true)"
if [ -n "$CH" ]; then
  printf '%s\n' "$CH" > "$SNAP/state/current-chapter.txt" 2>/dev/null || true
fi

# Last 40 lines of the active issue log (most recent cold-read ledger).
ISSUES_FILE=""
if [ -d "$ROOT/work/cold-reads" ]; then
  ISSUES_FILE="$(LC_ALL=C ls -1d "$ROOT"/work/cold-reads/*/issues.md 2>/dev/null | tail -n1 || true)"
fi
if [ -n "$ISSUES_FILE" ] && [ -f "$ISSUES_FILE" ]; then
  tail -n40 "$ISSUES_FILE" > "$SNAP/state/issues-tail.txt" 2>/dev/null || true
fi

exit 0
