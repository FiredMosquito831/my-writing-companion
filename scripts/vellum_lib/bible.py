# Vellum deterministic engine — bible validate / reindex / links (spec 5.2).
# Original code; CLI contract port of the story-skills bible CLI (MIT),
# per ATTRIBUTION.md.
"""Frontmatter schema validation for every kb entity, kebab-case ids,
deterministic `_index.md` registries, cross-reference integrity, and the
exemption staleness flip (underlying fact changed -> stale, re-arm once)."""
import hashlib
import json
import os
import re
import sys
from datetime import datetime, timezone

from . import util
from .util import EXIT_OK, EXIT_FINDINGS, make_finding, chapter_num_val

KEBAB_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")

# required frontmatter keys per entity type (spec 7.3 minimums)
REQUIRED = {
    "promise": ["id", "type", "title", "status", "planted-in", "reinforced",
                "payoff-in", "target-by", "abandoned-reason"],
    "question": ["id", "type", "title", "status", "raised-in", "answered-in",
                 "answer"],
    "knowledge": ["id", "type", "title", "statement", "holders",
                  "audience-learned-in", "superseded-by"],
    "prop": ["id", "type", "title", "introduced-in", "custody", "history"],
    "character": ["id", "type", "name", "status", "died-in", "aliases",
                  "pov-eligible"],
}
ENUMS = {
    ("promise", "status"): ("planned", "planted", "reinforced", "paid-off",
                            "abandoned"),
    ("question", "status"): ("open", "answered", "dormant"),
    ("character", "status"): ("alive", "deceased", "unknown"),
    ("prop", "custody.status"): ("in-play", "destroyed", "lost", "resolved"),
    ("knowledge", "certainty"): ("knows", "half-glimpse", "audience-only"),
}


def _validate_all(root):
    """Returns (findings, entities_by_kind). Fails loudly (exit 2) on
    unparseable frontmatter with file + line."""
    findings = []
    kinds = {}
    for kind in ("characters", "promises", "questions", "knowledge", "props"):
        try:
            kinds[kind] = util.load_entity_dir(root, kind)
        except util.FmError as e:
            util.die(str(e))
    all_ids = {k: {e["fm"].get("id", e["name"][:-3]) for e in es}
               for k, es in kinds.items()}
    char_ids = all_ids["characters"]
    knowledge_ids = all_ids["knowledge"]

    for kind, entities in kinds.items():
        singular = kind[:-1] if kind != "knowledge" else "knowledge"
        for e in entities:
            fm = e["fm"]
            eid = fm.get("id", e["name"][:-3])
            where = e["file"]
            # id: present, kebab-case, matches filename
            if not fm.get("id"):
                findings.append(make_finding(
                    "schema-violation", "blocker", where, 0, "id",
                    "%s entity %s is missing its id." % (singular, e["name"]),
                    key="canon:%s-schema" % eid))
            elif not KEBAB_RE.match(str(fm["id"])) or len(str(fm["id"])) > 48:
                findings.append(make_finding(
                    "schema-violation", "blocker", where, 0, str(fm["id"]),
                    "%s id %r is not kebab-case (ASCII, <= 48 chars)."
                    % (singular, fm["id"]),
                    key="canon:%s-schema" % eid))
            if fm.get("id") and e["name"][:-3] != str(fm["id"]):
                findings.append(make_finding(
                    "schema-violation", "blocker", where, 0, e["name"],
                    "file name %s does not match id %r." % (e["name"], fm["id"]),
                    key="canon:%s-schema" % eid))
            if fm.get("type") != singular:
                findings.append(make_finding(
                    "schema-violation", "blocker", where, 0, str(fm.get("type")),
                    "%s entity %s has type %r (expected %r)."
                    % (singular, e["name"], fm.get("type"), singular),
                    key="canon:%s-schema" % eid))
            for req in REQUIRED.get(singular, []):
                if req not in fm:
                    findings.append(make_finding(
                        "schema-violation", "blocker", where, 0, req,
                        "%s entity %s is missing required frontmatter %r "
                        "(use null, not omission)." % (singular, e["name"], req),
                        key="canon:%s-schema" % eid))
            # enums
            for (etype, field), allowed in ENUMS.items():
                if etype != singular:
                    continue
                if field == "custody.status":
                    cust = fm.get("custody")
                    if isinstance(cust, dict) and cust.get("status") not in allowed:
                        findings.append(make_finding(
                            "schema-violation", "blocker", where, 0, "custody",
                            "prop %s custody.status %r not in %s."
                            % (eid, cust.get("status"), list(allowed)),
                            key="canon:%s-schema" % eid))
                elif field == "certainty":
                    holders = fm.get("holders")
                    if isinstance(holders, list):
                        for h in holders:
                            if isinstance(h, dict) and h.get("certainty") not in allowed:
                                findings.append(make_finding(
                                    "schema-violation", "blocker", where, 0,
                                    "certainty",
                                    "knowledge %s: holder %s certainty %r "
                                    "not in %s." % (eid, h.get("character"),
                                                    h.get("certainty"), list(allowed)),
                                    key="canon:%s-schema" % eid))
                elif fm.get(field) is not None and fm.get(field) not in allowed:
                    findings.append(make_finding(
                        "schema-violation", "blocker", where, 0, field,
                        "%s %s has %s: %r (allowed: %s)."
                        % (singular, eid, field, fm.get(field), list(allowed)),
                        key="canon:%s-schema" % eid))
            # cross-references
            findings += _xrefs(singular, eid, fm, char_ids, knowledge_ids,
                               all_ids, kinds, where)
    return findings, kinds


def _chapter_ref_ok(root, v):
    """chapter-NN must exist on disk."""
    num = chapter_num_val(v)
    if num is None:
        return False
    for pad in ("%02d", "%03d", "%d"):
        if os.path.exists(util.project_file(
                root, "manuscript", "chapters", ("chapter-%s.md" % pad) % num)):
            return True
    return False


def _xrefs(singular, eid, fm, char_ids, knowledge_ids, all_ids, kinds, where):
    out = []
    if singular == "promise":
        for field in ("planted-in", "payoff-in", "target-by"):
            if fm.get(field) is not None and not isinstance(fm.get(field), (int, str)):
                pass
        refs = [fm.get(f) for f in ("planted-in", "payoff-in", "target-by")]
        refs += list(fm.get("reinforced") or []) if isinstance(fm.get("reinforced"), list) else []
        for r in refs:
            if r is None:
                continue
            if chapter_num_val(r) is None:
                out.append(make_finding(
                    "broken-reference", "blocker", where, 0, str(r),
                    "promise %s has a non-chapter reference %r (use "
                    "chapter-NN or null)." % (eid, r),
                    key="canon:%s-refs" % eid))
    elif singular == "question":
        for field in ("raised-in", "answered-in"):
            v = fm.get(field)
            if v is not None and chapter_num_val(v) is None:
                out.append(make_finding(
                    "broken-reference", "blocker", where, 0, str(v),
                    "question %s has a non-chapter %s %r."
                    % (eid, field, v),
                    key="canon:%s-refs" % eid))
    elif singular == "knowledge":
        holders = fm.get("holders")
        if isinstance(holders, list):
            for h in holders:
                if isinstance(h, dict) and h.get("character") not in char_ids:
                    out.append(make_finding(
                        "broken-reference", "blocker", where, 0,
                        str(h.get("character")),
                        "knowledge %s: holder %s is not a known character id."
                        % (eid, h.get("character")),
                        key="canon:%s-refs" % eid))
        if fm.get("superseded-by") is not None and fm["superseded-by"] not in knowledge_ids:
            out.append(make_finding(
                "broken-reference", "blocker", where, 0, str(fm["superseded-by"]),
                "knowledge %s: superseded-by %s does not exist."
                % (eid, fm["superseded-by"]),
                key="canon:%s-refs" % eid))
    elif singular == "prop":
        cust = fm.get("custody")
        if isinstance(cust, dict) and cust.get("owner") is not None \
                and cust.get("owner") not in char_ids:
            out.append(make_finding(
                "broken-reference", "blocker", where, 0, str(cust.get("owner")),
                "prop %s: custody owner %s is not a known character id."
                % (eid, cust.get("owner")),
                key="canon:%s-refs" % eid))
        hist = fm.get("history")
        if isinstance(hist, list):
            for h in hist:
                if isinstance(h, dict) and chapter_num_val(h.get("chapter")) is None:
                    out.append(make_finding(
                        "broken-reference", "blocker", where, 0, str(h),
                        "prop %s: history entry without a chapter number: %r"
                        % (eid, h),
                        key="canon:%s-refs" % eid))
    elif singular == "character":
        pass  # aliases are free text
    return out


def _validate_chapter_xrefs(root):
    out = []
    chapters = util.list_chapters(root)
    try:
        chars = {e["fm"].get("id", e["name"][:-3])
                 for e in util.load_entity_dir(root, "characters")}
        promises = {e["fm"].get("id", e["name"][:-3])
                    for e in util.load_entity_dir(root, "promises")}
        props = {e["fm"].get("id", e["name"][:-3])
                 for e in util.load_entity_dir(root, "props")}
    except util.FmError as e:
        util.die(str(e))
    for c in chapters:
        fm = c["fm"]
        for cid in _strlist(fm.get("pov")) + _strlist(fm.get("characters")) \
                + _strlist(fm.get("mentions")):
            if cid and cid not in chars:
                out.append(make_finding(
                    "broken-reference", "blocker", c["file"], 0, cid,
                    "chapter %s references unknown character id %s."
                    % (c["file"], cid),
                    key="canon:%s" % cid))
        for pid in _strlist(fm.get("promises-advanced")):
            if pid and pid not in promises:
                out.append(make_finding(
                    "broken-reference", "blocker", c["file"], 0, pid,
                    "chapter %s references unknown promise id %s."
                    % (c["file"], pid),
                    key="canon:%s" % pid))
        ao = fm.get("approved-outline")
        if ao and not os.path.exists(util.project_file(root, str(ao))):
            out.append(make_finding(
                "broken-reference", "blocker", c["file"], 0, str(ao),
                "chapter %s approved-outline %s does not exist."
                % (c["file"], ao),
                key="canon:%s-outline" % c["name"][:-3]))
    return out


def _strlist(v):
    if isinstance(v, list):
        return [x for x in v if isinstance(x, str)]
    if isinstance(v, str):
        return [v]
    return []


# ---------------------------------------------------------------------------
# Exemption staleness (spec 7.3): underlying fact changed -> stale, re-arm once
# ---------------------------------------------------------------------------

def _flip_stale_exemptions(root):
    """An active exemption recorded with an entity basis (entity + entity_hash
    at dismissal time) flips to stale when that file's content changed."""
    doc = util.load_exemptions(root)
    flipped = 0
    changed = False
    for e in doc.get("exemptions", []):
        if e.get("status") != "active":
            continue
        basis = e.get("entity")
        if not basis or not e.get("entity_hash"):
            continue
        # _entity_for_key records the kb/-prefixed rel path ("kb/clock.md");
        # strip the prefix so the path resolves under root/kb/.
        rel = basis[len("kb/"):] if basis.startswith("kb/") else basis
        p = util.project_file(root, "kb", *rel.split("/"))
        if not os.path.exists(p):
            continue
        with open(p, "rb") as f:
            cur = hashlib.sha256(f.read()).hexdigest()
        if cur != e["entity_hash"]:
            e["status"] = "stale"
            e["stale_note"] = ("previously dismissed; underlying fact changed "
                               "on %s" % datetime.now(timezone.utc).strftime("%Y-%m-%d"))
            flipped += 1
            changed = True
    if changed:
        util.atomic_write(util.exemptions_path(root),
                          json.dumps(doc, indent=2, ensure_ascii=False) + "\n")
    return flipped


# ---------------------------------------------------------------------------
# _index.md registries (deterministic rebuild)
# ---------------------------------------------------------------------------

_INDEX_HEADER = ("<!-- Engine-generated registry (vellum bible reindex). "
                 "Do not hand-edit. -->")


def _write_indexes(root, kinds):
    for kind, entities in kinds.items():
        lines = [_INDEX_HEADER, ""]
        lines.append("| id | title | status |")
        lines.append("|---|---|---|")
        for e in entities:
            fm = e["fm"]
            lines.append("| %s | %s | %s |" % (
                fm.get("id", "?"), fm.get("title", fm.get("name", "?")),
                fm.get("status", "?")))
        lines.append("")
        util.atomic_write(util.project_file(root, "kb", kind, "_index.md"),
                          "\n".join(lines))


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------

def validate(root):
    findings, kinds = _validate_all(root)
    findings += _validate_chapter_xrefs(root)
    flipped = _flip_stale_exemptions(root)
    findings = util.filter_findings(findings, util.load_exemptions(root))
    util.emit_findings(findings)
    if flipped:
        sys.stderr.write("bible validate: %d exemption(s) flipped to stale "
                         "(underlying fact changed) - the finding re-arms "
                         "once; the author re-decides.\n" % flipped)
    if findings:
        sys.stderr.write("bible validate: %d finding(s).\n" % len(findings))
        return EXIT_FINDINGS
    sys.stderr.write("bible validate: clean.\n")
    return EXIT_OK


def links(root):
    findings, kinds = _validate_all(root)
    findings = [f for f in findings
                if f["technique"] in ("broken-reference",)]
    findings += _validate_chapter_xrefs(root)
    findings = util.filter_findings(findings, util.load_exemptions(root))
    util.emit_findings(findings)
    if findings:
        sys.stderr.write("bible links: %d broken reference(s).\n" % len(findings))
        return EXIT_FINDINGS
    sys.stderr.write("bible links: clean.\n")
    return EXIT_OK


def reindex(root):
    findings, kinds = _validate_all(root)
    findings = util.filter_findings(findings, util.load_exemptions(root))
    release = util.lock_state(root)
    try:
        _write_indexes(root, kinds)
        # Repair pass: regenerate derived state + hashes (spec: reindex
        # repairs). _rebuild_unlocked because this caller already holds the
        # state lock.
        from . import state as state_mod
        chapters, characters, promises, questions, knowledge, props = \
            state_mod._gather(root)
        pending = any(c["fm"].get("status") == "accepted" for c in chapters)
        tracking = state_mod._tracking_doc(root, chapters, pending)
        tracking["counts"] = {
            "chapters": len(chapters),
            "characters": len(characters),
            "promises": len(promises),
            "questions": len(questions),
            "knowledge": len(knowledge),
            "props": len(props),
        }
        card = state_mod._build_card(root, chapters, characters, promises,
                                     questions, knowledge, props, pending)
        # Card-cap overflow is handled by _rebuild_unlocked (frozen card +
        # dated flag), not a hard die: reindex is the repair path and must
        # not crash (or refuse) when repair is hardest.
        state_mod._rebuild_unlocked(root, tracking, card)
    finally:
        release()
    if findings:
        sys.stderr.write("bible reindex: registries rebuilt; %d finding(s) "
                         "remain (reindex repairs derived files, not source "
                         "errors).\n" % len(findings))
        util.emit_findings(findings)
        return EXIT_FINDINGS
    sys.stderr.write("bible reindex: registries rebuilt, state repaired.\n")
    return EXIT_OK
