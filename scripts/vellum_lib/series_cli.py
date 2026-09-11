# Vellum series layer — library CLI dispatch (library-spec.md 8).
# Original code. Python >= 3.8, stdlib only, zero pip dependencies.
"""Argparse dispatch for all `library` subcommands (spec 8). Every command
accepts `--root <library-root>`; if omitted the command refuses (no walk-up
discovery, spec 16-C4/L9). Exit codes: 0 success · 1 findings/artifact ·
2 usage, schema, or environment error. No subcommand returns a blocker exit —
findings are informational (spec 16-A11/L10).
"""
import argparse
import json
import os
import re
import sys
import uuid as uuid_mod

from . import util
from . import series_bible as sb
from . import series_checks as sc
from .util import EXIT_OK, EXIT_FINDINGS, EXIT_ERROR, FmError, LockError

ENGINE_MIN_VERSION = "0.1.1"


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

def _require_root(args):
    root = getattr(args, "root", None)
    if not root:
        util.die("this command requires --root <library-root>; there is no "
                 "walk-up discovery (spec 1.4).")
    if not os.path.isdir(root):
        util.die("--root %s is not a directory." % root)
    return root


def _require_manifest(libroot):
    return sb.load_manifest(libroot)


def _resolve_book(libroot, manifest, book_root):
    if not book_root:
        util.die("this command requires a <book-root> argument.")
    if not os.path.isdir(book_root):
        util.die("book root %s does not exist." % book_root)
    book = sb.book_by_path(manifest, libroot, book_root)
    if book is None:
        return None, os.path.normpath(os.path.abspath(book_root))
    return book, sb.book_abspath(libroot, book)


def _require_linked(libroot, manifest, book_root):
    """Book must be linked (manifest entry with the sidecar's uuid)."""
    book, abspath = _resolve_book(libroot, manifest, book_root)
    if book is None or book.get("unlinked_at") is not None:
        util.die("%s is not linked to this library (run 'library link'); "
                 "there is no filesystem discovery of the library." % book_root)
    return book, abspath


def _emit_findings(findings):
    util.emit_findings(findings)


# ---------------------------------------------------------------------------
# init (spec 8.1)
# ---------------------------------------------------------------------------

def cmd_init(args):
    target = args.root or getattr(args, "root_pos", None)
    if not target:
        util.die("library init requires --root <library-root> (or the "
                 "positional <library-root> documented in the spec).")
    if os.path.exists(target) and not os.path.isdir(target):
        util.die("refusing to init: %s exists and is not a directory."
                 % target)
    marker_dirs = ("kb", "manuscript", "state")
    if os.path.isdir(target):
        for d in marker_dirs:
            if os.path.isdir(os.path.join(target, d)):
                util.die("refusing to init: %s contains a %s/ directory — "
                         "the library is never initialized inside a book "
                         "project (spec 1.4)." % (target, d))
        if os.path.exists(sb.manifest_path(target)):
            util.die("refusing to init: %s already contains a library "
                     "manifest." % target)
    series_title = args.title or os.path.basename(
        os.path.normpath(os.path.abspath(target))) or "Untitled Series"
    series_id = re.sub(r"[^a-z0-9]+", "-",
                       series_title.lower()).strip("-") or "series"
    os.makedirs(os.path.join(target, "series"), exist_ok=True)
    os.makedirs(os.path.join(target, "reports"), exist_ok=True)
    os.makedirs(os.path.join(target, "handoff"), exist_ok=True)
    manifest = {
        "kind": "vellum-library",
        "schema_version": sb.SCHEMA_VERSION,
        "series": {
            "title": series_title,
            "created": sb.now_iso(),
            "next_event_id": 1,
            "next_retcon_id": 1,
        },
        "books": [],
        "engine_min_version_global": ENGINE_MIN_VERSION,
    }
    bible = {
        "series_id": series_id,
        "schema_version": sb.SCHEMA_VERSION,
        "entities": {},
        "timeline": {"events": []},
    }
    release = sb.lock_library(target, "init")
    try:
        sb.write_manifest(target, manifest)
        if not os.path.exists(sb.bible_path(target)):
            sb.write_bible(target, bible)
        if not os.path.exists(sb.retcons_path(target)):
            with open(sb.retcons_path(target), "a", encoding="utf-8"):
                pass
        if not os.path.exists(sb.exemptions_path(target)):
            sb.write_series_exemptions(target, {"dismissals": []})
        if not os.path.exists(sb.errata_path(target)):
            util.atomic_write(sb.errata_path(target),
                              "# Errata — printed vs canon\n\n"
                              "Human-owned: record printed-vs-canon decisions "
                              "for published books here. The engine never "
                              "writes this file; `library validate` only "
                              "checks that every R### referenced exists in "
                              "series/retcons.jsonl.\n")
    finally:
        release()
    sys.stderr.write("library init: created %s (series %r).\n"
                     % (target, series_title))
    return EXIT_OK


# ---------------------------------------------------------------------------
# link (spec 8.2, 9)
# ---------------------------------------------------------------------------

def _story_hash(book_root):
    p = os.path.join(book_root, "kb", "story.md")
    if os.path.exists(p):
        return sb.entity_hash_of_file(p)
    return None


def _kb_entity_count(book_root):
    n = 0
    for kind in ("characters", "props", "promises", "questions", "knowledge"):
        d = os.path.join(book_root, "kb", kind)
        if os.path.isdir(d):
            n += sum(1 for name in os.listdir(d)
                     if name.endswith(".md") and name != "_index.md")
    return n


def _rel_forward(frm, to):
    """Library/book relative path in forward slashes (spec 2). Cross-drive
    roots cannot be made relative on Windows — fall back to the absolute
    normalized path so the pointer stays loadable rather than crashing."""
    try:
        rel = os.path.relpath(os.path.abspath(to), os.path.abspath(frm))
    except ValueError:
        return os.path.normpath(os.path.abspath(to)).replace("\\", "/")
    return rel.replace("\\", "/")


def cmd_link(args):
    libroot = _require_root(args)
    manifest = _require_manifest(libroot)
    if not args.book_root or not os.path.isdir(args.book_root):
        util.die("book root %r does not exist." % args.book_root)
    if not os.path.isdir(os.path.join(args.book_root, "kb")):
        util.die("%s is not a vellum book project (no kb/ directory)."
                 % args.book_root)
    book_root = os.path.normpath(os.path.abspath(args.book_root))
    sidecar, sidecar_err = sb.read_sidecar(book_root)
    if sidecar_err:
        util.die(".vellum/series-link.json is unreadable (%s) — fix or remove "
                 "it before linking; link never guesses over an unreadable "
                 "sidecar." % sidecar_err)
    if sidecar is not None and "schema_version" in sidecar \
            and sidecar["schema_version"] != sb.SCHEMA_VERSION:
        util.die("sidecar declares unknown schema_version %r (this engine "
                 "knows %d) — fail-loud, never guess."
                 % (sidecar["schema_version"], sb.SCHEMA_VERSION))
    # A complete sidecar that names a uuid absent from this manifest belongs
    # to another library unless its pointer resolves to this library (the
    # latter is the recoverable sidecar-first half-link). Reusing that uuid
    # would leave two manifests claiming the same live book.
    if (sidecar and sidecar.get("book_uuid")
            and sidecar.get("series_root")
            and sb.book_by_uuid(manifest, sidecar["book_uuid"]) is None
            and not _sidecar_targets(sidecar, book_root, libroot)):
        util.die("book is already linked to another library; run 'library "
                 "unlink' there first (sidecar series_root %r)."
                 % sidecar.get("series_root"))
    # Idempotent-completing: a sidecar uuid with no manifest entry finishes
    # the entry; an already-complete link is a no-op (spec 8.2/16-A4).
    if sidecar and sidecar.get("book_uuid"):
        existing = sb.book_by_uuid(manifest, sidecar["book_uuid"])
        if existing is not None:
            if existing.get("unlinked_at") is None:
                sys.stderr.write("library link: book %d already linked (uuid "
                                 "%s).\n" % (existing["ordinal"],
                                             existing["book_uuid"]))
                return EXIT_OK
            # Re-linking a detached book revives its original entry: the
            # ordinal and book_uuid are restored so prior by-book canon
            # stays attached to the same ordinal (spec 15.7 -> 15.1).
            return _revive_book(libroot, manifest, existing, book_root,
                                args, sidecar)
    # Duplicate protection: the same directory must not be linked twice while
    # live; a detached entry at the same path is revived, not duplicated.
    dup = sb.book_by_path(manifest, libroot, book_root)
    if dup is not None and dup.get("unlinked_at") is None:
        util.die("book %s is already linked as book %d (duplicate link "
                 "refused)." % (book_root, dup["ordinal"]))
    if dup is not None and dup.get("unlinked_at") is not None \
            and (not sidecar or not sidecar.get("book_uuid")
                 or sidecar["book_uuid"] == dup["book_uuid"]):
        return _revive_book(libroot, manifest, dup, book_root, args, sidecar)
    book_uuid = (sidecar or {}).get("book_uuid") or str(uuid_mod.uuid4())
    ordinals = [b["ordinal"] for b in manifest.get("books", [])]
    ordinal = (max(ordinals) + 1) if ordinals else 1
    status = (sidecar or {}).get("status") or args.status
    if status not in sb.BOOK_STATUSES:
        util.die("status %r not in %s." % (status, list(sb.BOOK_STATUSES)))
    title = util.load_story(book_root).get("title") or \
        os.path.basename(book_root)
    story_hash = _story_hash(book_root)
    # Sidecar first, manifest second: a crash between the two writes leaves a
    # recoverable half-state detected by validate (spec 8.2).
    release = sb.lock_library(libroot, "link")
    try:
        # Re-load inside the critical section: two concurrent links (or a
        # link racing a bootstrap --apply) must serialize through the lock
        # so neither clobbers the other's manifest entry (spec 8.0).
        manifest = sb.load_manifest(libroot)
        if sb.book_by_uuid(manifest, book_uuid) is not None or (
                sb.book_by_path(manifest, libroot, book_root) is not None
                and sb.book_by_path(manifest, libroot,
                                    book_root).get("unlinked_at") is None):
            util.die("book state changed concurrently while linking; "
                     "re-run 'library link'.")
        ordinals = [b["ordinal"] for b in manifest.get("books", [])]
        ordinal = (max(ordinals) + 1) if ordinals else 1
        sb.write_sidecar(book_root, {
            "series_root": _rel_forward(book_root, libroot),
            "book_uuid": book_uuid,
            "ordinal": ordinal,
            "status": status,
            "engine_min_version": ENGINE_MIN_VERSION,
        })
        manifest["books"].append({
            "book_uuid": book_uuid,
            "title": title,
            "path": _rel_forward(libroot, book_root),
            "ordinal": ordinal,
            "status": status,
            "linked_at": sb.now_iso(),
            "unlinked_at": None,
            "engine_min_version": ENGINE_MIN_VERSION,
            "kb_entity_count": _kb_entity_count(book_root),
            "story_hash_at_link": story_hash,
        })
        sb.write_manifest(libroot, manifest)
    finally:
        release()
    sys.stderr.write("library link: book %d (%s, %s) linked as %s.\n"
                     % (ordinal, title, status, book_uuid))
    return EXIT_OK


def _revive_book(libroot, manifest, entry, book_root, args, sidecar):
    """Re-attach a previously unlinked book: same uuid and ordinal, entry
    refreshed, unlinked_at cleared (spec 15.7 remigration)."""
    status = (sidecar or {}).get("status") or entry.get("status") \
        or args.status
    if status not in sb.BOOK_STATUSES:
        util.die("status %r not in %s." % (status, list(sb.BOOK_STATUSES)))
    title = util.load_story(book_root).get("title") or entry.get("title") \
        or os.path.basename(book_root)
    release = sb.lock_library(libroot, "link")
    try:
        # Re-load inside the critical section and refresh the live entry, so
        # a concurrent manifest writer is not clobbered (spec 8.0).
        manifest = sb.load_manifest(libroot)
        entry = sb.book_by_uuid(manifest, entry["book_uuid"])
        if entry is None:
            util.die("book entry vanished while linking; re-run "
                     "'library link'.")
        sb.write_sidecar(book_root, {
            "series_root": _rel_forward(book_root, libroot),
            "book_uuid": entry["book_uuid"],
            "ordinal": entry["ordinal"],
            "status": status,
            "engine_min_version": entry.get("engine_min_version")
            or ENGINE_MIN_VERSION,
        })
        entry["title"] = title
        entry["path"] = _rel_forward(libroot, book_root)
        entry["status"] = status
        entry["linked_at"] = sb.now_iso()
        entry["unlinked_at"] = None
        entry["kb_entity_count"] = _kb_entity_count(book_root)
        entry["story_hash_at_link"] = _story_hash(book_root)
        sb.write_manifest(libroot, manifest)
    finally:
        release()
    sys.stderr.write("library link: book %d (%s, %s) re-linked as %s.\n"
                     % (entry["ordinal"], title, status, entry["book_uuid"]))
    return EXIT_OK


# ---------------------------------------------------------------------------
# unlink (spec 8.3, 10 #6)
# ---------------------------------------------------------------------------

def cmd_unlink(args):
    libroot = _require_root(args)
    manifest = _require_manifest(libroot)
    book, book_root = _resolve_book(libroot, manifest, args.book_root)
    if book is None:
        util.die("unknown book %s (not in the manifest)." % args.book_root)
    bible = sb.load_bible(libroot)
    release = sb.lock_library(libroot, "unlink")
    try:
        book["unlinked_at"] = sb.now_iso()
        sb.write_manifest(libroot, manifest)
        sidecar = sb.sidecar_path(book_root)
        if args.keep_sidecar:
            # author choice (spec 8.3): leave a {} empty marker instead of
            # removing the sidecar entirely
            sb.write_sidecar(book_root, {})
        else:  # default: remove (spec 8.3)
            try:
                os.unlink(sidecar)
            except OSError:
                pass
        # orphan-book semantics: canon is retained, never deleted
    finally:
        release()
    # series:orphan-book-ref advisories listing retained canon entries
    ordinal = book["ordinal"]
    advisories = []
    for eid, entity in bible.get("entities", {}).items():
        for fname, fdata in entity.get("fields", {}).items():
            by_book = fdata.get("by-book")
            if isinstance(by_book, dict) and str(ordinal) in by_book:
                advisories.append(util.make_finding(
                    "orphan-book-ref", "note", "series/bible.json", 0,
                    "%s.%s[%s]" % (eid, fname, ordinal),
                    "%s retains by-book[%s] for the unlinked book %d — "
                    "orphan-book retention; canon remembers the detached "
                    "book." % (eid, ordinal, ordinal),
                    key="series:orphan-book-ref:%s:%s:%s"
                        % (eid, fname, ordinal),
                    audit="series"))
    _emit_findings(advisories)
    sys.stderr.write("library unlink: book %d detached; %d orphan canon "
                     "reference(s) retained.\n"
                     % (ordinal, len(advisories)))
    return EXIT_OK


# ---------------------------------------------------------------------------
# validate (spec 8.4)
# ---------------------------------------------------------------------------

def cmd_validate(args):
    libroot = _require_root(args)
    manifest = _require_manifest(libroot)
    bible = sb.load_bible(libroot)
    findings = []
    # Per-book checks
    for book in manifest.get("books", []):
        ordinal = book["ordinal"]
        root = sb.book_abspath(libroot, book)
        if not os.path.isdir(root) or not os.path.isdir(os.path.join(root, "kb")):
            findings.append(util.make_finding(
                "book-missing", "warning", "library.json", 0, book["path"],
                "book %d (%s) path %s does not resolve to a book project."
                % (ordinal, book["title"], book["path"]),
                key="series:book-missing:%s" % book["book_uuid"],
                audit="series"))
            continue
        # An unlinked book is no longer probed (spec 2): only the structural
        # sidecar check below still applies to it — its kb content (stale
        # series-ids, old engine copies) stays quiet after detach.
        if book.get("unlinked_at") is not None:
            if not os.path.exists(sb.sidecar_path(root)):
                findings.append(util.make_finding(
                    "half-linked", "warning", "library.json", 0,
                    book["book_uuid"],
                    "book %d has a manifest entry but no "
                    ".vellum/series-link.json sidecar — half-linked state."
                    % ordinal,
                    key="series:half-linked:%s" % book["book_uuid"],
                    audit="series"))
            continue
        if not os.path.exists(sb.sidecar_path(root)):
            findings.append(util.make_finding(
                "half-linked", "warning", "library.json", 0,
                book["book_uuid"],
                "book %d has a manifest entry but no .vellum/series-link.json "
                "sidecar — half-linked state." % ordinal,
                key="series:half-linked:%s" % book["book_uuid"],
                audit="series"))
        else:
            sidecar, sidecar_err = sb.read_sidecar(root)
            if sidecar_err:
                # An unreadable sidecar is not a stale one: report the parse
                # error under its own finding key so the author sees the real
                # fault, still repairable by --fix (spec 3/8.4).
                findings.append(util.make_finding(
                    "sidecar-unreadable", "warning",
                    ".vellum/series-link.json", 0, book["book_uuid"],
                    "book %d's .vellum/series-link.json is unreadable (%s); "
                    "validate --fix will regenerate it from the manifest."
                    % (ordinal, sidecar_err),
                    key="series:sidecar-unreadable:%s" % book["book_uuid"],
                    audit="series"))
            else:
                if "schema_version" in sidecar \
                        and sidecar["schema_version"] != sb.SCHEMA_VERSION:
                    util.die("sidecar for book %d declares unknown "
                             "schema_version %r — fail-loud, never guess."
                             % (ordinal, sidecar["schema_version"]))
                stale = _stale_sidecar_fields(libroot, book, root, sidecar)
                if stale:
                    findings.append(util.make_finding(
                        "half-linked", "warning",
                        ".vellum/series-link.json", 0, book["book_uuid"],
                        "book %d has a stale series-link sidecar (%s); "
                        "validate --fix will regenerate it from the manifest."
                        % (ordinal, ", ".join(stale)),
                        key="series:half-linked:%s" % book["book_uuid"],
                        audit="series"))
        # engine-copy lag (spec 8.4/16-L2): in-project scripts/ copy older
        # than the required engine version is advisory
        lag = _engine_copy_lag(root, book)
        if lag:
            findings.append(util.make_finding(
                "engine-copy-lag", "note", "scripts/vellum_lib/__init__.py",
                0, lag,
                "book %d carries an in-project engine copy (%s) older than "
                "engine_min_version — series commands still work from the "
                "library engine; upgrade the copy or remove it."
                % (ordinal, lag),
                key="series:engine-copy-lag:%d" % ordinal, audit="series"))
        # series-id: frontmatter keys must resolve to real bible entities
        findings += _series_id_resolution(libroot, manifest, bible, book, root)
    # Orphan sidecars passed as extra positional book roots
    for extra in (args.book_roots or []):
        if os.path.isdir(os.path.join(extra, ".vellum")) \
                and sb.load_sidecar(extra) is not None:
            sidecar = sb.load_sidecar(extra)
            uuid_v = sidecar.get("book_uuid")
            # Only sidecars that point at THIS library are half-linked here;
            # a book linked to a sibling library is not this manifest's defect.
            if uuid_v and _sidecar_targets(sidecar, extra, libroot) \
                    and sb.book_by_uuid(manifest, uuid_v) is None:
                findings.append(util.make_finding(
                    "half-linked", "warning", ".vellum/series-link.json", 0,
                    str(uuid_v),
                    "%s has a series-link sidecar but no manifest entry — "
                    "half-linked state; re-run 'library link' to complete."
                    % extra,
                    key="series:half-linked:%s" % uuid_v, audit="series"))
    else_scan = args.book_roots or []
    if not else_scan:
        # spec 8.4/T4: the documented plain `library validate` must itself
        # detect the crash-between-writes half state. Book roots conventionally
        # sit beside the library root, so scan the library's siblings for
        # sidecar-carrying books whose uuid is missing from the manifest.
        for extra in _sibling_book_roots(libroot):
            sidecar = sb.load_sidecar(extra)
            uuid_v = (sidecar or {}).get("book_uuid")
            if uuid_v and _sidecar_targets(sidecar, extra, libroot) \
                    and sb.book_by_uuid(manifest, uuid_v) is None:
                findings.append(util.make_finding(
                    "half-linked", "warning", ".vellum/series-link.json", 0,
                    str(uuid_v),
                    "%s has a series-link sidecar but no manifest entry — "
                    "half-linked state; re-run 'library link' to complete."
                    % extra,
                    key="series:half-linked:%s" % uuid_v, audit="series"))
    # established-in resolution (entities + timeline), finding not crash
    for eid, entity in bible.get("entities", {}).items():
        for coord in entity.get("established-in", []):
            findings += _established_ref_finding(libroot, manifest, bible,
                                                 eid, coord)
    for ev in bible.get("timeline", {}).get("events", []):
        if not sb.when_is_iso(ev.get("when")):
            findings.append(util.make_finding(
                "timeline-unparsed-when", "warning", "series/bible.json", 0,
                str(ev.get("when")),
                "timeline event %s has a non-ISO-8601 `when` (%r) — "
                "structured dates only (spec 16-C8)." % (ev["eid"],
                                                         ev.get("when")),
                key="series:timeline-unparsed-when:%s" % ev["eid"],
                audit="series"))
        for coord in ev.get("established-in", []) if isinstance(
                ev.get("established-in"), list) else [ev.get("established-in")]:
            if coord:
                findings += _established_ref_finding(
                    libroot, manifest, bible, "timeline:%s" % ev["eid"], coord)
    # errata refs exist
    findings += _errata_refs(libroot)
    # retcon log orphans (spec 8.7: validate recovers partial applies)
    findings += _retcon_log_orphans(libroot, bible)
    # No book root: validate-scope structural findings (book-missing,
    # half-linked, timeline-unparsed-when) are never bound to an entity hash,
    # so their dismissals cannot go stale when link/unlink/--fix rewrites
    # library.json or the sidecars (spec 6.3's uniform rule is for book-kb
    # entity findings only).
    findings = sc.filter_series_dismissals(findings, libroot, None)
    _emit_findings(findings)
    if args.fix:
        release = sb.lock_library(libroot, "validate --fix")
        try:
            _fix_sidecars(libroot, manifest)
            manifest = _fix_manifest_counters(libroot, manifest)
        finally:
            release()
        sys.stderr.write("library validate --fix: sidecars regenerated, "
                         "counters verified.\n")
    if findings:
        sys.stderr.write("library validate: %d finding(s).\n" % len(findings))
        return EXIT_FINDINGS
    sys.stderr.write("library validate: clean.\n")
    return EXIT_OK


def _sidecar_targets(sidecar, book_root, libroot):
    """True when the sidecar's series_root resolves to this library root."""
    sr = (sidecar or {}).get("series_root")
    if not sr or not isinstance(sr, str):
        return False
    resolved = os.path.normcase(os.path.normpath(os.path.join(
        os.path.abspath(book_root), sr)))
    return resolved == os.path.normcase(os.path.normpath(
        os.path.abspath(libroot)))


def _sibling_book_roots(libroot):
    """One-level scan of the library root's siblings for book projects
    carrying a .vellum/series-link.json sidecar (recoverable half-state
    detection without requiring the undocumented positional argument)."""
    parent = os.path.dirname(os.path.abspath(libroot)) or os.curdir
    out = []
    try:
        names = sorted(os.listdir(parent))
    except OSError:
        return out
    for name in names:
        candidate = os.path.join(parent, name)
        if os.path.normcase(os.path.abspath(candidate)) == \
                os.path.normcase(os.path.abspath(libroot)):
            continue
        if os.path.isdir(candidate) and \
                os.path.isfile(sb.sidecar_path(candidate)):
            out.append(candidate)
    return out


def _engine_copy_lag(book_root, book):
    init_py = os.path.join(book_root, "scripts", "vellum_lib", "__init__.py")
    if not os.path.exists(init_py):
        return None
    try:
        text = util.read_file(init_py)
    except OSError:
        return None
    m = re.search(r'__version__\s*=\s*["\']([^"\']+)["\']', text)
    if not m:
        return None
    have = m.group(1)
    want = book.get("engine_min_version") or \
        ENGINE_MIN_VERSION

    def parts(v):
        try:
            return tuple(int(x) for x in v.split("."))
        except ValueError:
            return None

    hp, wp = parts(have), parts(want)
    if hp is None or wp is None or hp >= wp:
        return None
    return have


def _series_id_resolution(libroot, manifest, bible, book, root):
    out = []
    for kind in ("characters", "props", "promises", "questions", "knowledge"):
        d = os.path.join(root, "kb", kind)
        if not os.path.isdir(d):
            continue
        for name in sorted(os.listdir(d)):
            if not name.endswith(".md") or name == "_index.md":
                continue
            path = os.path.join(d, name)
            fm, _ = util.strip_frontmatter_text(util.read_file(path))
            sid = fm.get("series-id")
            if sid and sid not in bible.get("entities", {}):
                out.append(util.make_finding(
                    "id-mismatch", "warning", "kb/%s/%s" % (kind, name), 0,
                    str(sid),
                    "series-id %s does not resolve to a real bible entity."
                    % sid,
                    key="series:id-mismatch:%s:%d"
                        % (fm.get("id", name[:-3]), book["ordinal"]),
                    audit="series"))
    return out


def _established_ref_finding(libroot, manifest, bible, ref_id, coord):
    parsed = sb.parse_coordinate(coord)
    if parsed is None:
        return [util.make_finding(
            "unqualified-ref", "warning", "series/bible.json", 0, str(coord),
            "established-in %r for %s is not a book-N/chapter-MM coordinate "
            "(spec 4.2)." % (coord, ref_id),
            key="series:unqualified-ref:%s:%s" % (ref_id, str(coord).lower()),
            audit="series")]
    ordinal, num = parsed
    book = sb.book_by_ordinal(manifest, ordinal)
    if book is None:
        return [util.make_finding(
            "established-ref-missing", "warning", "series/bible.json", 0,
            str(coord),
            "%s established-in %s points at book %d which is not in the "
            "manifest." % (ref_id, coord, ordinal),
            key="series:established-ref-missing:%s:%s" % (ref_id, coord),
            audit="series")]
    if book.get("unlinked_at") is not None:
        return []
    if sb.chapter_file(sb.book_abspath(libroot, book), num) is None:
        return [util.make_finding(
            "established-ref-missing", "warning", "series/bible.json", 0,
            str(coord),
            "%s established-in %s does not resolve to a chapter file in "
            "book %d (%s)." % (ref_id, coord, ordinal, book["title"]),
            key="series:established-ref-missing:%s:%s" % (ref_id, coord),
            audit="series")]
    return []


def _errata_refs(libroot):
    out = []
    p = sb.errata_path(libroot)
    if not os.path.exists(p):
        return out
    known = {r.get("rid") for r in sb.load_retcons(libroot)}
    for ref in re.findall(r"\bR\d+\b", util.read_file(p)):
        if ref not in known:
            out.append(util.make_finding(
                "errata-ref-missing", "warning", "series/errata.md", 0, ref,
                "errata references %s which does not exist in "
                "series/retcons.jsonl." % ref,
                key="series:errata-ref-missing:%s" % ref, audit="series"))
    return out


def _retcon_log_orphans(libroot, bible):
    out = []
    for row in sb.load_retcons(libroot):
        m = sb._RID_RE.match(str(row.get("rid", "")))
        if not m:
            continue
        rid_n = int(m.group(1))
        entity = bible.get("entities", {}).get(row.get("entity", ""))
        if entity is None:
            continue
        last = entity.get("last_touched")
        if last == row["rid"]:
            continue
        last_n = None
        lm = sb._RID_RE.match(str(last)) if isinstance(last, str) else None
        if lm:
            last_n = int(lm.group(1))
        if last_n is not None and last_n >= rid_n:
            continue
        out.append(util.make_finding(
            "retcon-log-orphan", "warning", "series/retcons.jsonl", 0,
            str(row.get("rid")),
            "retcon %s mutated %s but the bible shows last_touched %r — "
            "log row without matching bible state; reapply or correct."
            % (row.get("rid"), row.get("entity"), last),
            key="series:retcon-log-orphan:%s:%s"
                % (row.get("entity"), row.get("rid")),
            audit="series"))
    return out


def _stale_sidecar_fields(libroot, book, root, sidecar):
    """Sidecar fields that disagree with the manifest (drift, not truth)."""
    stale = []
    if sidecar.get("book_uuid") != book["book_uuid"]:
        stale.append("book_uuid")
    if sidecar.get("ordinal") != book["ordinal"]:
        stale.append("ordinal")
    if sidecar.get("status") != book["status"]:
        stale.append("status")
    if sidecar.get("series_root") != _rel_forward(root, libroot):
        stale.append("series_root")
    return stale


def _fix_sidecars(libroot, manifest):
    for book in manifest.get("books", []):
        root = sb.book_abspath(libroot, book)
        if not os.path.isdir(root):
            continue
        expected = {
            "series_root": _rel_forward(root, libroot),
            "book_uuid": book["book_uuid"],
            "ordinal": book["ordinal"],
            "status": book["status"],
            "engine_min_version": book.get("engine_min_version")
            or ENGINE_MIN_VERSION,
        }
        # --fix repairs stale as well as missing sidecars; the manifest is the
        # only source of truth for every sidecar field.
        sidecar = sb.load_sidecar(root)
        if sidecar != expected:
            sb.write_sidecar(root, expected)



def _fix_manifest_counters(libroot, manifest):
    """Repair only monotonic counters, as permitted by validate --fix.

    Counters must be strictly beyond all existing IDs; this prevents a
    recovered or hand-edited manifest from causing duplicate event/retcon IDs.
    """
    changed = False
    max_retcon = 0
    for row in sb.load_retcons(libroot):
        m = sb._RID_RE.match(str(row.get("rid", "")))
        if m:
            max_retcon = max(max_retcon, int(m.group(1)))
    series = manifest["series"]
    if series["next_retcon_id"] <= max_retcon:
        series["next_retcon_id"] = max_retcon + 1
        changed = True
    bible = sb.load_bible(libroot)
    max_event = 0
    for ev in bible.get("timeline", {}).get("events", []):
        m = re.match(r"^E(\d+)$", str(ev.get("eid", "")))
        if m:
            max_event = max(max_event, int(m.group(1)))
    if series["next_event_id"] <= max_event:
        series["next_event_id"] = max_event + 1
        changed = True
    if changed:
        sb.write_manifest(libroot, manifest)
    return manifest


# ---------------------------------------------------------------------------
# bootstrap (spec 8.5)
# ---------------------------------------------------------------------------

def _match_tier(bible, fm, name):
    """Deterministic match tier for one book kb entity: (tier, series_id).
    tier in {"exact", "alias", "ambiguity"}. Matching runs on frontmatter
    fields and kb entity names only — never on chapter prose (spec 16-L11)."""
    sid = fm.get("series-id")
    if sid and sid in bible.get("entities", {}):
        return "exact", sid
    exact = sb.find_entity_by_exact_name(bible, name)
    if exact:
        return "exact", exact
    alias = sb.find_entity_by_alias(bible, name)
    if alias:
        return "alias", alias
    for a in fm.get("aliases") or []:
        alias = sb.find_entity_by_alias(bible, a)
        if alias:
            return "alias", alias
    return "ambiguity", None


def _bootstrap_rows(libroot, manifest, bible, book_root):
    rows = {"exact": [], "alias": [], "ambiguity": []}
    claimed = {}
    for kind in ("characters", "props", "promises", "questions", "knowledge"):
        d = os.path.join(book_root, "kb", kind)
        if not os.path.isdir(d):
            continue
        for name in sorted(os.listdir(d)):
            if not name.endswith(".md") or name == "_index.md":
                continue
            path = os.path.join(d, name)
            fm, _ = util.strip_frontmatter_text(util.read_file(path))
            kb_id = fm.get("id", name[:-3])
            tier, sid = _match_tier(bible, fm, fm.get("name", kb_id))
            if sid and sid in claimed:
                # two book entities plausibly one series character -> [?]
                tier, sid = "ambiguity", None
            if sid:
                claimed[sid] = kb_id
            rows[tier].append({
                "kb_id": kb_id, "kind": kind, "file": path, "fm": fm,
                "series_id": sid, "name": fm.get("name", kb_id),
            })
    return rows


def cmd_bootstrap(args):
    libroot = _require_root(args)
    manifest = _require_manifest(libroot)
    bible = sb.load_bible(libroot)
    book, book_root = _require_linked(libroot, manifest, args.book_root)
    if book["status"] == "archived":
        util.die("library bootstrap refuses: archived books are frozen and "
                 "fully quiet; the layer never touches their canon.")
    rows = _bootstrap_rows(libroot, manifest, bible, book_root)
    if args.apply:
        return _bootstrap_apply(libroot, manifest, bible, book, book_root,
                                args.apply)
    # plan mode (default): write reports/bootstrap-plan-<ts>.md, exit 1
    ts = sb.now_iso().replace(":", "").replace("-", "")
    reports = os.path.join(libroot, "reports")
    os.makedirs(reports, exist_ok=True)
    plan_path = os.path.join(reports, "bootstrap-plan-%s.md" % ts)
    lines = [
        "---", "approved: false", "kind: bootstrap-plan",
        "book_ordinal: %d" % book["ordinal"], "book_title: %s" % book["title"],
        "resolution_notes: {}", "generated: %s" % sb.now_iso(), "---", "",
        "# Bootstrap plan — book %d (%s)" % (book["ordinal"], book["title"]),
        "",
        "Set `approved: true` only after resolving every [?] row with the",
        "author's verbatim resolution notes. `library bootstrap --apply`",
        "refuses otherwise (exit 2).", "",
        "## Exact matches (auto-join)",
        "",
    ]
    for r in rows["exact"]:
        lines.append("- entity: %s" % r["kb_id"])
        lines.append("  kind: %s" % r["kind"])
        lines.append("  tier: exact")
        lines.append("  series_id: %s" % r["series_id"])
        lines.append("")
    if not rows["exact"]:
        lines.append("(none)")
    lines += ["", "## Alias matches (auto-join, series:id-mismatch advisory)",
              ""]
    for r in rows["alias"]:
        lines.append("- entity: %s" % r["kb_id"])
        lines.append("  kind: %s" % r["kind"])
        lines.append("  tier: alias")
        lines.append("  series_id: %s" % r["series_id"])
        lines.append("  advisory: series:id-mismatch")
        lines.append("")
    if not rows["alias"]:
        lines.append("(none)")
    lines += ["", "## [?] Ambiguity rows (human resolution required)", "",
              "No series-id is written and no canon is promoted for [?] rows",
              "until the author resolves them. Fill `resolution:` with the",
              "target bible series_id, or `local` to keep the entity",
              "book-local, and add the author's verbatim note.", ""]
    for r in rows["ambiguity"]:
        lines.append("- entity: %s" % r["kb_id"])
        lines.append("  kind: %s" % r["kind"])
        lines.append("  name: %s" % r["name"])
        lines.append("  tier: ambiguity")
        lines.append("  resolution: ")
        lines.append("  author_words: \"\"")
    if not rows["ambiguity"]:
        lines.append("(none)")
    util.atomic_write(plan_path, "\n".join(lines) + "\n")
    n_amb = len(rows["ambiguity"])
    sys.stderr.write(
        "library bootstrap: plan written to %s (%d exact, %d alias, %d [?])."
        % (os.path.relpath(plan_path, libroot), len(rows["exact"]),
           len(rows["alias"]), n_amb) + "\n")
    return EXIT_FINDINGS if (rows["exact"] or rows["alias"] or n_amb) \
        else EXIT_OK


def _parse_plan(path):
    if not os.path.exists(path):
        util.die("plan file %s does not exist." % path)
    text = util.read_file(path)
    fm, body = util.strip_frontmatter_text(text)
    rows = []
    cur = None
    in_amb = False
    for line in body.split("\n"):
        s = line.strip()
        if s.startswith("## "):
            in_amb = "Ambiguity" in s or "[?]" in s
            continue
        m = re.match(r"^-\s+entity:\s*(.*)$", s)
        if m:
            if cur:
                rows.append(cur)
            cur = {"entity": m.group(1).strip()}
            continue
        if cur is not None:
            m2 = re.match(r"^(\w[\w-]*):\s*(.*)$", s)
            if m2:
                cur[m2.group(1)] = m2.group(2).strip()
            elif not s:
                rows.append(cur)
                cur = None
    if cur:
        rows.append(cur)
    return fm, rows, in_amb


def _validate_plan_frontmatter(fm, expect_ordinal=None):
    """Fail-loud (exit 2) on malformed plan frontmatter (spec 8)."""
    if fm.get("approved") is not True:
        return  # callers refuse on unapproved plans with their own message
    ordinal = fm.get("book_ordinal")
    if isinstance(ordinal, str) and ordinal.strip().isdigit():
        ordinal = int(ordinal.strip())
    if not isinstance(ordinal, int) or isinstance(ordinal, bool) or ordinal < 1:
        util.die("plan frontmatter book_ordinal %r is not a positive integer."
                 % fm.get("book_ordinal"))
    if expect_ordinal is not None and ordinal != expect_ordinal:
        util.die("plan frontmatter book_ordinal %d does not match the linked "
                 "book's ordinal %d." % (ordinal, expect_ordinal))
    return ordinal


def _author_words_value(raw):
    """Return plan author words without mutating their content.

    The double quotes used by the generated markdown plan are a syntax wrapper
    when they form one symmetric outer pair. Quotes inside the wrapper are
    author content and must remain untouched; whitespace inside it is content
    too. Callers use ``.strip()`` only to test whether the field is empty.
    """
    value = "" if raw is None else str(raw)
    if len(value) >= 2 and value[0] == value[-1] == '"':
        return value[1:-1]
    return value


def _require_bootstrap_resolution_notes(rows, fm):
    """Require an author's non-empty note for every ambiguity row."""
    notes = fm.get("resolution_notes")
    if isinstance(notes, dict):
        notes = {str(k): _author_words_value(v)
                 for k, v in notes.items()}
    else:
        notes = {}
    for row in rows:
        if row.get("tier") != "ambiguity":
            continue
        note = _author_words_value(row.get("author_words", ""))
        if not note.strip():
            note = notes.get(row.get("entity", ""), "")
        if not note.strip():
            util.die("bootstrap --apply refuses: ambiguity row %s has no "
                     "author resolution note." % row.get("entity"))
        row["author_words"] = note
        if not row.get("resolution", "").strip():
            util.die("bootstrap --apply refuses: ambiguity row %s has no "
                     "resolution." % row.get("entity"))
    return rows


def _row_to_match(row, book_root):
    """Recover a book-kb match from a serialized bootstrap plan row."""
    kb_id = row.get("entity", "")
    kind = row.get("kind", "characters")
    path = os.path.join(book_root, "kb", kind, kb_id + ".md")
    if not os.path.exists(path):
        # The engine writes entity ids, while filenames are allowed to differ;
        # locate by frontmatter id as a deterministic fallback.
        d = os.path.join(book_root, "kb", kind)
        for name in sorted(os.listdir(d)) if os.path.isdir(d) else []:
            if not name.endswith(".md") or name == "_index.md":
                continue
            candidate = os.path.join(d, name)
            fm, _ = util.strip_frontmatter_text(util.read_file(candidate))
            if fm.get("id", name[:-3]) == kb_id:
                path = candidate
                break
    if not os.path.exists(path):
        util.die("bootstrap --apply cannot find kb entity %s in %s."
                 % (kb_id, kind))
    fm, _ = util.strip_frontmatter_text(util.read_file(path))
    return {"kb_id": kb_id, "kind": kind, "file": path, "fm": fm,
            "series_id": row.get("series_id") or row.get("resolution"),
            "name": fm.get("name", kb_id)}


def _bootstrap_rows_from_plan(rows, book_root):
    out = {"exact": [], "alias": [], "ambiguity": []}
    for row in rows:
        tier = row.get("tier", "exact")
        if tier not in out:
            tier = "ambiguity"
        out[tier].append(_row_to_match(row, book_root))
    return out


def _bootstrap_apply(libroot, manifest, bible, book, book_root, plan_path):
    fm, rows, _ = _parse_plan(plan_path)
    if fm.get("approved") is not True:
        util.die("bootstrap --apply refuses: plan frontmatter is not "
                 "approved: true (spec 8.5).")
    _validate_plan_frontmatter(fm, expect_ordinal=book["ordinal"])
    ordinal = book["ordinal"]
    if book["status"] == "archived":
        util.die("bootstrap --apply refuses: archived books are frozen and "
                 "fully quiet; the layer never touches their canon.")
    published = book["status"] == "published"
    rows = _require_bootstrap_resolution_notes(rows, fm)
    # --apply executes the reviewed plan (spec 8.5): every joined row is
    # rebuilt from the plan's own rows via _row_to_match — exact and alias
    # tiers as planned, [?] rows resolved by the author to an existing bible
    # entity or to a new one, and `local` rows skipped with nothing written.
    joined = []
    new_entities = []
    skipped = []
    for r in rows:
        tier = r.get("tier") or "exact"
        if tier == "ambiguity":
            res = (r.get("resolution") or "").strip()
            if res == "local":
                skipped.append(r.get("entity"))
                continue
            m = _row_to_match(r, book_root)
            if res == "new":
                m["series_id"] = _series_id_for_new(m)
                new_entities.append(m)
            elif res in bible.get("entities", {}):
                m["series_id"] = res
            else:
                util.die("bootstrap --apply refuses: [?] row %s resolves to "
                         "unknown bible entity %r." % (r.get("entity"), res))
            joined.append(m)
        elif tier in ("exact", "alias"):
            joined.append(_row_to_match(r, book_root))
        else:
            util.die("bootstrap --apply refuses: unknown plan tier %r on row "
                     "%s." % (tier, r.get("entity")))
    # Preflight every planned kb mutation before writing any series-id line
    # or bible state. A malformed entity file then fails as a whole-command
    # refusal (exit 2) instead of a silent half-join (bible captured, kb
    # never updated) when only the later rows were unwritable.
    for m in joined:
        if m.get("series_id"):
            _require_series_id_injectable(m["file"])
    release = sb.lock_library(libroot, "bootstrap --apply")
    try:
        # Re-load inside the critical section so a concurrent link or retcon
        # --apply is serialized through the lock, not clobbered (spec 8.0).
        manifest = sb.load_manifest(libroot)
        bible = sb.load_bible(libroot)
        # create new bible entities first
        for m in new_entities:
            bible["entities"][m["series_id"]] = {
                "type": _entity_type(m["kind"]),
                "series_id": m["series_id"],
                "name": m.get("name") or m["kb_id"],
                "aliases": [],
                "fields": {},
                "established-in": [],
                "scope": "shared",
                "entity_hash": sb.entity_hash_of_file(m["file"]),
                "last_touched": "bootstrap",
            }
        for m in joined:
            sid = m.get("series_id")
            if not sid:
                continue  # nothing planned for this row
            entity = bible["entities"].get(sid)
            if entity is None:
                continue
            # freeze doctrine: bootstrap for a newly linked published book
            # may establish starting canon, never change pinned values
            if published and _ordinal_pinned(entity, ordinal):
                continue
            _write_series_id(m["file"], sid)
            _seed_by_book(bible, entity, ordinal, m["fm"])
            _seed_established_in(bible, entity, ordinal, m["fm"])
            # spec 4.1: capture-time audit record — sha256 of the book kb
            # entity file at last capture.
            entity["entity_hash"] = sb.entity_hash_of_file(m["file"])
            # spec 4.1: "bootstrap" marks initial capture only — a re-capture
            # must not reset a retcon id that already owns the entity.
            if entity.get("last_touched") in (None, "bootstrap"):
                entity["last_touched"] = "bootstrap"
        sb.write_bible(libroot, bible)
    finally:
        release()
    sys.stderr.write("library bootstrap --apply: %d entity(ies) joined, %d "
                     "left book-local, for book %d; bible updated.\n"
                     % (len(joined), len(skipped), ordinal))
    return EXIT_OK


def _series_id_for_new(row):
    kind = _entity_type(row.get("kind", "characters"))
    slug = re.sub(r"[^a-z0-9]+", "-",
                  str(row.get("kb_id", "")).lower()).strip("-")
    slug = re.sub(r"^(character|prop|promise|question|knowledge)-", "",
                  slug)
    return "%s:%s" % (kind, slug)


def _entity_type(kind_dir):
    singular = {"characters": "character", "props": "prop",
                "promises": "promise", "questions": "question",
                "knowledge": "knowledge"}
    return singular.get(kind_dir, "character")


def _ordinal_pinned(entity, ordinal):
    for fdata in entity.get("fields", {}).values():
        bb = fdata.get("by-book")
        if isinstance(bb, dict) and str(ordinal) in bb:
            return True
    return False


def _require_series_id_injectable(path):
    """Validate a kb file before any bootstrap --apply mutation.

    A plan may contain several joined rows, so checking all files before
    writing prevents earlier rows from acquiring a series-id when a later
    malformed file cannot accept one.
    """
    with open(path, "r", encoding="utf-8-sig", errors="replace",
              newline="") as f:
        text = f.read()
    if re.search(r"^series-id:", text, re.MULTILINE):
        return
    saw_open = False
    for line in text.split("\n"):
        if line.strip() == "---":
            if not saw_open:
                saw_open = True
                continue
            break
        if saw_open and re.match(r"^(id|type):", line):
            return
    util.die("cannot inject series-id into %s: no frontmatter delimiters "
             "or no id:/type: line." % path)


def _write_series_id(path, sid):
    # Read raw (newline='') so the file's own line endings survive the
    # round-trip: the golden-suite contract (spec 17-T1c) says source files
    # differ only by the injected series-id lines, and rewriting a CRLF
    # Windows-authored kb file with LF endings would be a whole-file diff.
    # utf-8-sig strips a leading BOM on read (a BOM'd opener must not hide
    # the frontmatter from the injector); the rewrite is BOM-free UTF-8.
    with open(path, "r", encoding="utf-8-sig", errors="replace",
              newline="") as f:
        text = f.read()
    if re.search(r"^series-id:", text, re.MULTILINE):
        return
    crlf = text.count("\r\n")
    lf = text.count("\n") - crlf
    ending = "\r\n" if crlf > lf else "\n"
    lines = text.split(ending)
    # insert after the id: line (or type: line) inside the frontmatter
    insert_at = None
    saw_open = False
    for i, line in enumerate(lines):
        if line.strip() == "---":
            if not saw_open:
                saw_open = True
                continue
            break
        if saw_open and re.match(r"^(id|type):", line):
            insert_at = i + 1
    if insert_at is None:
        util.die("cannot inject series-id into %s: no frontmatter delimiters "
                 "or no id:/type: line." % path)
    lines.insert(insert_at, "series-id: %s" % sid)
    util.atomic_write(path, ending.join(lines))


def _seed_by_book(bible, entity, ordinal, fm):
    """Deterministic copy of book kb frontmatter into the bible's by-book
    maps for scope: shared fields (no invention, spec 8.5)."""
    etype = entity["type"]
    for field, extractor in sc.FIELD_MAP.get(etype, ()):
        val = sc._kb_value(fm, extractor)
        if val is None:
            continue
        fdata = entity["fields"].setdefault(field, {"by-book": {}})
        if "value" in fdata:
            continue  # immutable book-independent fact: never overwritten
        bb = fdata.setdefault("by-book", {})
        bb.setdefault(str(ordinal), str(val))


# Deterministic established-in provenance per entity type (spec 4.2): the kb
# frontmatter field that names the chapter where the fact entered the story.
_PROVENANCE_FIELD = {
    "promise": "planted-in",
    "question": "raised-in",
    "prop": "introduced-in",
    "knowledge": "audience-learned-in",
}


def _seed_established_in(bible, entity, ordinal, fm):
    """Seed the entity's established-in coordinates from the book kb
    provenance frontmatter (short ordinal:chapter-NN form, spec 4.2).

    Without this the field is permanently empty in the documented workflow
    (the bible is engine-write-only), dead-lettering the do-not-re-explain
    register, open-thread-carry, and the handoff 'established in' register.
    """
    field = _PROVENANCE_FIELD.get(entity.get("type"))
    if field is None:
        return
    raw = fm.get(field)
    if not raw:
        return
    m = re.match(r"^chapter-0*(\d+)$", str(raw).strip(), re.IGNORECASE)
    if not m:
        return  # non-coordinate provenance is not invented here
    coord = sb.coord_short(ordinal, int(m.group(1)))
    coords = entity.setdefault("established-in", [])
    if not isinstance(coords, list):
        coords = entity["established-in"] = []
    if coord not in coords:
        coords.append(coord)


# ---------------------------------------------------------------------------
# retcon-check (spec 8.6) / retcon-plan (8.7) / retcon --apply (8.7)
# ---------------------------------------------------------------------------

def cmd_retcon_check(args):
    libroot = _require_root(args)
    manifest = _require_manifest(libroot)
    bible = sb.load_bible(libroot)
    book, book_root = _require_linked(libroot, manifest, args.book_root)
    ctx = sc.CatalogContext(libroot, manifest, bible, book, book_root)
    findings, _, _ = sc.run_catalog(ctx)
    findings = sc.filter_series_dismissals(findings, libroot, book_root)
    _emit_findings(findings)
    # Summarize the emitted set: the pre-dismissal counts would over-report
    # relative to the rows the author actually sees on stdout.
    det = sum(1 for f in findings if f.get("resolution") != "judgment")
    jud = sum(1 for f in findings if f.get("resolution") == "judgment")
    sys.stderr.write(sc.summarize(det, jud) + "\n")
    return EXIT_FINDINGS if findings else EXIT_OK


def cmd_retcon_plan(args):
    libroot = _require_root(args)
    manifest = _require_manifest(libroot)
    bible = sb.load_bible(libroot)
    book, book_root = _require_linked(libroot, manifest, args.book_root)
    if book["status"] == "archived":
        # spec 12: archived books are fully quiet — no plan, no nagging.
        sys.stderr.write("library retcon-plan: book %d is archived (fully "
                         "quiet); no retcon plan is produced.\n"
                         % book["ordinal"])
        return EXIT_OK
    ctx = sc.CatalogContext(libroot, manifest, bible, book, book_root)
    divergences = sc.check_canon_divergence(ctx)
    # A divergence the author already dismissed is a decided exemption, not
    # a retcon proposal: filter it out exactly like retcon-check does, so
    # the plan never re-litigates a dismissed author decision (spec 6).
    pre = len(divergences)
    divergences = sc.filter_series_dismissals(divergences, libroot,
                                              book_root)
    skipped_dismissed = pre - len(divergences)
    ts = sb.now_iso().replace(":", "").replace("-", "")
    reports = os.path.join(libroot, "reports")
    os.makedirs(reports, exist_ok=True)
    plan_path = os.path.join(reports, "retcon-plan-%s.md" % ts)
    published = book["status"] in ("published", "archived")
    lines = [
        "---", "approved: false", "author_words_required: true",
        "kind: retcon-plan", "book_ordinal: %d" % book["ordinal"],
        "book_title: %r" % book["title"],
        "override_published: %s" % ("false  # required when the plan touches "
                                    "published canon" if published
                                    else "n/a"), "generated: %s"
        % sb.now_iso(), "---", "",
        "# Retcon plan — book %d (%s)" % (book["ordinal"], book["title"]),
        "",
        "Generated by library retcon-plan. Set `approved: true` only after",
        "the author has reviewed every row and filled in `new_by_book` and",
        "`author_words`. %s" % (
            "This plan touches PUBLISHED canon: the default proposal is "
            "`retcon record required` (draft loses); changing frozen canon "
            "additionally requires `override_published: true`."
            if published else ""), "",
        "## Rows", "",
    ]
    for f in divergences:
        sid, field = _divergence_key_parts(f["key"])
        entity = bible.get("entities", {}).get(sid, {})
        fdata = entity.get("fields", {}).get(field, {})
        old_map = fdata.get("by-book") or (
            {"value": fdata["value"]} if "value" in fdata else {})
        lines.append("- entity: %s" % sid)
        lines.append("  field: %s" % field)
        lines.append("  old_by_book: %s"
                     % json.dumps(old_map, ensure_ascii=False))
        lines.append("  new_by_book: ")
        # The finding locates the diverging kb entity file, not a chapter;
        # a fabricated coordinate would misdirect the author's review.
        coord = _chapter_coord_from_finding(f, book["ordinal"])
        if coord:
            lines.append("  coordinate: %s" % coord)
        lines.append("  author_words: \"\"")
        lines.append("")
    if not divergences:
        lines.append("(no divergences — nothing to plan)")
        lines.append("")
    util.atomic_write(plan_path, "\n".join(lines) + "\n")
    sys.stderr.write("library retcon-plan: %d divergence row(s) written to "
                     "%s (%d dismissed row(s) skipped).\n"
                     % (len(divergences), os.path.relpath(plan_path, libroot),
                        skipped_dismissed))
    return EXIT_FINDINGS if divergences else EXIT_OK


def _chapter_coord_from_finding(finding, ordinal):
    """Best-effort book-N/chapter-MM coordinate from a divergence finding.

    Divergence findings point at the kb entity file, which carries no
    chapter; when a chapter is genuinely derivable (future finding shapes),
    use it, otherwise return None and omit the coordinate from the plan row
    rather than defaulting to a fabricated chapter-01."""
    loc = (finding.get("location") or {}).get("file") or ""
    m = re.search(r"chapter-0*(\d+)", loc)
    if m:
        return sb.coord_slash(ordinal, int(m.group(1)))
    return None


def _divergence_key_parts_for_plan(key):
    prefix = "series:iron-clash:" if key.startswith("series:iron-clash:") else "series:canon-divergence:"
    parts = key[len(prefix):].split(":")
    if len(parts) < 4:
        util.die("malformed divergence finding key %r." % key)
    return "%s:%s" % (parts[0], parts[1]), parts[-2]


def _divergence_key_parts(key):
    return _divergence_key_parts_for_plan(key)


def cmd_retcon_apply(args):
    libroot = _require_root(args)
    manifest = _require_manifest(libroot)
    bible = sb.load_bible(libroot)
    plan_path = args.apply
    fm, rows, _ = _parse_plan(plan_path)
    if fm.get("approved") is not True:
        util.die("retcon --apply refuses: plan frontmatter is not approved: "
                 "true (spec 8.7).")
    ordinal = _validate_plan_frontmatter(fm)
    book = sb.book_by_ordinal(manifest, ordinal) if ordinal is not None \
        else None
    if book is None:
        util.die("plan book_ordinal %r does not match a manifest book."
                 % ordinal)
    if book["status"] == "archived":
        util.die("retcon --apply refuses: archived books are frozen and "
                 "fully quiet; no new canon rows may be applied.")
    published = book["status"] == "published"
    if published and fm.get("override_published") is not True:
        util.die("retcon --apply refuses: the plan touches %s canon (canon "
                 "is frozen; draft loses). The author must explicitly "
                 "approve a change with override_published: true in the "
                 "plan frontmatter." % book["status"])
    if not rows:
        sys.stderr.write("library retcon --apply: plan has no rows.\n")
        return EXIT_OK
    # every row needs non-empty author_words (verbatim, to the log)
    for r in rows:
        words = _author_words_value(r.get("author_words"))
        if not words.strip():
            util.die("retcon --apply refuses: row for %s has an empty "
                     "author_words field (the author's words are recorded "
                     "verbatim, spec 8.7)." % r.get("entity"))
    # Pre-validate EVERY row before any commit: a plan whose row 3 is bad
    # must not leave rows 1-2 committed (exit 2 without partial application).
    # The per-row transaction discipline below still guards crashes mid-apply
    # (spec 16-A3/L3); validation is plan-granular, application is row-wise.
    for r in rows:
        _validate_retcon_row(manifest, bible, fm, r)
    applied = 0
    for r in rows:
        # one retcon transaction per row (spec 16-A3/L3)
        is_timeline = (r.get("kind") or "").strip() == "established-before"
        new_map = None
        if not is_timeline:
            new_map = _parse_new_by_book(r.get("new_by_book"))
            if new_map is None:
                util.die("retcon --apply refuses: row for %s has an "
                         "unparseable new_by_book %r."
                         % (r.get("entity"), r.get("new_by_book")))
            if r.get("entity") not in bible.get("entities", {}):
                util.die("retcon --apply refuses: unknown bible entity %s."
                         % r["entity"])
        release = sb.lock_library(libroot, "retcon --apply")
        try:
            manifest = sb.load_manifest(libroot)
            bible = sb.load_bible(libroot)
            rid = "R%03d" % manifest["series"]["next_retcon_id"]
            words = _author_words_value(r.get("author_words"))
            if is_timeline:
                # established-before (spec 8.9): the engine path that mints
                # E### timeline events; ids come from the monotonic counter
                # and are never renumbered.
                event = _apply_established_before(
                    libroot, bible, r, rid, book, words,
                    manifest["series"]["next_event_id"])
                manifest["series"]["next_retcon_id"] += 1
                manifest["series"]["next_event_id"] = \
                    max(manifest["series"]["next_event_id"],
                        int(event["eid"][1:]) + 1)
                sb.write_bible(libroot, bible)
                sb.write_manifest(libroot, manifest)
            else:
                entity = bible["entities"][r["entity"]]
                field_name = r["field"]
                fdata = entity["fields"].setdefault(field_name,
                                                    {"by-book": {}})
                old_map = fdata.get("by-book") or (
                    {"value": fdata["value"]} if "value" in fdata else {})
                _refuse_frozen_ordinal_changes(manifest, fm, r,
                                               field_name, fdata, new_map)
                row = {
                    "rid": rid,
                    "at": sb.now_iso(),
                    "author_words": words,
                    "kind": _row_kind(r, published),
                    "entity": r["entity"],
                    "field": "fields.%s" % field_name,
                    "from_book": book["ordinal"],
                    "old_by_book": old_map,
                    "new_by_book": new_map,
                    "proposed_by": book["ordinal"],
                }
                sb.append_retcon_row(libroot, row)
                # bible state is the truth. new_by_book is merged onto the
                # existing by-book map, never a blind replacement: an author
                # row that fills only the new ordinal must not silently
                # destroy the pinned values of every earlier book (freeze
                # doctrine, spec 11/12 — the map is the queryable truth).
                merged = dict(fdata["by-book"]) \
                    if isinstance(fdata.get("by-book"), dict) else {}
                merged.update(new_map)
                fdata.pop("value", None)
                fdata["by-book"] = merged
                entity["last_touched"] = rid
                sb.write_bible(libroot, bible)
                manifest["series"]["next_retcon_id"] += 1
                sb.write_manifest(libroot, manifest)
                _flush_matching_exemptions(libroot, r["entity"])
        finally:
            release()
        applied += 1
    # Stamp the plan as applied so state-card section 3 ("Open retcons") and
    # handoff stop listing it as pending (spec 8.8).
    _stamp_plan_applied(plan_path)
    sys.stderr.write("library retcon --apply: %d retcon transaction(s) "
                     "applied.\n" % applied)
    return EXIT_OK


def _row_kind(row, published):
    """Row kind for the audit log: the engine default (errata against
    published wording, else fact-change), or the author's explicit `kind:`
    line. reanimation and scope-change are recordable through the same
    approved-plan flow this way (spec 5 kinds; the engine's automatic
    detection only ever proposes fact-change/errata/established-before)."""
    kind = (row.get("kind") or "").strip()
    if kind == "established-before":
        return kind  # timeline rows are handled on their own path
    if kind:
        if kind not in sb.RETCON_KINDS:
            util.die("retcon --apply refuses: row kind %r is not in %s."
                     % (kind, list(sb.RETCON_KINDS)))
        return kind
    return "errata" if published else "fact-change"


def _validate_retcon_row(manifest, bible, plan_fm, row):
    """Fail-loud (exit 2) on any unappliable row, before any commit."""
    kind = (row.get("kind") or "").strip()
    if kind and kind not in sb.RETCON_KINDS:
        util.die("retcon --apply refuses: row kind %r is not in %s."
                 % (kind, list(sb.RETCON_KINDS)))
    if kind == "established-before":
        when = (row.get("when") or "").strip()
        if not sb.when_is_iso(when):
            util.die("retcon --apply refuses: established-before row needs "
                     "an ISO-8601 `when` (structured dates only, spec "
                     "16-C8), got %r." % when)
        if not (row.get("summary") or "").strip():
            util.die("retcon --apply refuses: established-before row has an "
                     "empty summary.")
        coord = (row.get("coordinate") or "").strip()
        if not coord:
            util.die("retcon --apply refuses: established-before rows "
                     "require an explicit book-N/chapter-MM coordinate; "
                     "refusing to fabricate chapter-01 provenance.")
        if sb.parse_coordinate(coord.replace("/", ":", 1)) is None:
            util.die("retcon --apply refuses: established-before coordinate "
                     "%r is not a book-N/chapter-MM coordinate." % coord)
        return
    new_map = _parse_new_by_book(row.get("new_by_book"))
    if new_map is None:
        util.die("retcon --apply refuses: row for %s has an unparseable "
                 "new_by_book %r."
                 % (row.get("entity"), row.get("new_by_book")))
    entity = bible.get("entities", {}).get(row.get("entity"))
    if entity is None:
        util.die("retcon --apply refuses: unknown bible entity %s."
                 % row.get("entity"))
    field_name = row.get("field")
    fdata = entity.get("fields", {}).get(field_name)
    if fdata is None:
        fdata = {}
    _refuse_frozen_ordinal_changes(manifest, plan_fm, row, field_name,
                                   fdata, new_map)


def _stamp_plan_applied(plan_path):
    """Write `applied_at: <utc>` into the applied plan's frontmatter.

    The plan is generated output; stamping it marks the retcon applied so
    the "Open retcons" registers never re-serve it as pending. Fail-open:
    a plan the engine cannot rewrite (deleted, moved) only loses the stamp.
    """
    try:
        text = util.read_file(plan_path)
    except OSError:
        return
    if re.search(r"(?m)^applied_at:", text):
        return
    lines = text.split("\n")
    if not lines or lines[0].strip() != "---":
        return
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            lines.insert(i, "applied_at: %s" % sb.now_iso())
            break
    else:
        return
    util.atomic_write(plan_path, "\n".join(lines))


def _refuse_frozen_ordinal_changes(manifest, plan_fm, row,
                                    field_name, fdata, new_map):
    """Reject a row that changes a frozen book's pinned field value.

    The plan ordinal is not the only ordinal a by-book row can mutate. A
    draft-book plan may mention an earlier published book, so inspect every
    proposed entry before the row is appended to the audit log.
    """
    if plan_fm.get("override_published") is True:
        return
    existing = fdata.get("by-book")
    existing = existing if isinstance(existing, dict) else {}
    fallback = fdata.get("value")
    for ordinal_text, proposed in new_map.items():
        target = sb.book_by_ordinal(manifest, int(ordinal_text))
        if target is None or target.get("status") not in ("published",
                                                             "archived"):
            continue
        current = existing.get(ordinal_text, fallback)
        if current is not None and str(current) != str(proposed):
            util.die("retcon --apply refuses: row for %s would change book "
                     "%d's frozen %s value (%r -> %r); set "
                     "override_published: true only with explicit author "
                     "approval." % (row.get("entity"), target["ordinal"],
                                    field_name, current, proposed))


def _apply_established_before(libroot, bible, row, rid, book, words,
                              next_event_id):
    """Apply a kind: established-before retcon row: mint the next E### event
    into bible.timeline (spec 8.9) and append the audit row."""
    when = (row.get("when") or "").strip()
    if not sb.when_is_iso(when):
        util.die("retcon --apply refuses: established-before row needs an "
                 "ISO-8601 `when` (structured dates only, spec 16-C8), got "
                 "%r." % when)
    summary = (row.get("summary") or "").strip()
    if not summary:
        util.die("retcon --apply refuses: established-before row has an "
                 "empty summary.")
    coord = (row.get("coordinate") or "").strip()
    if not coord:
        util.die("retcon --apply refuses: established-before rows require "
                 "an explicit book-N/chapter-MM coordinate; refusing to "
                 "fabricate chapter-01 provenance.")
    est = coord.replace("/", ":", 1)
    if sb.parse_coordinate(est) is None:
        util.die("retcon --apply refuses: established-before coordinate %r "
                 "is not a book-N/chapter-MM coordinate." % coord)
    events = bible.setdefault("timeline", {}).setdefault("events", [])
    existing_max = max([0] + [int(e["eid"][1:]) for e in events
                               if re.match(r"^E\d+$", str(e.get("eid", "")))])
    eid = "E%03d" % max(next_event_id, existing_max + 1)
    event = {"eid": eid, "when": when,
             "summary": summary, "established-in": est}
    events.append(event)
    sb.append_retcon_row(libroot, {
        "rid": rid,
        "at": sb.now_iso(),
        "author_words": words,
        "kind": "established-before",
        "entity": event["eid"],
        "field": "timeline",
        "from_book": book["ordinal"],
        "old_by_book": {},
        "new_by_book": {},
        "proposed_by": book["ordinal"],
    })
    return event


def _parse_new_by_book(raw):
    if raw is None:
        return None
    raw = raw.strip()
    if not raw:
        return None
    try:
        doc = json.loads(raw)
    except Exception:
        return None
    if not isinstance(doc, dict) or not all(isinstance(k, str) for k in doc):
        return None
    if not doc or not all(k.isdigit() and int(k) >= 1 for k in doc):
        return None
    return {str(k): v for k, v in doc.items()}


def _flush_matching_exemptions(libroot, series_id):
    """Flush exemptions whose underlying canon this retcon changed (the
    author re-decides against the new canon, spec 8.7)."""
    doc = sb.load_series_exemptions(libroot)
    marker = ":%s:" % series_id
    kept = [d for d in doc.get("dismissals", [])
            if marker not in (":" + str(d.get("finding_id", "")) + ":")]
    if len(kept) != len(doc.get("dismissals", [])):
        doc["dismissals"] = kept
        sb.write_series_exemptions(libroot, doc)


# ---------------------------------------------------------------------------
# state (spec 8.8), timeline (8.9), handoff (8.10), dismiss (8.11)
# ---------------------------------------------------------------------------

def cmd_state(args):
    libroot = _require_root(args)
    manifest = _require_manifest(libroot)
    bible = sb.load_bible(libroot)
    book, _ = _require_linked(libroot, manifest, args.book_root)
    if args.card_line:
        sys.stdout.write(sb.card_line(libroot, manifest, bible, book) + "\n")
        return EXIT_OK
    card = sb.build_state_card(libroot, manifest, bible, book)
    sys.stdout.write(sb.state_card_capped(card) + "\n")
    try:
        sys.stdout.flush()
    except Exception:
        pass
    return EXIT_OK


def cmd_timeline(args):
    libroot = _require_root(args)
    _require_manifest(libroot)
    bible = sb.load_bible(libroot)
    events = bible.get("timeline", {}).get("events", [])
    events = sorted(events, key=lambda e: sb.when_sort_key(e.get("when")))
    flagged = 0
    lines = ["# Series timeline", ""]
    for ev in events:
        ok = sb.when_is_iso(ev.get("when"))
        if not ok:
            flagged += 1
        lines.append("%s | %s%s | %s | established-in %s" % (
            ev["eid"], ev.get("when", "?"),
            "" if ok else "  [UNPARSEABLE WHEN]", ev.get("summary", ""),
            ev.get("established-in", "")))
    print("\n".join(lines))
    if flagged:
        sys.stderr.write("library timeline: %d event(s) with unparseable "
                         "`when` (structured ISO-8601 only, spec 16-C8).\n"
                         % flagged)
        return EXIT_FINDINGS
    sys.stderr.write("library timeline: %d event(s).\n" % len(events))
    return EXIT_OK


def cmd_handoff(args):
    libroot = _require_root(args)
    manifest = _require_manifest(libroot)
    bible = sb.load_bible(libroot)
    book, _ = _require_linked(libroot, manifest, args.book_root)
    nxt = max((b["ordinal"] for b in manifest.get("books", [])), default=1) + 1
    os.makedirs(os.path.join(libroot, "handoff"), exist_ok=True)
    path = os.path.join(libroot, "handoff", "handoff-%d.md" % nxt)
    lines = [
        "# Handoff — book %d" % nxt,
        "",
        "Generated by `library handoff` on %s from series canon. Read-only"
        % sb.now_iso(),
        "with respect to the bible.", "",
        "## Frozen canon snapshot (highest ordinal values)", "",
    ]
    for eid, entity in bible.get("entities", {}).items():
        if entity.get("scope") != "shared":
            continue
        parts = []
        for fname, fdata in entity.get("fields", {}).items():
            bb = fdata.get("by-book")
            if isinstance(bb, dict) and bb:
                hi = max(bb, key=lambda k: int(k) if k.isdigit() else -1)
                parts.append("%s = %r (book %s)" % (fname, bb[hi], hi))
            elif "value" in fdata:
                parts.append("%s = %r" % (fname, fdata["value"]))
        if parts:
            lines.append("- %s (%s): %s" % (eid, entity.get("name", "?"),
                                            "; ".join(parts)))
    lines += ["", "## Iron facts", ""]
    iron = sb._iron_rows(bible)
    lines += (["- %s" % r for r in iron] if iron else ["- (none)"])
    lines += ["", "## Do-not-re-explain register", ""]
    rows = sb._do_not_reexplain_rows(bible, nxt)
    lines += (["- %s" % r for _, r in rows] if rows
              else ["- (nothing established before this book)"])
    lines += ["", "## Open retcons", ""]
    open_rows = sb._open_retcon_rows(libroot)
    lines += (["- %s" % r for r in open_rows] if open_rows
              else ["- (no pending retcon plans)"])
    lines += ["", "## Errata posture", ""]
    if os.path.exists(sb.errata_path(libroot)):
        lines.append(util.read_file(sb.errata_path(libroot)).rstrip())
    else:
        lines.append("(no errata recorded)")
    lines += ["", "## One-line fact register", ""]
    for eid, entity in bible.get("entities", {}).items():
        if entity.get("scope") != "shared":
            continue
        est = ", ".join(entity.get("established-in", []) or []) or "?"
        lines.append("- %s — %s — established in %s"
                     % (eid, entity.get("name", "?"), est))
    util.atomic_write(path, "\n".join(lines) + "\n")
    sys.stderr.write("library handoff: wrote %s.\n"
                     % os.path.relpath(path, libroot))
    return EXIT_OK


def cmd_dismiss(args):
    libroot = _require_root(args)
    _require_manifest(libroot)
    reason = (args.reason or "").strip()
    if not reason:
        util.die("dismiss requires the reason in the author's own words "
                 "(--reason); empty reasons are refused (spec 8.11).")
    finding_id = args.finding_id
    if not finding_id.startswith("series:"):
        util.die("dismiss targets series finding ids (series:...); %r is "
                 "not a series finding." % finding_id)
    if finding_id.endswith(":*") and finding_id.count(":*") != 1:
        util.die("dismiss: a wildcard finding id carries exactly one "
                 "trailing ':*' (e.g. series:deceased-as-of-start:"
                 "char:uncle-radu:*); %r is malformed." % finding_id)
    doc = sb.load_series_exemptions(libroot)
    for d in doc["dismissals"]:
        if d.get("finding_id") == finding_id and not d.get("stale"):
            util.die("an active dismissal for %s already exists." % finding_id)
    entry = {
        "finding_id": finding_id,
        "reason_author_words": reason,
        "at": sb.now_iso(),
        "scope": "series",
    }
    # A wildcard is a standing exempt-list entry across the series. It has no
    # single firing book to hash against; retcon --apply flushes matching
    # entity dismissals when canon changes, so leave it unbound rather than
    # binding arbitrarily to the first linked book.
    book_root = args.book_root or None
    if not finding_id.endswith(":*"):
        h = sc._entity_hash_for_finding({"key": finding_id}, libroot,
                                        book_root) if book_root \
            else _hash_from_manifest(libroot, finding_id)
        if h:
            entry["expires_on_entity_hash"] = h
    doc["dismissals"].append(entry)
    release = sb.lock_library(libroot, "dismiss")
    try:
        sb.write_series_exemptions(libroot, doc)
    finally:
        release()
    sys.stderr.write("library dismiss: %s recorded (series scope).\n"
                     % finding_id)
    return EXIT_OK


def _hash_from_manifest(libroot, finding_id):
    manifest = sb.load_manifest(libroot)
    books = sb.linked_books(manifest)
    if not books:
        return None
    # Keys carry the book ordinal the finding fired in. Canonical
    # coordinate-terminated keys end ":N:chapter-MM" (deceased-as-of-start,
    # unlinked-cast); other keys end ":N" (canon-divergence et al.). Parse
    # the ordinal from the correct tail — a naive ":(\d+)$" regex would read
    # the chapter number of a coordinate key as the book ordinal.
    want = _ordinal_from_finding_key(finding_id)
    if want is not None:
        preferred = [b for b in books if b["ordinal"] == want]
        rest = [b for b in books if b["ordinal"] != want]
        books = preferred + rest
    for book in books:
        h = sc._entity_hash_for_finding({"key": finding_id}, libroot,
                                        sb.book_abspath(libroot, book))
        if h:
            return h
    return None


def _ordinal_from_finding_key(finding_id):
    """The book ordinal a finding key carries, or None.

    Coordinate keys end ":<ordinal>:chapter-<NN>"; plain keys end
    ":<ordinal>". A wildcard suffix ":*" carries no ordinal.
    """
    fid = (finding_id or "").strip()
    if fid.endswith(":*"):
        return None
    m = re.search(r":(\d+):chapter-\d+$", fid, re.IGNORECASE)
    if m:
        return int(m.group(1))
    m = re.match(r"^(.*):(\d+)$", fid)
    if m:
        try:
            return int(m.group(2))
        except ValueError:
            return None
    return None


# ---------------------------------------------------------------------------
# Parser + main
# ---------------------------------------------------------------------------

def build_parser():
    p = argparse.ArgumentParser(
        prog="library",
        description="Vellum library / series layer (stdlib Python >= 3.8). "
                    "Exit codes: 0 success, 1 findings/artifact, 2 usage or "
                    "schema error. Every command takes --root <library-root>; "
                    "there is no walk-up discovery.")
    sub = p.add_subparsers(dest="command")

    init = sub.add_parser("init", help="create the empty library tree")
    init.add_argument("root_pos", nargs="?", default=None,
                      help="library root to create (positional form per "
                           "spec 8.1)")
    init.add_argument("--root", default=None,
                      help="library root to create")
    init.add_argument("--title", default=None, help="series title")

    def add_book_cmd(name, help_text):
        c = sub.add_parser(name, help=help_text)
        c.add_argument("--root", default=None, help="library root")
        c.add_argument("book_root", help="book project root")
        return c

    add_book_cmd("link", "link a book to the library").add_argument(
        "--status", default="draft",
        help="initial book status: draft | published | archived")
    add_book_cmd("unlink", "detach a book (canon retained)").add_argument(
        "--keep-sidecar", action="store_true",
        help="leave an empty {} sidecar instead of removing it")
    add_book_cmd("bootstrap", "deterministic canon capture")
    b = [c for c in sub.choices.values() if c.prog.endswith("bootstrap")][0]
    b.add_argument("--plan", action="store_true",
                   help="write reports/bootstrap-plan-<ts>.md")
    b.add_argument("--apply", metavar="PLAN_FILE", default=None,
                   help="apply an approved bootstrap plan")
    add_book_cmd("retcon-check", "run the retcon detection catalog")
    add_book_cmd("retcon-plan", "produce a retcon plan from divergences")
    add_book_cmd("state", "print the series state card").add_argument(
        "--card-line", action="store_true",
        help="one-line summary (session-start hook)")
    add_book_cmd("handoff", "generate the handoff doc for the next book")

    val = sub.add_parser("validate", help="read-only library validation")
    val.add_argument("--root", default=None, help="library root")
    val.add_argument("--fix", action="store_true",
                     help="regenerate stale sidecars, rewrite counters only")
    val.add_argument("book_roots", nargs="*",
                     help="optional extra book roots to probe for orphan "
                          "sidecars")

    tl = sub.add_parser("timeline", help="E### events table (ISO `when`)")
    tl.add_argument("--root", default=None, help="library root")

    ret = sub.add_parser("retcon", help="apply an approved retcon plan")
    ret.add_argument("--root", default=None, help="library root")
    ret.add_argument("--apply", required=True, metavar="PLAN_FILE",
                     help="the approved plan file")

    dis = sub.add_parser("dismiss", help="record a series-scope dismissal")
    dis.add_argument("--root", default=None, help="library root")
    dis.add_argument("finding_id", help="the exact finding id (series:...)")
    dis.add_argument("--reason", required=True,
                     help="the author's words, verbatim")
    dis.add_argument("--book-root", default=None,
                     help="book root for the entity hash binding")
    return p


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    if not getattr(args, "command", None):
        parser.print_help()
        return EXIT_ERROR
    try:
        return {
            "init": cmd_init,
            "link": cmd_link,
            "unlink": cmd_unlink,
            "validate": cmd_validate,
            "bootstrap": cmd_bootstrap,
            "retcon-check": cmd_retcon_check,
            "retcon-plan": cmd_retcon_plan,
            "retcon": cmd_retcon_apply,
            "state": cmd_state,
            "timeline": cmd_timeline,
            "handoff": cmd_handoff,
            "dismiss": cmd_dismiss,
        }[args.command](args)
    except LockError as e:
        sys.stderr.write("library: %s\n" % e)
        return EXIT_ERROR
    except FmError as e:
        sys.stderr.write("library: %s\n" % e)
        return EXIT_ERROR
