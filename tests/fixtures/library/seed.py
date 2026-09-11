"""Two-book series-library fixture for library engine tests.

The fixture deliberately includes one example of each high-value series check:
book 1 is published, book 2 is draft, and both point at one bible outside the
book roots.  ``seed(destination)`` creates ``destination/library`` plus the
sibling book roots ``destination/book-1`` and ``destination/book-2``.
"""
import hashlib
import json
import re
from pathlib import Path


BOOK1_UUID = "3f2c9a1e-1111-4aaa-9bbb-000000000001"
BOOK2_UUID = "3f2c9a1e-2222-4aaa-9bbb-000000000002"


def _write(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


def _chapter(number, cast, mentions=(), title="Scene"):
    chars = ", ".join(cast)
    refs = ", ".join(mentions)
    body = "Lena traversează sala și observă lumina de pe ziduri. " \
           "Apoi notează totul în caiet și închide ușa.\n"
    return (
        "---\n"
        "title: %r\n"
        "number: %d\n"
        "status: final\n"
        "pov: character-lena\n"
        "characters: [%s]\n"
        "mentions: [%s]\n"
        "promises-advanced: []\n"
        "word-target: 3200\n"
        "word-count: null\n"
        "---\n\n%s" % (title, number, chars, refs, body)
    )


def _story(title):
    return "---\ntitle: %s\npremise: A series test book.\n---\n\n" % title


def _char(eid, name, status="alive", series_id=None, aliases=None,
          extra=""):
    lines = ["---", "id: %s" % eid, "type: character", "name: %s" % name,
             "status: %s" % status, "died-in: null",
             "aliases: [%s]" % ", ".join(aliases or []),
             "pov-eligible: true"]
    if series_id:
        lines.append("series-id: %s" % series_id)
    if extra:
        lines.append(extra.rstrip("\n"))
    lines += ["---", "\n", "%s stă în prag și privește încăperea.\n" % name]
    return "\n".join(lines)


def _prop(eid, title, location, series_id=None):
    lines = ["---", "id: %s" % eid, "type: prop", "title: %s" % title,
             "introduced-in: chapter-01", "custody:",
             "  owner: character-lena", "  location: %s" % location,
             "  status: in-play", "history:", "  - chapter: chapter-01",
             "    note: introduced"]
    if series_id:
        lines.append("series-id: %s" % series_id)
    lines += ["---", "\n", "Obiectul rămâne pe masă.\n"]
    return "\n".join(lines)


def _promise(eid, title, status, series_id=None):
    lines = ["---", "id: %s" % eid, "type: promise", "title: %s" % title,
             "status: %s" % status, "planted-in: chapter-01",
             "reinforced: []", "payoff-in: null", "target-by: null",
             "abandoned-reason: null"]
    if series_id:
        lines.append("series-id: %s" % series_id)
    lines += ["---", "\n", "Promisiunea rămâne în aer.\n"]
    return "\n".join(lines)


def _knowledge(eid, title, audience, series_id=None, holders="[]"):
    lines = ["---", "id: %s" % eid, "type: knowledge", "title: %s" % title,
             "statement: %s" % title, "holders: %s" % holders,
             "audience-learned-in: %s" % audience, "superseded-by: null"]
    if series_id:
        lines.append("series-id: %s" % series_id)
    lines += ["---", "\n", "Faptul este folosit în scenă.\n"]
    return "\n".join(lines)


def _book1(root):
    _write(root / "kb" / "story.md", _story("Volumul I"))
    _write(root / "kb" / "characters" / "character-lena.md",
           _char("character-lena", "Lena Popescu", series_id="char:lena-popescu",
                  aliases=["Lena"]))
    _write(root / "kb" / "characters" / "character-uncle-radu.md",
           _char("character-uncle-radu", "Uncle Radu", status="deceased",
                  series_id="char:uncle-radu", aliases=["Radu"]))
    # Deliberate published-book divergence: canon says Lena's desk.
    _write(root / "kb" / "props" / "prop-brass-key.md",
           _prop("prop-brass-key", "Brass key to the east wing", "library shelf",
                 "prop:brass-key"))
    _write(root / "kb" / "promises" / "promise-vault.md",
           _promise("promise-vault", "The vault promise", "planted",
                    "promise:the-vault-promise"))
    _write(root / "kb" / "knowledge" / "knowledge-academy.md",
           _knowledge("knowledge-academy", "The academy was founded in 1847",
                       "chapter-01", "knowledge:academy-founded"))
    _write(root / "manuscript" / "chapters" / "chapter-01.md",
           _chapter(1, ["character-lena"], title="Arrival"))
    _write(root / "manuscript" / "chapters" / "chapter-02.md",
           _chapter(2, ["character-lena", "character-uncle-radu"],
                    title="The key"))


def _book2(root):
    _write(root / "kb" / "story.md", _story("Volumul II"))
    _write(root / "kb" / "characters" / "character-lena.md",
           _char("character-lena", "Lena Popescu", status="grieving",
                  series_id="char:lena-popescu", aliases=["Lena"],
                  extra="role: graduate\n"))
    # Alias join with a different local id: advisory id-mismatch.
    _write(root / "kb" / "characters" / "character-radu.md",
           _char("character-radu", "Radu", status="deceased",
                  series_id="char:uncle-radu", aliases=["Radu"]))
    # Same-name shared entity but no series-id: judgment-routed unlinked cast.
    _write(root / "kb" / "characters" / "character-maria.md",
           _char("character-maria", "Maria Popescu"))
    _write(root / "kb" / "characters" / "character-vegg.md",
           _char("character-vegg", "Vegg the Ferryman"))
    _write(root / "kb" / "props" / "prop-brass-key.md",
           _prop("prop-brass-key", "Brass key to the east wing", "vault",
                 "prop:brass-key"))
    _write(root / "kb" / "promises" / "promise-vault.md",
           _promise("promise-vault", "The vault promise", "open",
                    "promise:the-vault-promise"))
    _write(root / "kb" / "promises" / "promise-bursary.md",
           _promise("promise-bursary", "The bursary promise", "paid-off"))
    # The fact is used in book 2 but claimed learned in book 3: a real
    # cross-book knowledge anachronism (the engine flags later, not earlier,
    # learned-in coordinates).
    _write(root / "kb" / "knowledge" / "knowledge-academy.md",
           _knowledge("knowledge-academy", "The academy was founded in 1847",
                       "3:chapter-01", "knowledge:academy-founded"))
    # Bare chapter-NN is current-book-local and is not a cross-book ref.
    _write(root / "kb" / "knowledge" / "knowledge-city-map.md",
           _knowledge("knowledge-city-map", "The city map is blue",
                       "chapter-03"))
    _write(root / "manuscript" / "chapters" / "chapter-01.md",
           _chapter(1, ["character-lena", "character-radu"], title="Return"))
    _write(root / "manuscript" / "chapters" / "chapter-02.md",
           _chapter(2, ["character-lena", "character-maria"],
                    mentions=["character-radu"], title="The guest"))
    # A deliberately old in-project copy for the version-lag advisory.
    _write(root / "scripts" / "vellum_lib" / "__init__.py",
           '__version__ = "0.1.0"\n')


def _entity(sid, typ, name, fields, established, aliases=None,
            last_touched="bootstrap"):
    return {
        "type": typ,
        "series_id": sid,
        "name": name,
        "aliases": aliases or [],
        "fields": fields,
        "established-in": established,
        "scope": "shared",
        "last_touched": last_touched,
    }


def seed(destination):
    destination = Path(destination)
    destination.mkdir(parents=True, exist_ok=True)
    library = destination / "library"
    book1 = destination / "book-1"
    book2 = destination / "book-2"
    _book1(book1)
    _book2(book2)

    bible = {
        "series_id": "aethelgard",
        "schema_version": 1,
        "entities": {
            "char:lena-popescu": _entity(
                "char:lena-popescu", "character", "Lena Popescu",
                {"status": {"by-book": {"1": "alive", "2": "alive"}},
                 "role": {"value": "student",
                          "iron": ["Lena studies architecture at Aethelgard"]}},
                ["1:chapter-01"], ["Lena", "Lena P."], "R001"),
            "char:uncle-radu": _entity(
                "char:uncle-radu", "character", "Uncle Radu",
                {"status": {"by-book": {"1": "deceased"}}},
                ["1:chapter-02"], ["Radu"]),
            "char:maria-popescu": _entity(
                "char:maria-popescu", "character", "Maria Popescu",
                {"status": {"by-book": {"1": "alive", "2": "alive"}}},
                ["1:chapter-01"]),
            "prop:brass-key": _entity(
                "prop:brass-key", "prop", "Brass key to the east wing",
                {"location": {"by-book": {"1": "Lena's desk", "2": "vault"}}},
                ["1:chapter-09"]),
            "promise:the-vault-promise": _entity(
                "promise:the-vault-promise", "promise", "The vault promise",
                {"status": {"by-book": {"1": "planted", "2": "open"}}},
                ["1:chapter-02"]),
            "knowledge:academy-founded": _entity(
                "knowledge:academy-founded", "knowledge",
                "The academy was founded in 1847",
                {"fact": {"value": True}},
                ["1:chapter-01"]),
        },
        "timeline": {"events": [
            {"eid": "E001", "when": "2011-07", "summary":
             "Lena receives the Aethelgard bursary",
             "established-in": "1:chapter-01"},
            {"eid": "E002", "when": "long ago", "summary":
             "The academy founding feast", "established-in": "1:chapter-01"},
            {"eid": "E011", "when": "2011-09", "summary": "Term begins",
             "established-in": "1:chapter-03"},
        ]},
    }
    story_hash_1 = "sha256:" + hashlib.sha256(
        (book1 / "kb" / "story.md").read_bytes()).hexdigest()
    story_hash_2 = "sha256:" + hashlib.sha256(
        (book2 / "kb" / "story.md").read_bytes()).hexdigest()
    manifest = {
        "kind": "vellum-library",
        "schema_version": 1,
        "series": {"title": "Aethelgard", "created": "2026-09-10T00:00:00Z",
                   "next_event_id": 12, "next_retcon_id": 3},
        "books": [
            {"book_uuid": BOOK1_UUID, "title": "Volumul I",
             "path": "../book-1", "ordinal": 1, "status": "published",
             "linked_at": "2026-09-10T00:00:00Z", "unlinked_at": None,
             "engine_min_version": "0.1.1", "kb_entity_count": 5,
             "story_hash_at_link": story_hash_1},
            {"book_uuid": BOOK2_UUID, "title": "Volumul II",
             "path": "../book-2", "ordinal": 2, "status": "draft",
             "linked_at": "2026-09-10T00:00:00Z", "unlinked_at": None,
             "engine_min_version": "0.1.1", "kb_entity_count": 9,
             "story_hash_at_link": story_hash_2},
        ],
        "engine_min_version_global": "0.1.1",
    }
    _write(library / "library.json", json.dumps(manifest, indent=2) + "\n")
    _write(library / "series" / "bible.json",
           json.dumps(bible, indent=2, ensure_ascii=False) + "\n")
    _write(library / "series" / "retcons.jsonl", "\n".join([
        json.dumps({"rid": "R001", "at": "2026-09-10T11:02:00Z",
                    "author_words": "Lena's status was confirmed for book two.",
                    "kind": "fact-change", "entity": "char:lena-popescu",
                    "field": "fields.status", "from_book": 1,
                    "old_by_book": {"1": "alive"},
                    "new_by_book": {"1": "alive", "2": "alive"},
                    "proposed_by": 2}, ensure_ascii=False),
        json.dumps({"rid": "R002", "at": "2026-09-10T15:40:00Z",
                    "author_words": "The brass key went to the vault at the end of book 1.",
                    "kind": "fact-change", "entity": "prop:brass-key",
                    "field": "fields.location", "from_book": 1,
                    "old_by_book": {"1": "Lena's desk"},
                    "new_by_book": {"1": "Lena's desk", "2": "vault"},
                    "proposed_by": 2}, ensure_ascii=False),
    ]) + "\n")
    _write(library / "series" / "exemptions.json",
           json.dumps({"dismissals": []}, indent=2) + "\n")
    _write(library / "series" / "errata.md",
           "# Errata — printed vs canon\n\n"
           "R001 records the printed decision.\n"
           "The key's hiding place was shown in chapter-04 of book 1.\n"
           "R002 is discussed at 1/chapter-01.\n")
    for root, uid, ordinal, status in (
            (book1, BOOK1_UUID, 1, "published"),
            (book2, BOOK2_UUID, 2, "draft")):
        _write(root / ".vellum" / "series-link.json", json.dumps({
            "series_root": "../library", "book_uuid": uid,
            "ordinal": ordinal, "status": status,
            "engine_min_version": "0.1.1",
        }, indent=2) + "\n")
    return library


# ---------------------------------------------------------------------------
# Spec 17 fixtures: min-book (minimal valid v0.1.1 book) and carte2-like
# (populated kb, populated series exemptions, prose-heavy chapter).
# ---------------------------------------------------------------------------

MIN_BOOK_UUID = "3f2c9a1e-3333-4aaa-9bbb-000000000003"
CARTE2_UUID = "3f2c9a1e-4444-4aaa-9bbb-000000000004"


def _seed_library_skeleton(library, title, book_uuid, book_root, book_title,
                           status="draft"):
    _write(library / "library.json", json.dumps({
        "kind": "vellum-library", "schema_version": 1,
        "series": {"title": title, "created": "2026-09-10T00:00:00Z",
                   "next_event_id": 1, "next_retcon_id": 1},
        "books": [{
            "book_uuid": book_uuid, "title": book_title,
            "path": "../" + book_root.name, "ordinal": 1,
            "status": status, "linked_at": "2026-09-10T00:00:00Z",
            "unlinked_at": None, "engine_min_version": "0.1.1",
            "kb_entity_count": None, "story_hash_at_link": None,
        }],
        "engine_min_version_global": "0.1.1",
    }, indent=2) + "\n")
    _write(library / "series" / "bible.json", json.dumps({
        "series_id": re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-"),
        "schema_version": 1, "entities": {},
        "timeline": {"events": []},
    }, indent=2) + "\n")
    (library / "series" / "retcons.jsonl").write_text(
        "", encoding="utf-8", newline="\n")
    _write(library / "series" / "exemptions.json",
           json.dumps({"dismissals": []}, indent=2) + "\n")
    _write(library / "series" / "errata.md", "# Errata — printed vs canon\n")
    _write(book_root / ".vellum" / "series-link.json", json.dumps({
        "series_root": "../" + library.name, "book_uuid": book_uuid,
        "ordinal": 1, "status": status, "engine_min_version": "0.1.1",
    }, indent=2) + "\n")


def seed_min_book(destination):
    """Spec 17 min-book: a minimal valid v0.1.1 book + empty library."""
    destination = Path(destination)
    destination.mkdir(parents=True, exist_ok=True)
    library = destination / "library"
    book = destination / "min-book"
    _write(book / "kb" / "story.md", _story("Min Book"))
    _write(book / "kb" / "characters" / "character-solo.md",
           _char("character-solo", "Solo"))
    _write(book / "manuscript" / "chapters" / "chapter-01.md",
           _chapter(1, ["character-solo"], title="Alone"))
    _seed_library_skeleton(library, "Min Series", MIN_BOOK_UUID, book,
                           "Min Book")
    return library


def _question(eid, title, status="open", series_id=None):
    lines = ["---", "id: %s" % eid, "type: question",
             "title: %s" % title, "status: %s" % status,
             "raised-in: chapter-01", "resolved-in: null"]
    if series_id:
        lines.append("series-id: %s" % series_id)
    lines += ["---", "", "Întrebarea rămâne deschisă."]
    return "\n".join(lines) + "\n"


def seed_carte2_like(destination):
    """Spec 17 carte2-like: 60 kb entities, populated series exemptions, and
    a prose-heavy chapter (a name appearing 200x that is in no kb file and
    no bible entity — the T5 prose-noise case, safe by construction because
    matching never reads prose)."""
    destination = Path(destination)
    destination.mkdir(parents=True, exist_ok=True)
    library = destination / "library"
    book = destination / "carte2-like"

    _write(book / "kb" / "story.md", _story("Carte2 Like"))
    entities = {}
    for i in range(1, 21):
        eid = "character-c%03d" % i
        _write(book / "kb" / "characters" / ("%s.md" % eid),
               _char(eid, "Cast Member %03d" % i,
                     status="alive" if i % 3 else "deceased",
                     series_id="char:c%03d" % i))
        entities["char:c%03d" % i] = _entity(
            "char:c%03d" % i, "character", "Cast Member %03d" % i,
            {"status": {"by-book": {"1": "alive" if i % 3 else "deceased"}},
             "role": {"value": "student"}},
            ["1:chapter-01"])
    for i in range(1, 11):
        eid = "prop-p%03d" % i
        _write(book / "kb" / "props" / ("%s.md" % eid),
               _prop(eid, "Prop %03d" % i, "shelf %d" % i,
                     series_id="prop:p%03d" % i))
        entities["prop:p%03d" % i] = _entity(
            "prop:p%03d" % i, "prop", "Prop %03d" % i,
            {"location": {"by-book": {"1": "shelf %d" % i}}},
            ["1:chapter-01"])
    for i in range(1, 11):
        eid = "promise-q%03d" % i
        _write(book / "kb" / "promises" / ("%s.md" % eid),
               _promise(eid, "Promise %03d" % i, "planted",
                        series_id="promise:q%03d" % i))
        entities["promise:q%03d" % i] = _entity(
            "promise:q%03d" % i, "promise", "Promise %03d" % i,
            {"status": {"by-book": {"1": "planted"}}}, ["1:chapter-01"])
    for i in range(1, 11):
        eid = "question-s%03d" % i
        _write(book / "kb" / "questions" / ("%s.md" % eid),
               _question(eid, "Question %03d" % i,
                         series_id="question:s%03d" % i))
        entities["question:s%03d" % i] = _entity(
            "question:s%03d" % i, "question", "Question %03d" % i,
            {"status": {"by-book": {"1": "open"}}}, ["1:chapter-01"])
    for i in range(1, 11):
        eid = "knowledge-k%03d" % i
        _write(book / "kb" / "knowledge" / ("%s.md" % eid),
               _knowledge(eid, "World fact %03d" % i, "chapter-01",
                          series_id="knowledge:k%03d" % i))
        entities["knowledge:k%03d" % i] = _entity(
            "knowledge:k%03d" % i, "knowledge", "World fact %03d" % i,
            {"fact": {"value": True}}, ["1:chapter-01"])
    assert len(entities) == 60

    # Book kb deliberately says c002 is 'away' while canon says 'alive':
    # the divergence is dismissed in the populated exemptions below.
    c002 = book / "kb" / "characters" / "character-c002.md"
    c002_text = c002.read_text(encoding="utf-8").replace(
        "status: deceased", "status: away").replace(
        "status: alive", "status: away")
    _write(c002, c002_text)

    # Prose-heavy chapter: a name 200x that appears in no kb file and no
    # bible entity. Matching runs on frontmatter and kb names only (spec
    # 8.5), so it must produce zero findings and zero plan rows.
    line = "Vasilica trece pragul și închide ușa în urma ei. " * 40
    body = "\n\n".join([line] * 5) + "\n"
    _write(book / "manuscript" / "chapters" / "chapter-01.md",
           "---\ntitle: Zgomot\nnumber: 1\nstatus: final\n"
           "pov: character-c001\ncharacters: [character-c001]\n"
           "mentions: []\npromises-advanced: []\nword-target: 3200\n"
           "word-count: null\n---\n\n" + body)

    story_hash = "sha256:" + hashlib.sha256(
        (book / "kb" / "story.md").read_bytes()).hexdigest()
    _seed_library_skeleton(library, "Carte2-Like Series", CARTE2_UUID, book,
                           "Carte2 Like")
    manifest = json.loads((library / "library.json").read_text(
        encoding="utf-8"))
    manifest["books"][0]["kb_entity_count"] = 60
    manifest["books"][0]["story_hash_at_link"] = story_hash
    _write(library / "library.json", json.dumps(manifest, indent=2) + "\n")

    bible = json.loads((library / "series" / "bible.json").read_text(
        encoding="utf-8"))
    bible["entities"] = entities
    _write(library / "series" / "bible.json",
           json.dumps(bible, indent=2, ensure_ascii=False) + "\n")

    # Populated series exemptions: the c002 status divergence dismissed with
    # the kb file's hash at dismissal time (uniform rule, spec 6.3).
    kb_hash = "sha256:" + hashlib.sha256(
        (book / "kb" / "characters" / "character-c002.md").read_bytes()
    ).hexdigest()
    _write(library / "series" / "exemptions.json", json.dumps({
        "dismissals": [{
            "finding_id": "series:canon-divergence:char:c002:status:1",
            "reason_author_words": "C002 is away on purpose through book one.",
            "at": "2026-09-10T12:00:00Z",
            "expires_on_entity_hash": kb_hash,
            "scope": "series",
        }]}, indent=2, ensure_ascii=False) + "\n")
    return library
