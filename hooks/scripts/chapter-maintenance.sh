#!/bin/bash
# chapter-maintenance.sh - SubagentStop (matcher writer): advisory maintenance
# pre-pass after the writer finishes.
# Adapted from oh-story-claudecode/skills/story-setup/references/templates/hooks (MIT) -
# the mechanical half of the chapter transaction (the LLM-side fact extraction is done by
# @kb-lead; the acceptance-time close-out fires from check-prose-after-write.sh when a
# chapter edit leaves it at status accepted/final — see write-time-capture.md).
#
# Runs the mechanical pass against the chapter the writer actually touched
# (identified from the SubagentStop transcript; falls back to the highest-numbered
# chapter): vellum wordcount --write && ledger check && state rebuild. Success is
# silent (stdout goes to the transcript, so silent-on-success is mandatory). Failure
# prints the failing check plus a fix direction naming the real cause. Missing
# interpreter OR a broken/unavailable engine falls back to a bash wordcount +
# advisory line.
set -u

HOOK_DIR="$(cd "$(dirname "$0")" && pwd)"
source "$HOOK_DIR/lib/common.sh"

read_hook_input

ROOT=$(project_root)

# Locate the chapter the writer just worked on. The SubagentStop payload carries
# transcript_path; the most recently mentioned manuscript chapter in that
# transcript is the one the writer touched (revision/bridge/alternate-take all
# target arbitrary chapters, so "highest-numbered" is wrong). Fall back to the
# highest-numbered chapter file when the transcript yields nothing.
touched_chapter() {
  local tp="" best="" f n lastnum=-1
  tp="$(extract_payload_field transcript_path 2>/dev/null || true)"
  if [ -n "$tp" ] && [ -f "$tp" ]; then
    # Scan transcript paths back-to-front; the last mention wins. LC_ALL=C byte
    # matching keeps this stable on UTF-8 transcripts.
    while IFS= read -r f; do
      # JSON transcripts escape backslashes as \; collapse them and unify.
      f="$(printf "%s\n" "$f" | tr "\\" "/" | sed "s#/\{2,\}#/#g")"
      case "$f" in
        */manuscript/chapters/chapter-*.md) ;;
        manuscript/chapters/chapter-*.md) f="$ROOT/$f" ;;
        *) continue ;;
      esac
      [ -f "$f" ] || continue
      n=$(basename "$f" | sed -n 's/^chapter-0*\([0-9][0-9]*\)\.md$/\1/p')
      [ -n "$n" ] || continue
      n=$((10#$n))
      if [ "$n" -gt "$lastnum" ]; then lastnum="$n"; best="$f"; fi
    done < <(grep -oE '([A-Za-z]:)?[^"\]*manuscript[\/]+chapters[\/]+chapter-[0-9]+[\.]md' "$tp" 2>/dev/null | tail -n 200 || true)
  fi
  if [ -n "$best" ]; then
    printf '%s\n' "$best"
    return 0
  fi
  current_chapter 2>/dev/null || true
}

CH="$(touched_chapter 2>/dev/null || true)"
if [ -z "$CH" ] || [ ! -f "$CH" ]; then
  exit 0
fi

# Pure-bash wordcount fallback (used when no interpreter resolves or the engine
# itself is unavailable). Counts words per the word rule (runs of
# letters/digits; apostrophes/hyphens join) and updates the word-count
# frontmatter field. Approximate but dependency-free.
bash_wordcount_update() {
  local file="$1" count
  count="$(grep -oE "[A-Za-z0-9]+([''\''-][A-Za-z0-9]+)*" "$file" 2>/dev/null | wc -l | tr -d ' ' || echo 0)"
  case "$count" in ''|*[!0-9]*) count=0 ;; esac
  if grep -qE '^word-count:' "$file" 2>/dev/null; then
    sed -i.bak -E "s/^word-count:.*/word-count: $count/" "$file" 2>/dev/null && rm -f "$file.bak" 2>/dev/null || true
  fi
  printf '%s\n' "$count"
}

if VPY=$(vellum_py) && vellum_run "$VPY" "$VELLUM_ENGINE" --version >/dev/null 2>&1; then
  ENGINE="$VELLUM_ENGINE"
  # wordcount --write (targeted at the touched chapter). Exit 1 = band
  # findings (advisory report, printed below); only >= 2 is a failure.
  WC_RC=0
  WCOUT="$(cd "$ROOT" && vellum_run "$VPY" "$ENGINE" wordcount --write "$CH" 2>&1)" || WC_RC=$?
  if [ "$WC_RC" -ge 2 ]; then
    printf '%s\n' "chapter-maintenance: 'vellum wordcount --write' failed for $(basename "$CH")." >&2
    printf '%s\n' "$WCOUT" >&2
    printf '%s\n' "Fix: check the chapter frontmatter parses (the engine reports file + line for unparseable YAML), then re-run 'python scripts/vellum wordcount --write'." >&2
    exit 0
  fi
  # ledger check (exit 1 = findings, which is a report, not a failure)
  LEDGER="$(cd "$ROOT" && vellum_run "$VPY" "$ENGINE" ledger check 2>&1)"
  LEDGER_RC=$?
  if [ "$LEDGER_RC" -ne 0 ] && [ "$LEDGER_RC" -ne 1 ]; then
    printf '%s\n' "chapter-maintenance: 'vellum ledger check' failed for $(basename "$CH")." >&2
    printf '%s\n' "$LEDGER" >&2
    printf '%s\n' "Fix: the engine could not run the ledger check (schema/usage error) - read its message, repair kb/ or frontmatter, then re-run." >&2
    exit 0
  fi
  # state rebuild
  REBUILD="$(cd "$ROOT" && vellum_run "$VPY" "$ENGINE" state rebuild 2>&1)" || {
    printf '%s\n' "chapter-maintenance: 'vellum state rebuild' failed for $(basename "$CH")." >&2
    printf '%s\n' "$REBUILD" >&2
    printf '%s\n' "Fix: state rebuild writes state/state-card.md (12 KB cap) and _tracking-state.json; check kb/ frontmatter and ledger integrity, then re-run." >&2
    exit 0
  }
  # Findings from the ledger check surface here (advisory pre-pass); silent when clean.
  if [ "$LEDGER_RC" -eq 1 ]; then
    printf '%s\n' "chapter-maintenance: ledger check findings for $(basename "$CH"):" >&2
    printf '%s\n' "$LEDGER" >&2
  fi
  # Success: silent (pending_capture is derived by state rebuild; the
  # acceptance-time close-out in check-prose-after-write.sh completes the
  # transaction when the chapter is accepted).
  exit 0
else
  # No interpreter, or the engine is broken/unavailable: approximate wordcount
  # + advisory naming the real cause.
  WC="$(bash_wordcount_update "$CH" 2>/dev/null || echo 0)"
  if VPY=$(vellum_py); then
    printf '%s\n' "vellum: the deterministic engine is unavailable (scripts/vellum failed to run) - ran a bash word-count fallback for $(basename "$CH") (${WC} words). Reinstall or repair the plugin's scripts/vellum; ledger check and state rebuild were skipped." >&2
  else
    printf '%s\n' "vellum: no Python interpreter found - ran a bash word-count fallback for $(basename "$CH") (${WC} words); full maintenance (ledger check, state rebuild) requires Python >= 3.8. Install Python and re-run the chapter close-out." >&2
  fi
  exit 0
fi
