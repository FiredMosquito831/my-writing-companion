# Vellum deterministic engine — ledger check (spec 5.2).
# Original code; check catalog adapted from story-skills revision-continuity
# (MIT) and Novel-OS/core/continuity_engine.py (MIT), per ATTRIBUTION.md.
"""Deterministic continuity checks over kb/ ledgers + manuscript frontmatter.

Check catalog (each emits findings in the shared schema, spec 3.6):
- dead-character reappearance (mentions: exempt)
- promise ordering: planted-in <= reinforced < payoff-in
- unfired setups past target-by
- dormant promises (> 3 chapters without movement)
- question states (answered-in/answer consistency)
- POV-not-in-cast
- frontmatter completeness (>= 200 words) — fails loud (frontmatter:incomplete)
- prop custody vs chapter `custody:` frontmatter
- knowledge learned-in violations (holder not in the learning chapter's cast)
- clock-table monotonicity
- outline-verbatim lines present in accepted chapters
- chapter filename / frontmatter number mismatch
"""
import re
import sys

from . import util
from .util import EXIT_OK, EXIT_FINDINGS, make_finding, chapter_num_val

DORMANT_AFTER = 3  # chapters without movement before a promise is dormant
FM_MIN_WORDS = 200


def _collect(root):
    """Run the catalog, filter exemptions, return findings (no printing)."""
    findings = []
    (chapters, characters, promises,
     questions, knowledge, props) = _gather_quiet(root)
    char_by_id = _by_id(characters)
    promise_by_id = _by_id(promises)
    prop_by_id = _by_id(props)
    latest = chapters[-1]["num"] if chapters else 0

    findings += _dead_characters(chapters, char_by_id)
    findings += _promise_checks(promises, promise_by_id, latest, chapters)
    findings += _question_checks(questions)
    findings += _chapter_checks(chapters, char_by_id, prop_by_id)
    findings += _knowledge_checks(knowledge, chapters, char_by_id)
    findings += _clock_checks(root, latest)
    findings += _verbatim_checks(root, chapters)

    return util.filter_findings(findings, util.load_exemptions(root))


def check(root):
    findings = _collect(root)
    util.emit_findings(findings)
    if findings:
        sys.stderr.write("ledger check: %d finding(s).\n" % len(findings))
        return EXIT_FINDINGS
    sys.stderr.write("ledger check: clean.\n")
    return EXIT_OK


def _gather_quiet(root):
    try:
        return (util.list_chapters(root),
                util.load_entity_dir(root, "characters"),
                util.load_entity_dir(root, "promises"),
                util.load_entity_dir(root, "questions"),
                util.load_entity_dir(root, "knowledge"),
                util.load_entity_dir(root, "props"))
    except util.FmError as e:
        util.die(str(e))


def _by_id(entities):
    return {e["fm"].get("id", e["name"][:-3]): e for e in entities}


def _quote_at(body, needle):
    """First line containing needle, trimmed to 60 chars."""
    for line in body.split("\n"):
        if needle in line:
            return line.strip()[:60]
    return ""


def _line_of(body, needle):
    for i, line in enumerate(body.split("\n"), 1):
        if needle in line:
            return i
    return 0


# --- dead characters -------------------------------------------------------

def _dead_characters(chapters, char_by_id):
    out = []
    for c in chapters:
        num = c["num"]
        for cid in _as_str_list(c["fm"].get("characters")):
            ent = char_by_id.get(cid)
            if not ent:
                continue
            fm = ent["fm"]
            if fm.get("status") == "deceased":
                died = chapter_num_val(fm.get("died-in"))
                if died is not None and num > died:
                    out.append(make_finding(
                        "dead-character", "warning",
                        c["file"], _line_of(c["body"], cid),
                        _quote_at(c["body"], cid),
                        "%s (status: deceased, died in chapter %d) appears "
                        "in-scene in chapter %d; mentions: are exempt, so "
                        "move the appearance to mentions: or remove it."
                        % (cid, died, num),
                        key="continuity:%s" % cid))
    return out


# --- promises --------------------------------------------------------------

def _promise_checks(promises, promise_by_id, latest, chapters):
    out = []
    for p in promises:
        fm = p["fm"]
        pid = fm.get("id", p["name"][:-3])
        planted = chapter_num_val(fm.get("planted-in"))
        payoff = chapter_num_val(fm.get("payoff-in"))
        target = chapter_num_val(fm.get("target-by"))
        reinforced = [chapter_num_val(r) for r in _as_str_list(fm.get("reinforced"))]
        reinforced = [r for r in reinforced if r is not None]

        # ordering: planted <= every reinforced < payoff
        if planted is not None and payoff is not None and planted >= payoff:
            out.append(make_finding(
                "promise-ordering", "warning", p["file"], 0, pid,
                "promise %s: planted-in (%s) is not before payoff-in (%s)."
                % (pid, fm.get("planted-in"), fm.get("payoff-in")),
                key="continuity:%s-ordering" % pid))
        bad_reinf = [r for r in reinforced
                     if (planted is not None and r < planted)
                     or (payoff is not None and r >= payoff)]
        if bad_reinf:
            out.append(make_finding(
                "promise-ordering", "warning", p["file"], 0, pid,
                "promise %s: reinforcement chapters %s violate planted-in "
                "(%s) <= reinforced < payoff-in (%s)."
                % (pid, bad_reinf, fm.get("planted-in"), fm.get("payoff-in")),
                key="continuity:%s-ordering" % pid))
        if planted is None and fm.get("status") in ("planted", "reinforced"):
            out.append(make_finding(
                "promise-ordering", "warning", p["file"], 0, pid,
                "promise %s has status %s but no planted-in."
                % (pid, fm.get("status")),
                key="continuity:%s-ordering" % pid))

        # unfired setup past its soft deadline
        status = fm.get("status")
        if (status in ("planned", "planted", "reinforced")
                and payoff is None and target is not None
                and latest >= target):
            out.append(make_finding(
                "promise-overdue", "suggestion", p["file"], 0, pid,
                "promise %s is unfired past its target-by (%s); the setup "
                "owes the reader a payoff or a target-date move."
                % (pid, fm.get("target-by")),
                key="continuity:%s-overdue" % pid))

        # dormant: no movement for > DORMANT_AFTER chapters
        if status in ("planted", "reinforced"):
            moves = [planted] + reinforced
            moves = [m for m in moves if m is not None]
            last = max(moves) if moves else None
            if last is not None and latest - last > DORMANT_AFTER:
                out.append(make_finding(
                    "promise-dormant", "suggestion", p["file"], 0, pid,
                    "promise %s has not moved for %d chapters (last movement "
                    "chapter %d, latest chapter %d)."
                    % (pid, latest - last, last, latest),
                    key="continuity:%s-dormant" % pid))
    return out


# --- questions -------------------------------------------------------------

def _question_checks(questions):
    out = []
    for q in questions:
        fm = q["fm"]
        qid = fm.get("id", q["name"][:-3])
        status = fm.get("status")
        if status == "answered":
            if not fm.get("answered-in") or not fm.get("answer"):
                out.append(make_finding(
                    "question-state", "suggestion", q["file"], 0, qid,
                    "question %s is answered but answered-in/answer is "
                    "missing." % qid,
                    key="continuity:%s-state" % qid))
        elif status == "open" and fm.get("answered-in"):
            out.append(make_finding(
                "question-state", "suggestion", q["file"], 0, qid,
                "question %s is open but carries answered-in %r."
                % (qid, fm.get("answered-in")),
                key="continuity:%s-state" % qid))
    return out


# --- per-chapter checks ----------------------------------------------------

_FM_REQUIRED = ("pov", "characters", "mentions", "promises-advanced")


def _chapter_checks(chapters, char_by_id, prop_by_id):
    out = []
    for c in chapters:
        fm = c["fm"]
        num = c["num"]
        missing = [f for f in _FM_REQUIRED if fm.get(f) is None]
        if c["words"] >= FM_MIN_WORDS and missing:
            out.append(make_finding(
                "frontmatter:incomplete", "warning", c["file"], 0, "",
                "chapter %s (%d words) is missing frontmatter: %s - fill it "
                "(the state rebuild goes blind on blank frontmatter)."
                % (c["file"], c["words"], ", ".join(missing)),
                key="frontmatter:chapter-%02d" % num))
        # filename / frontmatter number mismatch
        fmnum = fm.get("number")
        if isinstance(fmnum, int) and fmnum != num:
            out.append(make_finding(
                "chapter-number-mismatch", "warning", c["file"], 0, "",
                "frontmatter number %d does not match filename %s."
                % (fmnum, c["name"]),
                key="continuity:chapter-%02d-number-mismatch" % num))
        # POV must be in cast
        pov = fm.get("pov")
        cast = _as_str_list(fm.get("characters"))
        if c["words"] >= FM_MIN_WORDS and pov and pov not in cast:
            out.append(make_finding(
                "pov-not-in-cast", "warning", c["file"], 0, pov,
                "chapter %s POV %s does not appear in characters: (present "
                "in-scene)." % (c["file"], pov),
                key="continuity:chapter-%02d-pov-not-in-cast" % num))
        # POV/cast must exist in the bible
        for cid in ([pov] if pov else []) + cast:
            if cid and cid not in char_by_id:
                out.append(make_finding(
                    "broken-reference", "warning", c["file"], 0, cid,
                    "chapter %s references unknown character id %s."
                    % (c["file"], cid),
                    key="canon:%s" % cid))
        # prop custody vs chapter custody: frontmatter
        for prid in _as_str_list(fm.get("custody")):
            ent = prop_by_id.get(prid)
            if not ent:
                out.append(make_finding(
                    "prop-custody", "warning", c["file"], 0, prid,
                    "chapter %s lists custody of unknown prop %s."
                    % (c["file"], prid),
                    key="continuity:%s-custody" % prid))
            else:
                st = (ent["fm"].get("custody") or {}).get("status") \
                    if isinstance(ent["fm"].get("custody"), dict) else None
                if st in ("destroyed", "lost", "resolved"):
                    out.append(make_finding(
                        "prop-custody", "warning", c["file"], 0, prid,
                        "chapter %s lists custody of prop %s whose recorded "
                        "status is %s." % (c["file"], prid, st),
                        key="continuity:%s-custody" % prid))
    return out


# --- knowledge -------------------------------------------------------------

def _knowledge_checks(knowledge, chapters, char_by_id):
    out = []
    ch_by_num = {c["num"]: c for c in chapters}
    for k in knowledge:
        fm = k["fm"]
        kid = fm.get("id", k["name"][:-3])
        holders = fm.get("holders")
        if holders is None:
            continue
        if not isinstance(holders, list):
            out.append(make_finding(
                "schema-violation", "blocker", k["file"], 0, "holders",
                "knowledge %s: holders must be a list." % kid,
                key="canon:%s-schema" % kid))
            continue
        for h in holders:
            if not isinstance(h, dict):
                out.append(make_finding(
                    "schema-violation", "blocker", k["file"], 0, kid,
                    "knowledge %s: holder entries must be maps "
                    "(character/learned-in/certainty)." % kid,
                    key="canon:%s-schema" % kid))
                continue
            cid = h.get("character")
            learned = chapter_num_val(h.get("learned-in"))
            certainty = h.get("certainty")
            if certainty not in ("knows", "half-glimpse", "audience-only"):
                out.append(make_finding(
                    "schema-violation", "blocker", k["file"], 0, kid,
                    "knowledge %s: holder %s has invalid certainty %r "
                    "(knows | half-glimpse | audience-only)."
                    % (kid, cid, certainty),
                    key="canon:%s-schema" % kid))
            if cid and cid not in char_by_id:
                out.append(make_finding(
                    "broken-reference", "warning", k["file"], 0, cid,
                    "knowledge %s: holder %s is not a known character."
                    % (kid, cid),
                    key="canon:%s" % cid))
            if learned is not None:
                ch = ch_by_num.get(learned)
                if ch is None:
                    out.append(make_finding(
                        "knowledge-learned-in", "warning", k["file"], 0, kid,
                        "knowledge %s: %s learned-in %r does not exist."
                        % (kid, cid, h.get("learned-in")),
                        key="continuity:%s-learned-in" % kid))
                elif cid and cid not in _as_str_list(ch["fm"].get("characters")):
                    out.append(make_finding(
                        "knowledge-learned-in", "warning", k["file"], 0, kid,
                        "knowledge %s: %s learned-in %s but is not in that "
                        "chapter's characters: (they were not in scene)."
                        % (kid, cid, h.get("learned-in")),
                        key="continuity:%s-learned-in" % kid))
        sup = fm.get("superseded-by")
        if sup and sup not in {k2["fm"].get("id") for k2 in knowledge}:
            out.append(make_finding(
                "broken-reference", "warning", k["file"], 0, sup,
                "knowledge %s: superseded-by %s does not exist."
                % (kid, sup),
                key="canon:%s" % sup))
    return out


# --- clock -----------------------------------------------------------------

def _clock_checks(root, latest):
    out = []
    path = util.project_file(root, "kb", "clock.md")
    if not _exists(path):
        return out
    rows = []
    for line in util.read_file(path).split("\n"):
        s = line.strip()
        if not s.startswith("|") or s.startswith("|--") or s.startswith("| thread"):
            continue
        rows.append([c.strip() for c in s.strip("|").split("|")])
    for cells in rows:
        if len(cells) < 5:
            continue
        thread, started, _pos, _reading, last = cells[:5]
        sn = _num_from_cell(started)
        ln = _num_from_cell(last)
        if sn is not None and ln is not None and sn > ln:
            out.append(make_finding(
                "clock-non-monotonic", "warning", "kb/clock.md",
                _line_of(util.read_file(path), thread), thread,
                "clock thread %s: started (%s) is after its last chapter "
                "(%s) - the thread runs backwards." % (thread, started, last),
                key="continuity:clock-%s" % re.sub(r"[^a-z0-9-]", "-", thread.lower())))
    return out


def _num_from_cell(cell):
    m = re.search(r"(?:ch(?:apter)?[- ]?)?0*(\d+)", cell, re.IGNORECASE)
    return int(m.group(1)) if m else None


# --- outline verbatim lines -------------------------------------------------

def _verbatim_checks(root, chapters):
    out = []
    outlines = util.outline_files(root)
    by_num = {c["num"]: c for c in chapters}
    for num, o in outlines.items():
        verbatim = o["fm"].get("verbatim")
        if not isinstance(verbatim, list):
            continue
        c = by_num.get(num)
        if not c or c["fm"].get("status") not in ("accepted", "final"):
            continue  # only owed once the chapter is accepted
        for v in verbatim:
            if isinstance(v, str) and v.strip() and v not in c["body"]:
                out.append(make_finding(
                    "outline-verbatim-missing", "warning", c["file"],
                    0, v[:60],
                    "accepted chapter %s is missing its outline-verbatim "
                    "line: %r" % (c["file"], v[:60]),
                    key="continuity:chapter-%02d-verbatim" % num))
    return out


def _exists(p):
    import os
    return os.path.exists(p)


def _as_str_list(v):
    if v is None:
        return []
    if isinstance(v, list):
        return [x for x in v if isinstance(x, str)]
    return [str(v)]
