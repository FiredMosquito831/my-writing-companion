# Vellum series layer — retcon detection catalog (library-spec.md 10).
# Original code. Python >= 3.8, stdlib only, zero pip dependencies.
"""The deterministic retcon-check catalog plus the judgment-flagged rows the
engine emits but never resolves. Matching runs on frontmatter fields and kb
entity names only — never on chapter prose (spec 16-L11).

Findings use the shared finding schema WITHOUT a version bump (spec 16-C2):
two additive optional fields, `book` (ordinal) and `series_scope: true`.
"""
import json
import os
import re
import sys

from . import util
from . import series_bible as sb
from .util import make_finding

AUDIT = "series"


def _f(code, severity, where, quote, issue, key, ordinal=None,
       resolution=None, confidence="deterministic"):
    finding = make_finding(code, severity, where, 0, quote, issue, key=key,
                           confidence=confidence, audit=AUDIT)
    finding["series_scope"] = True
    if ordinal is not None:
        finding["book"] = ordinal
    if resolution is not None:
        finding["resolution"] = resolution
    return finding


# ---------------------------------------------------------------------------
# Field mapping: bible field name -> book kb frontmatter extractor (spec 10 #4)
# ---------------------------------------------------------------------------

FIELD_MAP = {
    "character": (("status", "status"), ("role", "role")),
    "prop": (("status", "custody.status"), ("location", "custody.location")),
    "promise": (("status", "status"),),
    "question": (("status", "status"),),
    "knowledge": (),
}

_UNRESOLVED_PROMISE = ("planned", "planted", "reinforced", "open")


def _kb_value(fm, extractor):
    if "." in extractor:
        head, sub = extractor.split(".", 1)
        node = fm.get(head)
        if isinstance(node, dict):
            return node.get(sub)
        return None
    return fm.get(extractor)


class CatalogContext(object):
    """Everything the catalog needs for one linked book (spec 8.6)."""

    def __init__(self, libroot, manifest, bible, book, book_root):
        self.libroot = libroot
        self.manifest = manifest
        self.bible = bible
        self.book = book
        self.book_root = book_root
        self.ordinal = book["ordinal"]
        self.chapters = util.list_chapters(book_root)
        self.entities = {}
        for kind in ("characters", "props", "promises", "questions",
                     "knowledge"):
            self.entities[kind] = util.load_entity_dir(book_root, kind)

    def all_entities(self):
        for kind, entities in self.entities.items():
            for e in entities:
                yield kind, e

    def entity_by_series_id(self, series_id):
        for kind, e in self.all_entities():
            if e["fm"].get("series-id") == series_id:
                return e
        return None


# ---------------------------------------------------------------------------
# Deterministic checks (spec 10, in catalog order)
# ---------------------------------------------------------------------------

def check_deceased_as_of_start(ctx):
    """#1 — a shared character deceased at ordinal-1 cast in the current
    book's chapter frontmatter `characters:` (mentions are exempt)."""
    out = []
    prev = ctx.ordinal - 1
    for c in ctx.chapters:
        for cid in _strlist(c["fm"].get("characters")):
            ent = next((e for k, e in ctx.all_entities()
                        if k == "characters"
                        and e["fm"].get("id", e["name"][:-3]) == cid), None)
            if ent is None:
                continue
            sid = ent["fm"].get("series-id")
            if not sid:
                continue
            entity = ctx.bible.get("entities", {}).get(sid)
            if not entity or entity.get("scope") != "shared":
                continue
            status = sb.effective_at(ctx.bible, sid, "status", prev)
            if status == "deceased":
                out.append(_f(
                    "deceased-as-of-start", "warning", c["file"], cid,
                    "%s is deceased as of the start of this book (status "
                    "by-book[%d] = deceased, established in the prior book) "
                    "but is cast in %s." % (sid, prev, c["file"]),
                    "series:deceased-as-of-start:%s:%s"
                    % (sid, sb.coord_short(ctx.ordinal, c["num"])),
                    ordinal=ctx.ordinal))
    return out


def check_open_thread_carry(ctx):
    """#2 — a promise/question still unresolved in this book whose series
    canon was established in a published book."""
    out = []
    published_ordinals = {b["ordinal"] for b in sb.linked_books(ctx.manifest)
                          if b["status"] == "published"}
    seen = set()
    for kind, e in ctx.all_entities():
        if kind not in ("promises", "questions"):
            continue
        fm = e["fm"]
        sid = fm.get("series-id")
        if not sid:
            continue
        entity = ctx.bible.get("entities", {}).get(sid)
        if not entity or entity.get("scope") != "shared":
            continue
        est_ordinals = set()
        for coord in entity.get("established-in", []):
            parsed = sb.parse_coordinate(coord)
            if parsed:
                est_ordinals.add(parsed[0])
        if not (est_ordinals & published_ordinals):
            continue
        status = fm.get("status")
        unresolved = (status in _UNRESOLVED_PROMISE if kind == "promises"
                      else status == "open")
        # A populated resolution field closes the thread regardless of the
        # status string. Promise ledgers use payoff-in; question ledgers use
        # resolved-in, and older ledgers may omit either field.
        if fm.get("resolved-in") is not None:
            unresolved = False
        if kind == "promises" and fm.get("payoff-in") is not None:
            unresolved = False
        if not unresolved:
            continue
        if sid in seen:
            continue
        seen.add(sid)
        out.append(_f(
            "open-thread-carry", "warning", e["file"], sid,
            "%s is still unresolved (%s) in this book but was established in "
            "a published book — the open thread carries across the series "
            "boundary." % (sid, status),
            "series:open-thread-carry:%s:%d" % (sid, ctx.ordinal),
            ordinal=ctx.ordinal))
    return out


def check_knowledge_anachronism(ctx):
    """#3 — a world-level knowledge fact (no character holders) whose
    audience-learned-in is claimed in a later book than the book using it.
    Per-book character knowledge stays in book scope (vellum ledger check)."""
    out = []
    for kind, e in ctx.all_entities():
        if kind != "knowledge":
            continue
        fm = e["fm"]
        holders = fm.get("holders")
        if isinstance(holders, list) and any(
                isinstance(h, dict) and h.get("character") for h in holders):
            continue  # per-book character knowledge carve-out
        if fm.get("reveal-planned") is True:
            # An explicitly planned cross-book reveal (dramatic irony): the
            # reader learns it in a later book on purpose, so the later
            # audience-learned-in is the mechanism, not an anachronism.
            continue
        learned = fm.get("audience-learned-in")
        parsed = sb.parse_coordinate(learned)
        if parsed is None:
            continue  # bare chapter-NN means the current book: not anachronistic
        if parsed[0] <= ctx.ordinal:
            continue
        sid = fm.get("series-id") or fm.get("id", e["name"][:-3])
        out.append(_f(
            "knowledge-anachronism", "warning", e["file"], str(learned),
            "world-level fact %s claims audience-learned-in %s (book %d) but "
            "is used as active canon in book %d — the fact is claimed learned "
            "in a later book than the one using it."
            % (sid, learned, parsed[0], ctx.ordinal),
            "series:knowledge-anachronism:%s:%d" % (sid, ctx.ordinal),
            ordinal=ctx.ordinal))
    return out


def _field_extractors(entity):
    """Bible field -> kb frontmatter extractor pairs for one entity.

    The curated FIELD_MAP comes first; any other by-book field is compared
    against the same-named frontmatter counterpart in the book kb (spec 11:
    time indexing covers ALL by-book fields, not only character status).
    Value-encoded fields only participate through the curated map.
    """
    mapped = dict(FIELD_MAP.get(entity.get("type"), ()))
    out = []
    for field, fdata in entity.get("fields", {}).items():
        extractor = mapped.pop(field, None)
        if extractor is not None:
            out.append((field, extractor))
        elif isinstance(fdata, dict) and "by-book" in fdata:
            out.append((field, field))
    # curated fields with no bible-side field yet stay in the map (they are
    # skipped at the bible_field None check, preserving catalog behavior)
    out.extend((f, x) for f, x in mapped.items())
    return out


def _iron_clash(file, book_val, sid, field, eff, iron, ordinal, published,
                extra_issue=None):
    """An iron-literal divergence. Severity stays inside the shared finding
    schema's enum ('warning'); the elevation is carried by the
    series:iron-clash key, which downstream consumers match on."""
    if extra_issue:
        issue = extra_issue + (" The field carries iron literals (%s) — any "
                               "divergence is an iron clash."
                               % "; ".join(iron))
    else:
        issue = ("%s.%s matches series canon (%r) but contradicts the "
                 "field's iron literal (%s) — any divergence against an iron "
                 "literal is an iron clash." % (sid, field, eff,
                                                "; ".join(iron)))
    f = _f("canon-divergence", "warning", file, str(book_val), issue,
           "series:iron-clash:%s:%s:%d" % (sid, field, ordinal),
           ordinal=ordinal)
    # A published-book conflict still needs muse/kb-lead judgment; iron only
    # changes the key/class, not resolution.
    if published:
        f["resolution"] = "judgment"
    return f


def check_canon_divergence(ctx):
    """#4 — a shared fact's value in this book kb differs from the by-book
    value at this ordinal. Iron fields elevate to series:iron-clash. Against
    a published book the row is judgment-flagged (retcon record required)."""
    out = []
    published = ctx.book["status"] == "published"
    for kind, e in ctx.all_entities():
        fm = e["fm"]
        sid = fm.get("series-id")
        if not sid:
            continue
        entity = ctx.bible.get("entities", {}).get(sid)
        if not entity or entity.get("scope") != "shared":
            continue
        for field, extractor in _field_extractors(entity):
            bible_field = entity.get("fields", {}).get(field)
            if bible_field is None:
                continue
            iron = [str(x) for x in (bible_field.get("iron") or [])]
            eff = sb.effective_at(ctx.bible, sid, field, ctx.ordinal)
            book_val = _kb_value(fm, extractor)
            if eff is None or book_val is None:
                continue
            if str(book_val) == str(eff):
                # Iron literals are never compared by the divergence branch
                # alone (it only fires when kb != effective). For an
                # immutable `value`-encoded fact the kb value that matches
                # canon but contradicts the iron literal is still a proposed
                # divergence against that literal (spec 4.1): elevate it.
                if iron and "value" in bible_field \
                        and str(book_val) not in iron:
                    out.append(_iron_clash(
                        e["file"], book_val, sid, field, eff, iron,
                        ctx.ordinal, published))
                continue
            key = "series:canon-divergence:%s:%s:%d" % (sid, field,
                                                        ctx.ordinal)
            issue = ("%s.%s diverges at book %d: book kb says %r, series "
                     "canon says %r." % (sid, field, ctx.ordinal, book_val,
                                         eff))
            if iron:
                out.append(_iron_clash(
                    e["file"], book_val, sid, field, eff, iron,
                    ctx.ordinal, published, extra_issue=issue))
            elif published:
                out.append(_f(
                    "canon-divergence", "warning", e["file"], str(book_val),
                    issue + " Book is published (canon frozen): retcon record "
                    "required (draft loses); the author must explicitly "
                    "approve a change to frozen canon.",
                    key, ordinal=ctx.ordinal, resolution="judgment"))
            else:
                out.append(_f(
                    "canon-divergence", "warning", e["file"], str(book_val),
                    issue, key, ordinal=ctx.ordinal))
    return out


def _scan_text_for_report(path):
    """Read a generated report for coordinate scanning.

    Retcon plans record the author's words verbatim (spec 8.7, never
    edited): a bare chapter-NN inside an author_words value is the author's
    content, not an unqualified coordinate, and flagging it would create a
    per-plan nag that can only be silenced by dismissing each new plan.
    author_words values are stripped before the scan.
    """
    text = util.read_file(path)
    return re.sub(r"(?m)^\s*author_words:.*$", "author_words:", text)


def check_unqualified_refs(ctx):
    """#5 — bare chapter-NN where a book-N/chapter-MM coordinate is
    expected, in series files (errata), retcon/bootstrap plans, and
    handoff docs."""
    out = []
    targets = []
    errata = sb.errata_path(ctx.libroot)
    if os.path.exists(errata):
        targets.append(("errata", errata))
    series_dir = os.path.join(ctx.libroot, "series")
    if os.path.isdir(series_dir):
        for name in sorted(os.listdir(series_dir)):
            if name.endswith(".md") and name != "errata.md":
                targets.append(("series/" + name[:-3],
                                os.path.join(series_dir, name)))
    handoff = os.path.join(ctx.libroot, "handoff")
    if os.path.isdir(handoff):
        for name in sorted(os.listdir(handoff)):
            if name.endswith(".md"):
                targets.append(("handoff/" + name[:-3],
                                os.path.join(handoff, name)))
    reports = os.path.join(ctx.libroot, "reports")
    if os.path.isdir(reports):
        for name in sorted(os.listdir(reports)):
            if name.endswith(".md"):
                targets.append((name[:-3], os.path.join(reports, name)))
    for label, path in targets:
        try:
            text = _scan_text_for_report(path)
        except OSError:
            continue
        for ref in sb.find_unqualified_refs(text):
            num = ref.split("-", 1)[1]
            where = ("series/errata.md" if label == "errata"
                     else "series/%s.md" % label if label.startswith(
                         ("series/", "handoff/"))
                     else "series/reports/%s.md" % label)
            out.append(_f(
                "unqualified-ref", "suggestion", where,
                ref,
                "bare %r where a book-N/chapter-MM coordinate is expected "
                "(e.g. %s); the qualified form is mandatory in series files "
                "and plans." % (ref, sb.coord_slash(ctx.ordinal, int(num))),
                "series:unqualified-ref:%s:%s" % (label, ref),
                ordinal=ctx.ordinal))
    return out


def check_orphan_book_refs(ctx):
    """#6 — by-book entries for an ordinal whose book is unlinked or
    missing from the manifest (canon remembers detached books)."""
    out = []
    for eid, entity in ctx.bible.get("entities", {}).items():
        for fname, fdata in entity.get("fields", {}).items():
            by_book = fdata.get("by-book")
            if not isinstance(by_book, dict):
                continue
            for o in sorted(by_book):
                try:
                    ordinal = int(o)
                except ValueError:
                    continue
                book = sb.book_by_ordinal(ctx.manifest, ordinal)
                if book is not None and book.get("unlinked_at") is None:
                    continue
                out.append(_f(
                    "orphan-book-ref", "note", "series/bible.json",
                    "%s.%s[%s]" % (eid, fname, o),
                    "%s carries by-book[%s] for book %d whose link is "
                    "detached or missing — orphan-book retention (canon "
                    "remembers the detached book)." % (eid, o, ordinal),
                    "series:orphan-book-ref:%s:%s:%s" % (eid, fname, o),
                    ordinal=ordinal))
    return out


def check_id_mismatch(ctx):
    """#7 — a book kb entity joined via alias has a different internal kb id
    from the bible series_id (advisory). Generic over entity types: the
    name-equality inference (kb name equals bible name -> exact join, else
    alias join) decides, for characters and for props/promises/questions/
    knowledge alike."""
    out = []
    for kind, e in ctx.all_entities():
        fm = e["fm"]
        sid = fm.get("series-id")
        if not sid:
            continue
        entity = ctx.bible.get("entities", {}).get(sid)
        if entity is None:
            continue  # unresolvable ids are validate's series:id-mismatch
        kb_id = fm.get("id", e["name"][:-3])
        if kb_id == sid:
            continue
        # Name-equality inference (characters carry `name:`, the other
        # ledger kinds carry `title:`): an exact name join is not an alias
        # join, so the id difference is not advisory-worthy.
        kb_name = fm.get("name") or fm.get("title")
        if sb._norm_name(kb_name) == sb._norm_name(entity.get("name")):
            continue  # joined by exact name — not an alias join
        out.append(_f(
            "id-mismatch", "suggestion", e["file"], kb_id,
            "%s is joined by alias but its kb id %r differs from the bible "
            "series_id %r — confirm the mapping or reclassify (advisory, "
            "not a failure)." % (sid, kb_id, sid),
            "series:id-mismatch:%s:%d" % (kb_id, ctx.ordinal),
            ordinal=ctx.ordinal))
    return out


def check_retcon_log_orphans(ctx):
    """#9 — a retcons.jsonl row the bible does not reflect (bible
    last_touched older than the row): flag for corrective reapply."""
    out = []
    for row in sb.load_retcons(ctx.libroot):
        rid = row.get("rid", "")
        m = sb._RID_RE.match(rid)
        if not m:
            continue
        rid_n = int(m.group(1))
        entity = ctx.bible.get("entities", {}).get(row.get("entity", ""))
        if entity is None:
            continue
        last = entity.get("last_touched")
        if last == rid:
            continue
        last_n = None
        if isinstance(last, str):
            lm = sb._RID_RE.match(last)
            if lm:
                last_n = int(lm.group(1))
        if last_n is not None and last_n >= rid_n:
            continue
        out.append(_f(
            "retcon-log-orphan", "warning", "series/retcons.jsonl", rid,
            "retcon %s mutated %s but the bible shows last_touched %r — the "
            "log row has no matching bible state; reapply or correct "
            "(series:retcon-log-orphan)." % (rid, row.get("entity"), last),
            "series:retcon-log-orphan:%s:%s" % (row.get("entity"), rid),
            ordinal=ctx.ordinal))
    return out


def check_established_refs(ctx):
    """#10 — an established-in coordinate that does not resolve to a
    chapter file in the linked book: a finding, not a crash (spec 16-A6)."""
    out = []
    for eid, entity in ctx.bible.get("entities", {}).items():
        for coord in entity.get("established-in", []):
            out += _established_ref_finding(ctx, eid, coord)
    return out


def _established_ref_finding(ctx, ref_id, coord):
    parsed = sb.parse_coordinate(coord)
    if parsed is None:
        return [_f(
            "unqualified-ref", "warning", "series/bible.json", str(coord),
            "established-in %r for %s is not a book-N/chapter-MM "
            "coordinate (spec 4.2)." % (coord, ref_id),
            "series:unqualified-ref:%s:%s" % (ref_id, str(coord).lower()),
            ordinal=ctx.ordinal)]
    ordinal, num = parsed
    book = sb.book_by_ordinal(ctx.manifest, ordinal)
    where = "series/bible.json"
    if book is None:
        return [_f(
            "established-ref-missing", "warning", where, str(coord),
            "%s established-in %s points at book %d which is not in the "
            "manifest." % (ref_id, coord, ordinal),
            "series:established-ref-missing:%s:%s" % (ref_id, coord),
            ordinal=ordinal)]
    if book.get("unlinked_at") is not None:
        return []  # orphan-book semantics cover detached books
    book_root = sb.book_abspath(ctx.libroot, book)
    if sb.chapter_file(book_root, num) is None:
        return [_f(
            "established-ref-missing", "warning", where, str(coord),
            "%s established-in %s does not resolve to a chapter file in "
            "book %d (%s)." % (ref_id, coord, ordinal, book["title"]),
            "series:established-ref-missing:%s:%s" % (ref_id, coord),
            ordinal=ordinal)]
    return []


# ---------------------------------------------------------------------------
# Judgment-flagged rows (engine emits, never resolves — routed to muse/kb-lead)
# ---------------------------------------------------------------------------

def check_unlinked_cast(ctx):
    """Advisory — a series canon entity (name match, shared scope) appears
    in a chapter cast but carries no series-id join key in the book kb."""
    out = []
    bible_names = {}
    for eid, entity in ctx.bible.get("entities", {}).items():
        if entity.get("scope") == "shared":
            bible_names[sb._norm_name(entity.get("name"))] = eid
    for c in ctx.chapters:
        for cid in _strlist(c["fm"].get("characters")):
            ent = next((e for k, e in ctx.all_entities()
                        if k == "characters"
                        and e["fm"].get("id", e["name"][:-3]) == cid), None)
            if ent is None or ent["fm"].get("series-id"):
                continue
            sid = bible_names.get(sb._norm_name(ent["fm"].get("name")))
            if sid is None:
                continue
            out.append(_f(
                "unlinked-cast", "suggestion", c["file"], cid,
                "%s (%s) is cast in %s but has no series-id join key while a "
                "shared series entity of the same name exists — route to "
                "kb-lead to confirm or add the join key."
                % (cid, ent["fm"].get("name"), c["file"]),
                "series:unlinked-cast:%s:%s"
                % (sid, sb.coord_short(ctx.ordinal, c["num"])),
                ordinal=ctx.ordinal, resolution="judgment",
                confidence="judgment"))
    return out


# ---------------------------------------------------------------------------

def _strlist(v):
    if isinstance(v, list):
        return [x for x in v if isinstance(x, str)]
    if isinstance(v, str):
        return [v]
    return []


def run_catalog(ctx):
    """Run the detection catalog for one linked book.

    Returns (findings, deterministic_count, judgment_count). Archived books
    are fully quiet (spec 12): zero divergence AND history findings.
    """
    if ctx.book["status"] == "archived":
        return [], 0, 0
    findings = []
    findings += check_deceased_as_of_start(ctx)
    findings += check_open_thread_carry(ctx)
    findings += check_knowledge_anachronism(ctx)
    findings += check_canon_divergence(ctx)
    findings += check_unqualified_refs(ctx)
    findings += check_orphan_book_refs(ctx)
    findings += check_id_mismatch(ctx)
    findings += check_retcon_log_orphans(ctx)
    findings += check_established_refs(ctx)
    findings += check_unlinked_cast(ctx)
    judgments = [f for f in findings if f.get("resolution") == "judgment"]
    deterministic = [f for f in findings if f.get("resolution") != "judgment"]
    return findings, len(deterministic), len(judgments)


def filter_series_dismissals(findings, libroot, book_root):
    """Drop findings whose exact finding_id is an active series dismissal.

    A dismissal may also be recorded in wildcard form (finding_id ending in
    ``:*``): it suppresses every finding whose key starts with the wildcard's
    prefix — e.g. ``series:deceased-as-of-start:char:uncle-radu:*`` for an
    intentionally recurring apparition, so the author dismisses once for the
    life of the series instead of once per chapter (spec 10 #1 exempt list).

    An entity-bound dismissal is bound to the kb entity's hash at dismissal
    time; a direct kb edit flips the hash -> the dismissal goes stale and the
    finding re-fires (uniform rule, spec 6.3/16-M2)."""
    dismissals = sb.load_series_exemptions(libroot).get("dismissals", [])
    active = {}
    wildcards = []
    for d in dismissals:
        fid = d.get("finding_id")
        if not fid:
            continue
        if fid.endswith(":*"):
            wildcards.append((fid[:-1], d))
        else:
            active[fid] = d
    out = []
    for f in findings:
        key = f.get("key")
        d = active.get(key)
        if d is None:
            for prefix, wd in wildcards:
                if isinstance(key, str) and key.startswith(prefix):
                    d = wd
                    break
        if d is None:
            out.append(f)
            continue
        bound = _entity_hash_for_finding(f, libroot, book_root)
        if d.get("expires_on_entity_hash") and bound is not None \
                and d["expires_on_entity_hash"] != bound:
            f = dict(f)
            f["issue"] = f.get("issue", "") + (
                " (previously dismissed; the underlying kb entity changed on "
                "disk — the dismissal went stale and the finding re-fires)")
            out.append(f)
        # else: actively dismissed — drop
    return out


def _entity_hash_for_finding(finding, libroot, book_root):
    """Return the bound book-kb file hash when the finding identifies one.

    Most series keys embed a bible id (``char:slug``), while advisory keys
    such as ``id-mismatch`` embed the book-kb id instead.  Resolve both forms
    so dismissal staleness is uniform across the catalog.
    """
    if not book_root:
        return None
    key = finding.get("key", "")
    parts = key.split(":")
    entity_id = None
    for i, part in enumerate(parts[1:], 1):
        if part in ("char", "prop", "promise", "question", "knowledge") \
                and i + 1 < len(parts):
            entity_id = "%s:%s" % (part, parts[i + 1])
            break

    candidates = []
    if entity_id is not None:
        candidates.append(("series-id", entity_id))
    # id-mismatch and future catalog keys may carry a local kb id/name in the
    # first component after the finding code.
    if len(parts) > 2 and parts[2]:
        candidates.append(("id-or-name", parts[2]))

    for kind in ("characters", "props", "promises", "questions", "knowledge"):
        d = os.path.join(book_root, "kb", kind)
        if not os.path.isdir(d):
            continue
        for name in sorted(os.listdir(d)):
            if not name.endswith(".md") or name == "_index.md":
                continue
            path = os.path.join(d, name)
            fm, _ = util.strip_frontmatter_text(util.read_file(path))
            for mode, candidate in candidates:
                if mode == "series-id" and fm.get("series-id") == candidate:
                    return sb.entity_hash_of_file(path)
                if mode == "id-or-name" and (
                        fm.get("id", name[:-3]) == candidate or
                        sb._norm_name(fm.get("name")) ==
                        sb._norm_name(candidate)):
                    return sb.entity_hash_of_file(path)
    # A caller that already has a complete finding can bind directly to its
    # reported file — but only when that file is a book kb entity file
    # (kb/...).  Structural findings (library.json, .vellum/series-link.json,
    # series/bible.json, chapters) must not bind a hash: their referenced
    # resources are rewritten by link/unlink/--fix/retcon-apply, which would
    # stale-loop a dismissal whose underlying condition never changed (the
    # uniform entity-hash rule, spec 6.3, is for book-kb entity findings).
    reported = (finding.get("location") or {}).get("file") or \
        finding.get("file")
    if reported:
        norm = str(reported).replace("\\", "/")
        if norm.startswith("kb/") or "/kb/" in norm:
            path = reported if os.path.isabs(reported) else os.path.join(
                book_root, reported)
            path = os.path.abspath(path)
            root = os.path.abspath(book_root)
            if (os.path.isfile(path) and
                    os.path.commonpath([path, root]) == root):
                return sb.entity_hash_of_file(path)
    return None


def summarize(deterministic, judgment):
    return ("library retcon-check: %d deterministic finding%s, %d "
            "judgment-flagged (muse/kb-lead review)"
            % (deterministic, "" if deterministic == 1 else "s", judgment))
