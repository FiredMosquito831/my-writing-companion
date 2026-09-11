# Vellum series layer — library manifest, series bible, retcon log (library-spec.md 4, 5, 6, 11).
# Original code. Python >= 3.8, stdlib only, zero pip dependencies.
"""Series-bible dialect, separate from v0.1.1 bible.py (spec 16-L18): manifest
and bible load/validate with strict unknown-key rejection (exit 2), by-book
effective-at-N resolution (spec 11), the coordinate convention (spec 4.2),
the library lock (spec 8.0), and the series state card (spec 8.8).

All machine state is JSON. Markdown is only ever generated human-facing
output, never parseable state.
"""
import hashlib
import json
import os
import re
import sys
import time
import uuid as uuid_mod
from datetime import datetime, timezone

from . import util
from .util import EXIT_OK, EXIT_FINDINGS, EXIT_ERROR, make_finding, die

SCHEMA_VERSION = 1
BOOK_STATUSES = ("draft", "published", "archived")
ENTITY_TYPES = ("character", "prop", "promise", "question", "knowledge")
STATE_CARD_MAX_BYTES = 12 * 1024  # hard cap (spec 8.8)

MANIFEST_KEYS = {"kind", "schema_version", "series", "books",
                 "engine_min_version_global"}
MANIFEST_SERIES_KEYS = {"title", "created", "next_event_id", "next_retcon_id"}
BOOK_KEYS = {"book_uuid", "title", "path", "ordinal", "status", "linked_at",
             "unlinked_at", "engine_min_version", "kb_entity_count",
             "story_hash_at_link"}
BOOK_REQUIRED = {"book_uuid", "title", "path", "ordinal", "status",
                 "linked_at"}

BIBLE_KEYS = {"series_id", "schema_version", "entities", "timeline"}
ENTITY_KEYS = {"type", "series_id", "name", "aliases", "fields",
               "established-in", "scope", "entity_hash", "last_touched"}
ENTITY_REQUIRED = {"type", "series_id", "name", "fields", "established-in",
                   "scope"}
FIELD_KEYS = {"value", "by-book", "iron"}
EVENT_KEYS = {"eid", "when", "summary", "established-in"}

RETCON_KINDS = ("fact-change", "reanimation", "scope-change",
                "established-before", "errata")
RETCON_ROW_KEYS = {"rid", "at", "author_words", "kind", "entity", "field",
                   "from_book", "old_by_book", "new_by_book", "proposed_by"}
RETCON_ROW_REQUIRED = {"rid", "at", "author_words", "kind", "entity",
                       "field", "from_book", "proposed_by"}

# Coordinate convention (spec 4.2): bible internals use "1:chapter-03"
# (short form); markdown reports use "1/chapter-03" (slash form). Both
# parse to the same key. A bare "chapter-NN" in a series file is itself a
# finding (series:unqualified-ref).
_SHORT_COORD_RE = re.compile(r"^(\d+):chapter-0*(\d+)$", re.IGNORECASE)
_SLASH_COORD_RE = re.compile(r"^(\d+)/chapter-0*(\d+)$", re.IGNORECASE)
_BARE_COORD_RE = re.compile(r"^chapter-0*(\d+)$", re.IGNORECASE)
# Bare chapter reference inside prose/markdown where a qualified coordinate
# is expected (not preceded by a book prefix, ordinal:, slash, or word char).
_UNQUALIFIED_REF_RE = re.compile(
    r"(?<![\w/:.\-])chapter-\d+(?![\w-])", re.IGNORECASE)
_EID_RE = re.compile(r"^E\d{3,}$")
_RID_RE = re.compile(r"^R(\d+)$")
_ISO_WHEN_RE = re.compile(
    r"^\d{4}(-\d{2}(-\d{2})?)?([T ]\d{2}:\d{2}(:\d{2})?Z?)?$")


def now_iso():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

def manifest_path(libroot):
    return os.path.join(libroot, "library.json")


def bible_path(libroot):
    return os.path.join(libroot, "series", "bible.json")


def retcons_path(libroot):
    return os.path.join(libroot, "series", "retcons.jsonl")


def exemptions_path(libroot):
    return os.path.join(libroot, "series", "exemptions.json")


def errata_path(libroot):
    return os.path.join(libroot, "series", "errata.md")


def sidecar_path(book_root):
    return os.path.join(book_root, ".vellum", "series-link.json")


def book_abspath(libroot, book):
    """Resolve a manifest book path (relative, forward slashes) to absolute."""
    return os.path.normpath(os.path.join(libroot, book["path"].replace("\\", "/")))


def chapter_file(book_root, num):
    """Path of manuscript/chapters/chapter-NN.md in a book, or None."""
    for pad in ("%02d", "%03d", "%d"):
        p = os.path.join(book_root, "manuscript", "chapters",
                         ("chapter-%s.md" % pad) % num)
        if os.path.exists(p):
            return p
    return None


# ---------------------------------------------------------------------------
# Coordinates (spec 4.2)
# ---------------------------------------------------------------------------

def parse_coordinate(coord):
    """Parse "1:chapter-03" or "1/chapter-03" -> (ordinal, chapter) | None."""
    if not isinstance(coord, str):
        return None
    m = _SHORT_COORD_RE.match(coord.strip())
    if m:
        return int(m.group(1)), int(m.group(2))
    m = _SLASH_COORD_RE.match(coord.strip())
    if m:
        return int(m.group(1)), int(m.group(2))
    return None


def coord_short(ordinal, chapter):
    return "%d:chapter-%02d" % (ordinal, chapter)


def coord_slash(ordinal, chapter):
    return "%d/chapter-%02d" % (ordinal, chapter)


def is_bare_coordinate(coord):
    return isinstance(coord, str) and bool(_BARE_COORD_RE.match(coord.strip()))


def find_unqualified_refs(text):
    """Bare chapter-NN occurrences in markdown where a qualified coordinate
    is expected (series files / retcon plans, spec 10 #5)."""
    out = []
    for m in _UNQUALIFIED_REF_RE.finditer(text):
        out.append(m.group(0).lower())
    return out


# ---------------------------------------------------------------------------
# Manifest — library.json (spec 2)
# ---------------------------------------------------------------------------

def validate_manifest(doc, path="library.json"):
    if not isinstance(doc, dict):
        die("%s is not a JSON object." % path)
    if doc.get("kind") != "vellum-library":
        die("%s: kind %r is not \"vellum-library\" (not a vellum library "
            "manifest)." % (path, doc.get("kind")))
    if doc.get("schema_version") != SCHEMA_VERSION:
        die("%s: unknown schema_version %r (this engine knows schema "
            "version %d)." % (path, doc.get("schema_version"),
                              SCHEMA_VERSION))
    unknown = set(doc.keys()) - MANIFEST_KEYS
    if unknown:
        die("%s: unknown keys: %s." % (path, ", ".join(sorted(unknown))))
    series = doc.get("series")
    if not isinstance(series, dict):
        die("%s: series is not an object." % path)
    unk = set(series.keys()) - MANIFEST_SERIES_KEYS
    if unk:
        die("%s: series has unknown keys: %s." % (path, ", ".join(sorted(unk))))
    for k in ("title", "created", "next_event_id", "next_retcon_id"):
        if k not in series:
            die("%s: series is missing %r." % (path, k))
    for k in ("next_event_id", "next_retcon_id"):
        if not isinstance(series[k], int) or series[k] < 1:
            die("%s: series.%s must be a positive integer." % (path, k))
    books = doc.get("books")
    if not isinstance(books, list):
        die("%s: books is not a list." % path)
    for i, book in enumerate(books):
        _validate_book(book, "%s: books[%d]" % (path, i))
    if "engine_min_version_global" not in doc:
        die("%s: engine_min_version_global missing." % path)
    return doc


def _validate_book(book, where):
    if not isinstance(book, dict):
        die("%s is not an object." % where)
    unknown = set(book.keys()) - BOOK_KEYS
    if unknown:
        die("%s has unknown keys: %s." % (where, ", ".join(sorted(unknown))))
    for k in BOOK_REQUIRED:
        if k not in book:
            die("%s is missing %r." % (where, k))
    if not isinstance(book["ordinal"], int):
        die("%s: ordinal must be an integer." % where)
    if book["status"] not in BOOK_STATUSES:
        die("%s: status %r not in %s." % (where, book["status"],
                                          list(BOOK_STATUSES)))
    p = book["path"]
    if not isinstance(p, str) or not p:
        die("%s: path must be a non-empty string." % where)
    if "\\" in p:
        die("%s: path must use forward slashes." % where)


def load_manifest(libroot):
    p = manifest_path(libroot)
    if not os.path.exists(p):
        die("library.json not found under %s (pass --root <library-root>; "
            "there is no walk-up discovery)." % libroot)
    try:
        with open(p, "r", encoding="utf-8-sig") as f:
            doc = json.load(f)
    except Exception as e:
        die("library.json is unreadable: %s" % e)
    return validate_manifest(doc, "library.json")


def write_manifest(libroot, manifest):
    manifest["schema_version"] = SCHEMA_VERSION
    util.atomic_write(manifest_path(libroot),
                      json.dumps(manifest, indent=2, ensure_ascii=False) + "\n")


# ---------------------------------------------------------------------------
# Series bible — series/bible.json (spec 4)
# ---------------------------------------------------------------------------

def validate_bible(doc, path="series/bible.json"):
    if not isinstance(doc, dict):
        die("%s is not a JSON object." % path)
    if doc.get("schema_version") != SCHEMA_VERSION:
        die("%s: unknown schema_version %r." % (path, doc.get("schema_version")))
    unknown = set(doc.keys()) - BIBLE_KEYS
    if unknown:
        die("%s: unknown keys: %s." % (path, ", ".join(sorted(unknown))))
    for k in ("series_id", "entities", "timeline"):
        if k not in doc:
            die("%s: missing %r." % (path, k))
    if not isinstance(doc["entities"], dict):
        die("%s: entities is not an object." % path)
    for eid, entity in doc["entities"].items():
        if not isinstance(eid, str) or not eid:
            die("%s: entity keys must be non-empty strings." % path)
        if not isinstance(entity, dict):
            die("%s: entities[%s] is not an object." % (path, eid))
        if entity.get("series_id") != eid:
            die("%s: entities[%s].series_id %r does not match its key."
                % (path, eid, entity.get("series_id")))
        _validate_entity(entity, "%s: entities[%s]" % (path, eid))
    tl = doc.get("timeline")
    if not isinstance(tl, dict) or not isinstance(tl.get("events"), list):
        die("%s: timeline.events is not a list." % path)
    for i, ev in enumerate(tl["events"]):
        _validate_event(ev, "%s: timeline.events[%d]" % (path, i))
    return doc


def _validate_entity(entity, where):
    if not isinstance(entity, dict):
        die("%s is not an object." % where)
    unknown = set(entity.keys()) - ENTITY_KEYS
    if unknown:
        die("%s has unknown keys: %s." % (where, ", ".join(sorted(unknown))))
    for k in ENTITY_REQUIRED:
        if k not in entity:
            die("%s is missing %r." % (where, k))
    if entity["type"] not in ENTITY_TYPES:
        die("%s: type %r not in %s." % (where, entity["type"],
                                        list(ENTITY_TYPES)))
    if entity["scope"] not in ("shared", "local"):
        die("%s: scope %r not in (shared, local)." % (where, entity["scope"]))
    if not isinstance(entity["fields"], dict):
        die("%s: fields is not an object." % where)
    for fname, fdata in entity["fields"].items():
        _validate_field(fdata, "%s: fields[%s]" % (where, fname))
    est = entity["established-in"]
    if not isinstance(est, list) or not all(isinstance(x, str) for x in est):
        die("%s: established-in must be a list of coordinate strings." % where)


def _validate_field(fdata, where):
    if not isinstance(fdata, dict):
        die("%s is not an object." % where)
    unknown = set(fdata.keys()) - FIELD_KEYS
    if unknown:
        die("%s has unknown keys: %s." % (where, ", ".join(sorted(unknown))))
    has_value = "value" in fdata
    has_by_book = "by-book" in fdata
    if has_value and has_by_book:
        die("%s has both value and by-book (spec 4.1: one encoding per "
            "field, never both)." % where)
    if not has_value and not has_by_book:
        die("%s has neither value nor by-book." % where)
    if has_by_book:
        bb = fdata["by-book"]
        if (not isinstance(bb, dict)
                or not all(isinstance(k, str) and k.isdigit() and int(k) >= 1
                           for k in bb)):
            die("%s: by-book must be an object keyed by positive ordinal "
                "strings." % where)
    if "iron" in fdata and not isinstance(fdata["iron"], list):        die("%s: iron must be a list of literal strings." % where)


def _validate_event(ev, where):
    if not isinstance(ev, dict):
        die("%s is not an object." % where)
    unknown = set(ev.keys()) - EVENT_KEYS
    if unknown:
        die("%s has unknown keys: %s." % (where, ", ".join(sorted(unknown))))
    for k in EVENT_KEYS:
        if k not in ev:
            die("%s is missing %r." % (where, k))
    if not _EID_RE.match(str(ev.get("eid", ""))):
        die("%s: eid %r is not in E### form." % (where, ev.get("eid")))


def load_bible(libroot):
    p = bible_path(libroot)
    if not os.path.exists(p):
        die("series/bible.json not found under %s (run 'library init')."
            % libroot)
    try:
        with open(p, "r", encoding="utf-8-sig") as f:
            doc = json.load(f)
    except Exception as e:
        die("series/bible.json is unreadable: %s" % e)
    return validate_bible(doc, "series/bible.json")


def write_bible(libroot, bible):
    bible["schema_version"] = SCHEMA_VERSION
    util.atomic_write(bible_path(libroot),
                      json.dumps(bible, indent=2, ensure_ascii=False) + "\n")


# ---------------------------------------------------------------------------
# Retcon log — series/retcons.jsonl (spec 5). Append-only audit trail.
# ---------------------------------------------------------------------------

def load_retcons(libroot):
    p = retcons_path(libroot)
    rows = []
    if not os.path.exists(p):
        return rows
    with open(p, "r", encoding="utf-8-sig") as f:
        for ln, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                row = json.loads(line)
            except Exception as e:
                die("series/retcons.jsonl line %d is unparseable: %s"
                    % (ln, e))
            if not isinstance(row, dict):
                die("series/retcons.jsonl line %d is not a JSON object." % ln)
            missing = RETCON_ROW_REQUIRED - set(row.keys())
            if missing:
                die("series/retcons.jsonl line %d is missing keys: %s"
                    % (ln, ", ".join(sorted(missing))))
            if row.get("kind") not in RETCON_KINDS:
                die("series/retcons.jsonl line %d: kind %r not in %s."
                    % (ln, row.get("kind"), list(RETCON_KINDS)))
            rows.append(row)
    return rows


def append_retcon_row(libroot, row):
    """Append one JSONL row (audit trail). Never rewrites the log."""
    p = retcons_path(libroot)
    d = os.path.dirname(p)
    if d and not os.path.isdir(d):
        os.makedirs(d, exist_ok=True)
    with open(p, "a", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")


# ---------------------------------------------------------------------------
# Series exemptions — series/exemptions.json (spec 6)
# ---------------------------------------------------------------------------

def load_series_exemptions(libroot):
    p = exemptions_path(libroot)
    if not os.path.exists(p):
        return {"dismissals": []}
    try:
        with open(p, "r", encoding="utf-8-sig") as f:
            doc = json.load(f)
    except Exception:
        return {"dismissals": []}
    if not isinstance(doc.get("dismissals"), list):
        doc["dismissals"] = []
    return doc


def write_series_exemptions(libroot, doc):
    util.atomic_write(exemptions_path(libroot),
                      json.dumps(doc, indent=2, ensure_ascii=False) + "\n")


def active_dismissals(libroot):
    return [d for d in load_series_exemptions(libroot)["dismissals"]
            if d.get("finding_id") and not d.get("stale")]


# ---------------------------------------------------------------------------
# By-book resolution (spec 11) — the map is the truth, never a log walk
# ---------------------------------------------------------------------------

def effective_at(bible, entity_id, field_name, ordinal):
    """Effective value of a by-book field at book ordinal N.

    value = bible.entities[<id>].fields[<field>].by-book.get(str(N),
            bible.entities[<id>].fields[<field>].value)
    """
    entity = bible.get("entities", {}).get(entity_id)
    if entity is None:
        return None
    field = entity.get("fields", {}).get(field_name)
    if field is None:
        return None
    by_book = field.get("by-book")
    if isinstance(by_book, dict):
        return by_book.get(str(ordinal), field.get("value"))
    return field.get("value")


def book_by_ordinal(manifest, ordinal):
    for book in manifest.get("books", []):
        if book.get("ordinal") == ordinal:
            return book
    return None


def book_by_uuid(manifest, book_uuid):
    """Books are matched by book_uuid, never by realpath (spec 2)."""
    for book in manifest.get("books", []):
        if book.get("book_uuid") == book_uuid:
            return book
    return None


def book_by_path(manifest, libroot, book_root):
    """Match a book root against the manifest, preferring linked entries.

    Path comparison is normalized for Windows' case-insensitive filesystem.
    A detached entry remains available as a fallback so ``link`` can revive
    it, but a live entry always wins when both records share a path.
    """
    want = os.path.normcase(os.path.normpath(os.path.abspath(book_root)))
    detached = None
    for book in manifest.get("books", []):
        candidate = os.path.normcase(os.path.normpath(
            os.path.abspath(book_abspath(libroot, book))))
        if candidate != want:
            continue
        if book.get("unlinked_at") is None:
            return book
        if detached is None:
            detached = book
    return detached


def linked_books(manifest):
    """Books still probed (unlinked_at is null), in ordinal order."""
    return sorted((b for b in manifest.get("books", [])
                   if b.get("unlinked_at") is None),
                  key=lambda b: b["ordinal"])


# ---------------------------------------------------------------------------
# Entity matching helpers (bootstrap tiers, spec 8.5)
# ---------------------------------------------------------------------------

def _norm_name(name):
    return str(name or "").strip().casefold()


def find_entity_by_exact_name(bible, name):
    for eid, entity in bible.get("entities", {}).items():
        if _norm_name(entity.get("name")) == _norm_name(name):
            return eid
    return None


def find_entity_by_alias(bible, alias):
    """Whole-string alias match (casefold, trimmed) — never substring."""
    for eid, entity in bible.get("entities", {}).items():
        for a in entity.get("aliases", []) or []:
            if _norm_name(a) == _norm_name(alias):
                return eid
    return None


def entity_hash_of_file(path):
    with open(path, "rb") as f:
        return "sha256:" + hashlib.sha256(f.read()).hexdigest()


# ---------------------------------------------------------------------------
# Library lock (spec 8.0) — library-root/.lock, PID + subcommand
# ---------------------------------------------------------------------------

_LIB_LOCK_STALE_SECONDS = 120


def lock_library(libroot, command="write"):
    """Exclusive advisory lock before any write. Contention timeout (30 s,
    override with VELLUM_LIB_LOCK_TIMEOUT for tests) -> LockError (exit 2).
    Reads never lock."""
    timeout = float(os.environ.get("VELLUM_LIB_LOCK_TIMEOUT", "30"))
    lock_path = os.path.join(libroot, ".lock")
    deadline = time.time() + timeout
    while True:
        try:
            fd = os.open(lock_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            os.write(fd, ("%d %s" % (os.getpid(), command)).encode("ascii"))
            os.close(fd)
            break
        except FileExistsError:
            try:
                age = time.time() - os.path.getmtime(lock_path)
            except OSError:
                age = 0
            if age > _LIB_LOCK_STALE_SECONDS:
                sys.stderr.write("library: stale lock removed (held %.0fs).\n"
                                 % age)
                try:
                    os.unlink(lock_path)
                except OSError:
                    pass
                continue
            if time.time() >= deadline:
                raise util.LockError(
                    "library is locked by another process (%s); wait for it "
                    "to finish or remove the stale lock file."
                    % os.path.join(libroot, ".lock"))
            time.sleep(0.05)

    def release():
        try:
            os.unlink(lock_path)
        except OSError:
            pass

    return release


# ---------------------------------------------------------------------------
# Sidecar (spec 3)
# ---------------------------------------------------------------------------

def read_sidecar(book_root):
    """Read the sidecar with a distinguishable failure.

    Returns (sidecar, error): sidecar is None when the file is absent and a
    dict otherwise; error is None for an absent or successfully parsed file
    and the exception text when the file exists but does not parse. BOM
    tolerance (utf-8-sig) removes the most common "unreadable" trigger;
    genuinely malformed JSON stays distinguishable from an empty sidecar so
    validate can say "unreadable" instead of misdiagnosing "stale" (spec 3).
    """
    p = sidecar_path(book_root)
    if not os.path.exists(p):
        return None, None
    try:
        with open(p, "r", encoding="utf-8-sig") as f:
            return json.load(f), None
    except Exception as e:
        return {}, "%s" % e


def load_sidecar(book_root):
    """Fail-open form used by repair and hook paths: None when absent, {}
    when unreadable (a stale-looking but repairable sidecar)."""
    doc, _err = read_sidecar(book_root)
    return doc


def write_sidecar(book_root, doc):
    util.atomic_write(sidecar_path(book_root),
                      json.dumps(doc, indent=2, ensure_ascii=False) + "\n")


# ---------------------------------------------------------------------------
# Series state card (spec 8.8) — fixed sections, 12 KB hard cap
# ---------------------------------------------------------------------------

def _do_not_reexplain_rows(bible, current_ordinal):
    """One line per scope:shared fact established in an earlier book.

    Every established-in coordinate older than the current book is its own
    register line (spec 8.8 section 2: one line per shared fact) — a shared
    entity whose facts were established across several books yields one line
    per coordinate, never only the first."""
    rows = []
    for eid, entity in bible.get("entities", {}).items():
        if entity.get("scope") != "shared":
            continue
        label = entity.get("name", eid)
        for coord in entity.get("established-in", []):
            parsed = parse_coordinate(coord)
            if parsed and parsed[0] < current_ordinal:
                rows.append((parsed[0], "%s — established in %s"
                             % (label, coord_slash(*parsed))))
    rows.sort()
    return rows


def _iron_rows(bible):
    rows = []
    for eid, entity in bible.get("entities", {}).items():
        for fname, fdata in entity.get("fields", {}).items():
            iron = fdata.get("iron")
            if iron:
                rows.append("%s.%s: %s" % (eid, fname, "; ".join(
                    str(x) for x in iron)))
    return rows


def build_state_card(libroot, manifest, bible, book):
    """Fixed-section series state card for one linked book (spec 8.8)."""
    ordinal = book["ordinal"]
    L = []
    L.append("## Series state")
    L.append("")
    # 1. Series title + linked books and statuses
    L.append("Series: %s (engine dialect v%d). Linked books:"
             % (manifest["series"].get("title", "?"), SCHEMA_VERSION))
    for b in linked_books(manifest):
        marker = " <- this book" if b["ordinal"] == ordinal else ""
        L.append("- book %d — %s (%s)%s" % (b["ordinal"], b["title"],
                                            b["status"], marker))
    # 2. Do-not-re-explain register
    L.append("")
    L.append("Established before this book — do not re-explain:")
    rows = _do_not_reexplain_rows(bible, ordinal)
    if rows:
        for _, row in rows:
            L.append("- %s" % row)
    else:
        L.append("- (nothing established before this book)")
    # 3. Open retcons (pending plans, not yet applied)
    L.append("")
    L.append("Open retcons:")
    open_rows = _open_retcon_rows(libroot)
    if open_rows:
        for row in open_rows:
            L.append("- %s" % row)
    else:
        L.append("- (no pending retcon plans)")
    # 4. Iron facts
    L.append("")
    L.append("Iron facts:")
    iron = _iron_rows(bible)
    if iron:
        for row in iron:
            L.append("- %s" % row)
    else:
        L.append("- (none)")
    # 5. Last 5 retcon ids
    L.append("")
    L.append("Recent retcons:")
    recent = load_retcons(libroot)[-5:]
    if recent:
        for row in recent:
            L.append("- %s [%s] %s — %s" % (
                row["rid"], row.get("kind", "?"), row.get("entity", "?"),
                str(row.get("author_words", ""))[:80]))
    else:
        L.append("- (retcon log empty)")
    L.append("")
    return "\n".join(L)


def _open_retcon_rows(libroot):
    rows = []
    reports = os.path.join(libroot, "reports")
    plans = []
    if os.path.isdir(reports):
        for name in sorted(os.listdir(reports)):
            if name.startswith("retcon-plan-") and name.endswith(".md"):
                plans.append(os.path.join(reports, name))
    for p in plans[-3:]:
        try:
            text = util.read_file(p)
        except OSError:
            continue
        fm, _ = util.strip_frontmatter_text(text)
        # An applied plan is historical, not an open retcon.  The apply
        # command stamps its plan after every row has committed, so a state
        # card never re-serves stale "pending apply" context.
        if fm.get("applied_at"):
            continue
        state = ("approved, pending apply"
                 if fm.get("approved") is True else "awaiting author approval")
        n = text.count("- entity:")
        rows.append("%s — %d row(s), %s" % (os.path.basename(p), n, state))
    return rows


_TRUNCATION_MARKER = ("[series section truncated at the {max_bytes}-byte "
                      "injection budget — run 'library state' for the full "
                      "card or prune series canon.]")


def state_card_capped(card):
    if len(card.encode("utf-8")) <= STATE_CARD_MAX_BYTES:
        return card
    return state_card_capped_with_budget(card, STATE_CARD_MAX_BYTES)


def state_card_capped_with_budget(card, max_bytes):
    """Truncate a card without allowing its marker to exceed max_bytes.

    The truncation marker is part of the output budget.  This matters when a
    series section is injected into an already-full v0.1.1 state card: a
    marker that is larger than the remaining budget must not turn a valid
    card into an over-cap frozen card.
    """
    if len(card.encode("utf-8")) <= max_bytes:
        return card
    marker = _TRUNCATION_MARKER.format(max_bytes=max_bytes)
    marker_bytes = len(marker.encode("utf-8"))
    limit = max_bytes - marker_bytes
    if limit <= 0:
        return ""
    keep = []
    size = 0
    for line in card.split("\n"):
        b = len((line + "\n").encode("utf-8"))
        if size + b > limit:
            break
        keep.append(line)
        size += b
    if not keep:
        return ""
    keep.append(marker)
    return "\n".join(keep)


def card_line(libroot, manifest, bible, book):
    """One-line summary for the session-start hook (fail-open caller)."""
    books = linked_books(manifest)
    summary = ", ".join("%d %s" % (b["ordinal"], b["status"])
                        for b in books)
    n_retcons = len(load_retcons(libroot))
    return ("series %s — this book: ordinal %d (%s) — books: %s — "
            "retcons: %d" % (manifest["series"].get("title", "?"),
                             book["ordinal"], book["status"], summary,
                             n_retcons))


def state_card_section(book_root):
    """Section appended to the v0.1.1 `vellum state` card when the book is
    linked (spec 8.8/13.5). Fail-open: any error -> None (byte-identical
    v0.1.1 output for unlinked books and unreachable libraries)."""
    try:
        sidecar = load_sidecar(book_root)
        if not sidecar or not sidecar.get("series_root"):
            return None
        libroot = os.path.normpath(os.path.join(
            os.path.abspath(book_root), sidecar["series_root"]))
        if not os.path.isdir(libroot):
            return None
        manifest = load_manifest(libroot)
        bible = load_bible(libroot)
        book = book_by_uuid(manifest, sidecar.get("book_uuid"))
        if book is None or book.get("unlinked_at") is not None:
            return None
        return build_state_card(libroot, manifest, bible, book)
    except SystemExit:
        return None
    except Exception:
        return None


# ---------------------------------------------------------------------------
# Timeline (spec 8.9) — structured ISO-8601 `when`, never prose-parsed
# ---------------------------------------------------------------------------

def when_sort_key(when):
    """Sortable key for an ISO-8601 `when`; unparseable values sort last."""
    if isinstance(when, str) and _ISO_WHEN_RE.match(when.strip()):
        return (0, when.strip())
    return (1, str(when))


def when_is_iso(when):
    return isinstance(when, str) and bool(_ISO_WHEN_RE.match(when.strip()))
