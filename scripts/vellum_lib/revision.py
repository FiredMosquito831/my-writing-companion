# Vellum deterministic engine — revision-plan cross-check (ADD-3 follow-up).
# Original code (base design credited in ATTRIBUTION.md).
"""`revision status`: report-only cross-check of work/revision-plan.md
against the source artifacts findings came from. A row marked `resolved`
whose source finding is still active (a cold-read CR-### line with no
terminal triage token — | fixed | / | deferred-with-author-signoff | /
| accepted-limitation |) is reported stale; a `declined` row without the
author's verbatim reason is reported as a finding. Writes nothing; not a
gate."""
import os
import re
import sys

from . import util
from .util import EXIT_OK, EXIT_FINDINGS

PLAN_REL = ("work", "revision-plan.md")

ROW_RE = re.compile(r"^REV-\d{3,}\s*\|")
STATUSES = ("open", "in-progress", "resolved", "declined")
# Terminal cold-read triage tokens (issue-format.md — verbatim, pipe-wrapped).
TERMINAL_TOKENS = ("| fixed |", "| deferred-with-author-signoff |",
                   "| accepted-limitation |")

_TROUBLE_TOKENS = ("| triage |", "| fixed |", "| deferred-with-author-signoff |",
                   "| accepted-limitation |")


def _plan_path(root):
    return util.project_file(root, *PLAN_REL)


def parse_plan(text, path):
    """Parse the pipe-delimited rows. Returns (rows, findings) where rows are
    dicts with id/source/status/note and findings are shared-schema entries
    for malformed rows (fail-soft on the plan: bad rows never stop the rest)."""
    rows, findings = [], []
    for i, raw in enumerate(text.split("\n"), 1):
        line = raw.rstrip("\r").strip()
        if not ROW_RE.match(line):
            continue
        fields = [f.strip() for f in line.split("|")]
        # [REV-###, source, location, category, impact, effort, move, status, note?]
        rid = fields[0]
        if len(fields) < 8 or fields[7] not in STATUSES:
            findings.append(util.make_finding(
                "revision-row", "warning", path, i, line[:80],
                "malformed revision-plan row (need 8 pipe fields and status "
                "in %s): %s" % ("/".join(STATUSES), rid),
                key="revision:%s-malformed" % rid))
            continue
        rows.append({
            "id": rid, "source": fields[1], "location": fields[2],
            "category": fields[3], "status": fields[7],
            "note": fields[8] if len(fields) > 8 else "",
            "line": i,
        })
    return rows, findings


def _cold_read_sources(root):
    """All issues.md files under work/cold-reads/, as (relpath, lines)."""
    base = util.project_file(root, "work", "cold-reads")
    out = []
    if not os.path.isdir(base):
        return out
    for dirpath, _dirs, files in os.walk(base):
        for name in sorted(files):
            if name != "issues.md":
                continue
            p = os.path.join(dirpath, name)
            rel = os.path.relpath(p, root).replace("\\", "/")
            with open(p, "r", encoding="utf-8", errors="replace") as f:
                out.append((rel, f.read().split("\n")))
    return out


def _cr_resolved(lines, cr_id):
    """True when the CR-### issue line exists and carries a terminal triage
    token on itself or within the three lines after it (issue-format.md
    triage convention). Returns None when the line is not found."""
    prefix = cr_id + " "
    idx = None
    for i, line in enumerate(lines):
        if line.startswith(prefix) and "|" in line:
            idx = i
            break
    if idx is None:
        return None
    window = lines[idx:idx + 4]
    for line in window:
        for tok in TERMINAL_TOKENS:
            if tok in line:
                return True
    return False


def status(root):
    plan = _plan_path(root)
    if not os.path.exists(plan):
        sys.stdout.write("no revision plan (work/revision-plan.md); "
                         "nothing to check.\n")
        return EXIT_OK

    rows, findings = parse_plan(util.read_file(plan), "work/revision-plan.md")

    counts = {}
    for r in rows:
        counts[r["status"]] = counts.get(r["status"], 0) + 1
    sys.stdout.write("revision plan: %d row(s) — %s\n" % (
        len(rows), ", ".join("%s %d" % (k, counts[k])
                             for k in STATUSES if counts.get(k)) or "none"))

    for r in rows:
        if r["status"] == "declined" and not r["note"]:
            findings.append(util.make_finding(
                "revision-row", "warning", "work/revision-plan.md",
                r["line"], r["id"],
                "declined row %s carries no reason — declined rows record "
                "the author's words verbatim (exemption discipline)"
                % r["id"], key="revision:%s-declined-no-reason" % r["id"]))

    sources = None  # lazily loaded only when a resolved cold-read row exists
    for r in rows:
        if r["status"] != "resolved" or not r["source"].startswith("cold-read:"):
            continue
        if sources is None:
            sources = _cold_read_sources(root)
        cr_id = r["source"].split(":", 1)[1].strip()
        found = False
        resolved_anywhere = False
        for rel, lines in sources:
            resolved = _cr_resolved(lines, cr_id)
            if resolved is None:
                continue
            found = True
            if resolved:
                resolved_anywhere = True
                break
        if found and not resolved_anywhere:
            findings.append(util.make_finding(
                "stale-resolved", "warning", "work/revision-plan.md",
                r["line"], r["source"],
                "row %s marked resolved but %s has no terminal triage token "
                "(| fixed | / | deferred-with-author-signoff | / "
                "| accepted-limitation |) — stale" % (r["id"], cr_id),
                key="revision:%s-stale" % r["id"]))
        elif not found:
            sys.stdout.write("note: %s source %s not found in any "
                             "work/cold-reads/*/issues.md (skipped)\n"
                             % (r["id"], cr_id))

    if findings:
        util.emit_findings(findings)
        return EXIT_FINDINGS
    sys.stdout.write("no stale or malformed rows.\n")
    return EXIT_OK
