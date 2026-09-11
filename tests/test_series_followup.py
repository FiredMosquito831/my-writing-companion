# Series-layer follow-up coverage (library-spec.md 17) — regression tests for
# the repaired contracts: plan-driven bootstrap --apply (existing-entity and
# new resolutions, no approval bypass), unlink/re-link revival, sibling
# orphan-sidecar detection, established-before retcons, plan frontmatter
# validation, capped series-card injection, the byte-identity golden surface,
# real lock contention, and the per-subcommand exit-code table.
import json
import os
import subprocess
import sys
import time
from pathlib import Path

PLUGIN_ROOT = Path(__file__).resolve().parent.parent


def _keys(findings):
    return {f["key"] for f in findings}


def _latest_plan(library, prefix):
    paths = sorted((library / "reports").glob(prefix + "*.md"))
    assert paths
    return paths[-1]


def _load_seed():
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "library_seed", PLUGIN_ROOT / "tests" / "fixtures" / "library" /
        "seed.py")
    seed = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(seed)
    return seed


# ---------------------------------------------------------------------------
# bootstrap --apply: the human-resolution flow (spec 8.5)
# ---------------------------------------------------------------------------

_AMB_FILL = ("tier: ambiguity\n  resolution: \n  author_words: \"\"")


def _fill_ambiguities(body, entity, resolution, note, other_note):
    """Resolve one [?] row and mark every other [?] row local."""
    """Resolve one [?] row and mark every other [?] row local."""
    lines = body.split("\n")
    out = []
    current = None
    is_ambiguity = False
    for line in lines:
        if line.startswith("- entity: "):
            current = line[len("- entity: "):].strip()
            is_ambiguity = False
        if line.strip() == "tier: ambiguity":
            is_ambiguity = True
        if is_ambiguity and line.strip() == "resolution:":
            if current == entity:
                out.append("  resolution: %s" % resolution)
            else:
                out.append("  resolution: local")
            continue
        if is_ambiguity and line.strip() == 'author_words: ""':
            out.append('  author_words: "%s"' %
                       (note if current == entity else other_note))
            continue
        out.append(line)
    return "\n".join(out)


_AMB_FILL = "tier: ambiguity\n  resolution: \n  author_words: \"\""


# The helper above is intentionally line-oriented because the plan parser is
# line-oriented; `_AMB_FILL` remains useful for callers that do literal checks.


def test_bootstrap_ambiguity_resolves_existing_entity_and_new(
        library, library_engine, library_books):
    b2 = library_books[1]
    ana = b2 / "kb" / "characters" / "character-ana.md"
    ana.write_text(
        "---\nid: character-ana\ntype: character\nname: Ana Popescu\n"
        "status: alive\ndied-in: null\naliases: []\npov-eligible: true\n"
        "---\n\nAna sta in prag.\n", encoding="utf-8", newline="\n")
    r = library_engine("bootstrap", "--root", str(library), str(b2))
    assert r.returncode == 1, r.stderr
    plan = _latest_plan(library, "bootstrap-plan-")
    body = open(plan, encoding="utf-8").read()
    body = body.replace("approved: false", "approved: true")
    body = _fill_ambiguities(
        body, "character-ana", "char:maria-popescu",
        "Ana is Maria under a new local page.",
        "These rows remain book-local.")
    plan.write_text(body, encoding="utf-8", newline="\n")
    r = library_engine("bootstrap", "--root", str(library), "--apply", plan,
                       str(b2))
    assert r.returncode == 0, r.stderr
    # The resolved existing entity: series-id written into the book kb...
    assert "series-id: char:maria-popescu" in ana.read_text(encoding="utf-8")
    # ...and by-book seeded from the resolved kb entity (spec 8.5).
    bible = json.loads((library / "series" / "bible.json").read_text(
        encoding="utf-8"))
    assert bible["entities"]["char:maria-popescu"]["fields"]["status"][
        "by-book"].get("2") == "alive"

    # resolution: new used to crash with a KeyError ('file') because the raw
    # parsed plan row was appended to the joined list without a kb file.
    fact = b2 / "kb" / "knowledge" / "knowledge-new-fact.md"
    fact.write_text(
        "---\nid: knowledge-new-fact\ntype: knowledge\ntitle: New fact\n"
        "statement: New fact\nholders: []\naudience-learned-in: chapter-03\n"
        "superseded-by: null\n---\n\nFact.\n", encoding="utf-8",
        newline="\n")
    r = library_engine("bootstrap", "--root", str(library), str(b2))
    assert r.returncode == 1
    plan = _latest_plan(library, "bootstrap-plan-")
    body = open(plan, encoding="utf-8").read()
    body = body.replace("approved: false", "approved: true")
    body = _fill_ambiguities(
        body, "knowledge-new-fact", "new",
        "This is a new series fact.", "Remaining rows stay local.")
    plan.write_text(body, encoding="utf-8", newline="\n")
    r = library_engine("bootstrap", "--root", str(library), "--apply", plan,
                       str(b2))
    assert r.returncode == 0, r.stderr
    assert "series-id: knowledge:new-fact" in fact.read_text(encoding="utf-8")
    bible = json.loads((library / "series" / "bible.json").read_text(
        encoding="utf-8"))
    assert "knowledge:new-fact" in bible["entities"]


def test_bootstrap_apply_does_not_join_entities_added_after_plan(
        library, library_engine, library_books):
    b2 = library_books[1]
    r = library_engine("bootstrap", "--root", str(library), str(b2))
    assert r.returncode == 1
    plan = _latest_plan(library, "bootstrap-plan-")
    body = open(plan, encoding="utf-8").read()
    body = body.replace("approved: false", "approved: true")
    body = body.replace(
        _AMB_FILL,
        "tier: ambiguity\n  resolution: local\n"
        '  author_words: "All planned ambiguous rows stay local."')
    plan.write_text(body, encoding="utf-8", newline="\n")
    # An entity added to the book kb after the plan was approved must NOT be
    # joined: --apply executes the reviewed plan, not a fresh derivation.
    late = b2 / "kb" / "characters" / "character-added-late.md"
    late.write_text(
        "---\nid: character-added-late\ntype: character\nname: Added Late\n"
        "status: alive\ndied-in: null\naliases: []\npov-eligible: true\n"
        "---\n\nLate.\n", encoding="utf-8", newline="\n")
    r = library_engine("bootstrap", "--root", str(library), "--apply", plan,
                       str(b2))
    assert r.returncode == 0, r.stderr
    assert "series-id:" not in late.read_text(encoding="utf-8")


def test_bootstrap_apply_does_not_reset_retcon_last_touched(
        library, library_engine, library_books):
    b2 = library_books[1]
    (library / "reports").mkdir(exist_ok=True)
    plan = library / "reports" / "bootstrap-plan-recapture.md"
    plan.write_text(
        "---\napproved: true\nkind: bootstrap-plan\nbook_ordinal: 2\n"
        "---\n\n## Exact matches (auto-join)\n\n"
        "- entity: character-lena\n  kind: characters\n  tier: exact\n"
        "  series_id: char:lena-popescu\n\n"
        "## Alias matches (auto-join, series:id-mismatch advisory)\n\n"
        "(none)\n\n## [?] Ambiguity rows (human resolution required)\n\n"
        "(none)\n", encoding="utf-8", newline="\n")
    r = library_engine("bootstrap", "--root", str(library), "--apply", plan,
                       str(b2))
    assert r.returncode == 0, r.stderr
    bible = json.loads((library / "series" / "bible.json").read_text(
        encoding="utf-8"))
    # R001 owns this entity; a re-capture must not reset it to "bootstrap".
    assert bible["entities"]["char:lena-popescu"]["last_touched"] == "R001"


# ---------------------------------------------------------------------------
# unlink / re-link lifecycle (spec 15.7 -> 15.1) and sidecar choice (8.3)
# ---------------------------------------------------------------------------

def test_unlink_relink_restores_same_manifest_entry(
        library, library_engine, library_books):
    book = library_books[1]
    manifest_path = library / "library.json"
    before = json.loads(manifest_path.read_text(encoding="utf-8"))
    original = next(b for b in before["books"] if b["ordinal"] == 2)
    assert library_engine("unlink", "--root", str(library),
                          str(book)).returncode == 0
    assert library_engine("link", "--root", str(library),
                          str(book)).returncode == 0
    after = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert len(after["books"]) == 2  # revived, not duplicated
    revived = next(b for b in after["books"]
                   if b["book_uuid"] == original["book_uuid"])
    assert revived["ordinal"] == original["ordinal"]
    assert revived["unlinked_at"] is None
    # All downstream commands bind to the revived entry.
    r = library_engine("state", "--root", str(library), "--card-line", str(book))
    assert r.returncode == 0
    assert "ordinal 2" in r.stdout


def test_unlink_keep_sidecar_writes_empty_marker(
        library, library_engine, library_books):
    book = library_books[1]
    r = library_engine("unlink", "--root", str(library), "--keep-sidecar",
                       str(book))
    assert r.returncode == 0, r.stderr
    assert json.loads((book / ".vellum" / "series-link.json").read_text(
        encoding="utf-8")) == {}


# ---------------------------------------------------------------------------
# validate: automatic half-state recovery detection (spec 8.4/T4)
# ---------------------------------------------------------------------------

def test_validate_plain_scan_finds_sibling_orphan_sidecar(
        library, library_engine):
    orphan = library.parent / "orphan-book"
    (orphan / ".vellum").mkdir(parents=True)
    (orphan / ".vellum" / "series-link.json").write_text(
        '{"book_uuid":"orphan-uuid","series_root":"../library"}\n',
        encoding="utf-8")
    r = library_engine("validate", "--root", str(library))
    assert r.returncode == 1
    fs = [json.loads(l) for l in r.stdout.splitlines() if l.startswith("{")]
    assert "series:half-linked:orphan-uuid" in _keys(fs)


# ---------------------------------------------------------------------------
# retcon --apply: established-before timeline events (spec 8.9) and plan
# frontmatter validation (exit-2 contract, spec 8)
# ---------------------------------------------------------------------------

def test_retcon_apply_established_before_mints_timeline_event(
        library, library_engine):
    plan = library / "reports" / "retcon-plan-event.md"
    plan.parent.mkdir(exist_ok=True)
    plan.write_text(
        "---\napproved: true\nbook_ordinal: 2\n---\n\n## Rows\n\n"
        "- entity: timeline\n  kind: established-before\n"
        "  when: 2011-08\n  summary: The hidden archive opens.\n"
        "  coordinate: 2/chapter-01\n"
        '  author_words: "The archive predates the scene."\n',
        encoding="utf-8", newline="\n")
    r = library_engine("retcon", "--root", str(library), "--apply", str(plan))
    assert r.returncode == 0, r.stderr
    bible = json.loads((library / "series" / "bible.json").read_text(
        encoding="utf-8"))
    assert bible["timeline"]["events"][-1] == {
        "eid": "E012", "when": "2011-08",
        "summary": "The hidden archive opens.",
        "established-in": "2:chapter-01"}
    manifest = json.loads((library / "library.json").read_text(
        encoding="utf-8"))
    assert manifest["series"]["next_event_id"] == 13
    log = (library / "series" / "retcons.jsonl").read_text(
        encoding="utf-8").strip().splitlines()
    assert json.loads(log[-1])["kind"] == "established-before"


def test_retcon_apply_rejects_non_integer_book_ordinal(
        library, library_engine):
    plan = library / "reports" / "retcon-plan-bad-ordinal.md"
    plan.parent.mkdir(exist_ok=True)
    plan.write_text("---\napproved: true\nbook_ordinal: two\n---\n",
                    encoding="utf-8", newline="\n")
    r = library_engine("retcon", "--root", str(library), "--apply", str(plan))
    assert r.returncode == 2
    assert "book_ordinal" in r.stderr


def test_retcon_plan_archived_book_is_quiet(library, library_engine,
                                            library_books):
    b2 = library_books[1]
    manifest_path = library / "library.json"
    doc = json.loads(manifest_path.read_text(encoding="utf-8"))
    doc["books"][1]["status"] = "archived"
    manifest_path.write_text(json.dumps(doc, indent=2), encoding="utf-8")
    r = library_engine("retcon-plan", "--root", str(library), str(b2))
    assert r.returncode == 0, r.stderr
    assert "archived" in r.stderr


# ---------------------------------------------------------------------------
# Series state card: injected section reserves the 12KB total cap (spec 8.8)
# ---------------------------------------------------------------------------

def test_series_injected_card_reserves_total_cap(
        engine, project, library_engine, tmp_path):
    libroot = tmp_path / "large-series"
    assert library_engine("init", "--root", str(libroot)).returncode == 0
    assert library_engine("link", "--root", str(libroot),
                          str(project)).returncode == 0
    # A do-not-re-explain register that dwarfs the 12KB card cap (the sample
    # project is book 2, so every fact established in book 1 lands in the
    # register): the injected series section must be truncated to the
    # remaining budget, never push the whole card into card_over_cap.
    bible_path = libroot / "series" / "bible.json"
    bible = json.loads(bible_path.read_text(encoding="utf-8"))
    manifest_path = libroot / "library.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["books"][0]["ordinal"] = 2
    manifest_path.write_text(json.dumps(manifest, indent=2),
                             encoding="utf-8", newline="\n")
    sidecar = project / ".vellum" / "series-link.json"
    sc = json.loads(sidecar.read_text(encoding="utf-8"))
    sc["ordinal"] = 2
    sidecar.write_text(json.dumps(sc, indent=2), encoding="utf-8",
                       newline="\n")
    bible["entities"] = {}
    for i in range(400):
        sid = "knowledge:long-%03d" % i
        bible["entities"][sid] = {
            "type": "knowledge", "series_id": sid,
            "name": "Long fact " + ("x" * 80), "aliases": [],
            "fields": {"fact": {"value": "y" * 120}},
            "established-in": ["1:chapter-01"], "scope": "shared",
            "last_touched": "bootstrap"}
    bible_path.write_text(json.dumps(bible, ensure_ascii=False, indent=2),
                          encoding="utf-8", newline="\n")
    r = library_engine("state", "--root", str(libroot), str(project))
    assert r.returncode == 0, r.stderr
    # The standalone command caps at its own 12KB budget with a marker.
    assert len(r.stdout.encode("utf-8")) <= 12 * 1024 + 200
    assert "series section truncated" in r.stdout
    # The injected card in the project stays under the shared hard cap, and
    # the rebuild is not frozen into card_over_cap by series-driven bloat.
    r2 = engine("state", "rebuild")
    assert r2.returncode == 0, r2.stderr
    card = project / "state" / "state-card.md"
    assert card.stat().st_size <= 12 * 1024
    assert "series section truncated" in card.read_text(encoding="utf-8")
    tracking = json.loads(
        (project / "state" / "_tracking-state.json").read_text(
            encoding="utf-8"))
    assert tracking.get("card_over_cap") is None
    tracking = json.loads(
        (project / "state" / "_tracking-state.json").read_text(
            encoding="utf-8"))
    assert tracking.get("card_over_cap") is None


# ---------------------------------------------------------------------------
# T1 golden: v0.1.1 surface stable through link / bootstrap / retcon
# ---------------------------------------------------------------------------

def _v011_surface(engine, project):
    commands = [
        ("ledger", "check"), ("bible", "validate"), ("wordcount",),
        ("knowledge", "character-vess", "--as-of", "5"),
        ("state", "rebuild"),
    ]
    out = []
    for args in commands:
        r = engine(*args)
        out.append((args, r.returncode, r.stdout))
    # The state card is part of the T1 snapshot surface (spec 17-T1). The
    # generated-at stamp and the series section the link injects (spec T3)
    # are normalized; every other v0.1.1 byte must be identical.
    out.append(("state-card", 0, _normalized_state_card(project)))
    return out


def _normalized_state_card(project):
    import hashlib
    card = (project / "state" / "state-card.md").read_text(encoding="utf-8")
    idx = card.find("## Series state")
    if idx != -1:
        card = card[:idx]
    lines = [l for l in card.split("\n")
             if not l.startswith("Generated by `vellum state")]
    body = "\n".join(lines).rstrip("\n")
    return hashlib.sha256(body.encode("utf-8")).hexdigest()


def _project_hashes(project):
    import hashlib
    out = {}
    for path in project.rglob("*"):
        if not path.is_file():
            continue
        rel = path.relative_to(project).as_posix()
        if rel.startswith(("state/", "work/", "export/", ".vellum/")):
            continue
        out[rel] = hashlib.sha256(path.read_bytes()).hexdigest()
    return out


def test_v011_surface_golden_across_link_bootstrap_and_retcon(
        engine, project, library_engine, tmp_path):
    assert engine("state", "rebuild").returncode == 0
    baseline_surface = _v011_surface(engine, project)
    baseline_hashes = _project_hashes(project)

    libroot = tmp_path / "golden-library"
    assert library_engine("init", "--root", str(libroot)).returncode == 0
    assert library_engine("link", "--root", str(libroot),
                          str(project)).returncode == 0
    # (a) == (b): linking changes nothing in the v0.1.1 surface.
    assert _v011_surface(engine, project) == baseline_surface
    assert _project_hashes(project) == baseline_hashes

    r = library_engine("bootstrap", "--root", str(libroot), str(project))
    assert r.returncode == 1
    plan = _latest_plan(libroot, "bootstrap-plan-")
    body = open(plan, encoding="utf-8").read()
    body = body.replace("approved: false", "approved: true")
    body = body.replace(
        _AMB_FILL,
        'tier: ambiguity\n  resolution: new\n'
        '  author_words: "Captured at migration."')
    plan.write_text(body, encoding="utf-8", newline="\n")
    assert library_engine("bootstrap", "--root", str(libroot), "--apply",
                          plan, str(project)).returncode == 0
    assert _v011_surface(engine, project) == baseline_surface
    after = _project_hashes(project)
    assert set(after) == set(baseline_hashes)
    # (c): source files differ only by the injected series-id lines.
    for rel, digest in baseline_hashes.items():
        before_bytes = (project / rel).read_bytes()
        after_text = (project / rel).read_text(encoding="utf-8")
        normalized = "\n".join(
            line for line in after_text.split("\n")
            if not line.startswith("series-id:"))
        before_norm = "\n".join(
            line for line in before_bytes.decode("utf-8").split("\n")
            if not line.startswith("series-id:"))
        assert normalized.encode("utf-8") == before_norm.encode("utf-8"), rel

    # (d): a retcon application leaves the v0.1.1 surface unchanged.
    mira = (project / "kb" / "characters" / "character-mira-tarn.md")
    sid = None
    for line in mira.read_text(encoding="utf-8").split("\n"):
        if line.startswith("series-id:"):
            sid = line.split(":", 1)[1].strip()
    assert sid, "bootstrap wrote no series-id into character-mira-tarn"
    retcon = libroot / "reports" / "retcon-plan-golden.md"
    retcon.write_text(
        "---\napproved: true\nbook_ordinal: 1\n---\n\n## Rows\n\n"
        "- entity: %s\n  field: status\n"
        '  new_by_book: {"1": "alive"}\n'
        '  author_words: "The status is confirmed."\n' % sid,
        encoding="utf-8", newline="\n")
    assert library_engine("retcon", "--root", str(libroot), "--apply",
                          str(retcon)).returncode == 0, \
        library_engine("retcon", "--root", str(libroot), "--apply",
                       str(retcon)).stderr
    assert _v011_surface(engine, project) == baseline_surface


# ---------------------------------------------------------------------------
# T11 concurrency: real second process holding the lock
# ---------------------------------------------------------------------------

def test_lock_contention_uses_real_second_process(library):
    script = ("import os,time\n"
              "fd=os.open(os.environ['VELLUM_TEST_LOCK'], "
              "os.O_CREAT|os.O_EXCL|os.O_WRONLY)\n"
              "os.write(fd,b'999 holder')\n"
              "os.close(fd)\n"
              "time.sleep(10)\n")
    env = dict(os.environ)
    env["VELLUM_TEST_LOCK"] = str(library / ".lock")
    holder = subprocess.Popen([sys.executable, "-c", script], env=env)
    try:
        deadline = time.time() + 5
        while not (library / ".lock").exists() and time.time() < deadline:
            time.sleep(0.01)
        env2 = dict(os.environ)
        env2["VELLUM_LIB_LOCK_TIMEOUT"] = "0.2"
        r = subprocess.run(
            [sys.executable, str(PLUGIN_ROOT / "scripts" / "library.py"),
             "dismiss", "--root", str(library), "series:test:1",
             "--reason", "real contention"],
            cwd=str(library), env=env2, capture_output=True, text=True,
            encoding="utf-8", timeout=15)
        assert r.returncode == 2
        assert "locked by another process" in r.stderr
    finally:
        holder.terminate()
        holder.wait(timeout=5)
        (library / ".lock").unlink(missing_ok=True)


# ---------------------------------------------------------------------------
# T12 exit-code table: every subcommand exercised (spec 8)
# ---------------------------------------------------------------------------

def test_series_exit_code_table_covers_every_subcommand(
        library, library_engine, library_books, tmp_path):
    b2 = library_books[1]
    cases = [
        ((), 2),
        (("no-such-command",), 2),
        (("init", str(tmp_path / "positional-init")), 0),
        (("init", "--root", str(library_books[0])), 2),
        (("init", "--root",
          str(library_books[0] / "kb" / "story.md")), 2),
        (("link", "--root", str(library),
          str(tmp_path / "missing-book")), 2),
        (("unlink", "--root", str(library),
          str(tmp_path / "missing-book")), 2),
        (("validate", "--root", str(library)), 1),
        (("validate", "--root", str(tmp_path / "missing-library")), 2),
        (("bootstrap", "--root", str(library), str(b2)), 1),
        (("retcon-check", "--root", str(library), str(b2)), 1),
        (("retcon-plan", "--root", str(library), str(b2)), 1),
        (("state", "--root", str(library), str(b2)), 0),
        (("timeline", "--root", str(library)), 1),
        (("handoff", "--root", str(library), str(b2)), 0),
    ]
    seen = set()
    for args, expected in cases:
        r = library_engine(*args)
        assert r.returncode == expected, (args, r.stderr)
        if args:
            seen.add(args[0])
    bad = library / "reports" / "exit-bad.md"
    bad.parent.mkdir(exist_ok=True)
    bad.write_text("---\napproved: false\n---\n", encoding="utf-8")
    assert library_engine("retcon", "--root", str(library), "--apply",
                          str(bad)).returncode == 2
    seen.add("retcon")
    assert library_engine("dismiss", "--root", str(library),
                          "series:exit:1").returncode == 2
    seen.add("dismiss")
    assert seen >= {"init", "link", "unlink", "validate", "bootstrap",
                    "retcon-check", "retcon-plan", "retcon", "state",
                    "timeline", "handoff", "dismiss"}


# ---------------------------------------------------------------------------
# Spec 17 fixtures: min-book and carte2-like (populated exemptions +
# prose-noise chapter)
# ---------------------------------------------------------------------------

def test_min_book_fixture_is_shipped_and_linkable(tmp_path, library_engine):
    seed = _load_seed()
    lib = seed.seed_min_book(str(tmp_path / "min"))
    book = lib.parent / "min-book"
    assert (book / "kb" / "story.md").exists()
    assert library_engine("validate", "--root", str(lib)).returncode in (0, 1)
    r = library_engine("bootstrap", "--root", str(lib), str(book))
    assert r.returncode in (0, 1), r.stderr


def test_carte2_like_fixture_prose_noise_is_ignored(tmp_path, library_engine):
    seed = _load_seed()
    lib = seed.seed_carte2_like(str(tmp_path / "carte2"))
    book = lib.parent / "carte2-like"
    # T5: a name appearing 200x in chapter prose produces zero findings and
    # zero plan rows (matching never reads prose, spec 8.5/16-L11).
    r = library_engine("bootstrap", "--root", str(lib), str(book))
    assert r.returncode in (0, 1), r.stderr
    plan = _latest_plan(lib, "bootstrap-plan-")
    assert "Vasilica" not in open(plan, encoding="utf-8").read()
    r = library_engine("retcon-check", "--root", str(lib), str(book))
    assert "Vasilica" not in r.stdout
    # The populated series exemption suppresses its divergence finding.
    assert "series:canon-divergence:char:c002:status:1" not in r.stdout
# ---------------------------------------------------------------------------
# Regression coverage for the v0.2.0 repair sweep
# ---------------------------------------------------------------------------

def _library_findings_from(library_engine, book):
    r = library_engine("retcon-check", "--root", ".", str(book))
    fs = [json.loads(l) for l in r.stdout.splitlines()
          if l.startswith("{")]
    return r, fs


def test_dismiss_coordinate_key_binds_the_firing_books_hash(
        library, library_engine, library_books):
    # The documented `library dismiss <finding-id>` form must bind the hash
    # of the book the finding fired in, not book 1's same-entity kb file:
    # a coordinate-terminated key ends ":N:chapter-MM" and the ordinal, not
    # the chapter number, selects the book.
    b2 = library_books[1]
    fid = "series:deceased-as-of-start:char:uncle-radu:2:chapter-01"
    r = library_engine("dismiss", "--root", ".", fid,
                       "--reason", "He is a ghost; the apparition is "
                                   "intentional.")
    assert r.returncode == 0, r.stderr
    doc = json.loads((library / "series" / "exemptions.json").read_text(
        encoding="utf-8"))
    entry = doc["dismissals"][0]
    import hashlib
    want = "sha256:" + hashlib.sha256(
        (b2 / "kb" / "characters" / "character-radu.md").read_bytes()
    ).hexdigest()
    assert entry["expires_on_entity_hash"] == want
    # the dismissal suppresses the finding for the firing book
    _, fs = _library_findings_from(library_engine, b2)
    assert fid not in _keys(fs)


def test_coordinate_dismissal_stale_rearm_uses_firing_book(
        library, library_engine, library_books):
    b2 = library_books[1]
    fid = "series:deceased-as-of-start:char:uncle-radu:2:chapter-01"
    library_engine("dismiss", "--root", ".", fid,
                   "--reason", "Intentional apparition.")
    # A direct edit of book 2's kb entity flips the hash: the dismissal
    # goes stale and the finding re-fires. If the hash had been bound to
    # book 1's kb file (the misbinding regression), this edit would not
    # re-arm anything.
    p = b2 / "kb" / "characters" / "character-radu.md"
    p.write_text(p.read_text(encoding="utf-8") + "\n", encoding="utf-8")
    _, fs = _library_findings_from(library_engine, b2)
    hit = [f for f in fs if f["key"] == fid]
    assert hit and "went stale" in hit[0]["issue"]


def test_wildcard_dismissal_suppresses_recurring_apparition(
        library, library_engine, library_books):
    # spec 10 #1 exempt list: an intentionally recurring apparition is
    # dismissed once with the wildcard key, not once per chapter.
    b2 = library_books[1]
    fid = "series:deceased-as-of-start:char:uncle-radu:*"
    r = library_engine("dismiss", "--root", ".", fid,
                       "--reason", "He is a ghost; the apparition is "
                                   "intentional.")
    assert r.returncode == 0, r.stderr
    doc = json.loads((library / "series" / "exemptions.json").read_text(
        encoding="utf-8"))
    # a wildcard is a standing exempt-list entry: no single firing book to
    # hash against, so it is recorded unbound (a retcon that changes the
    # entity flushes it, spec 8.7)
    assert "expires_on_entity_hash" not in doc["dismissals"][0]
    _, fs = _library_findings_from(library_engine, b2)
    assert not any(k.startswith("series:deceased-as-of-start:"
                                "char:uncle-radu") for k in _keys(fs))
    # other characters' findings are unaffected by the wildcard
    assert any(k.startswith("series:unlinked-cast:") for k in _keys(fs))


def test_retcon_check_summary_counts_emitted_rows(
        library, library_engine, library_books):
    # After a dismissal the stderr summary must match the rows actually
    # emitted, not the pre-dismissal catalog counts.
    b2 = library_books[1]
    fid = "series:canon-divergence:char:lena-popescu:status:2"
    r = library_engine("dismiss", "--root", ".", fid,
                       "--reason", "Lena grieves through book two on "
                                   "purpose.",
                       "--book-root", str(b2))
    assert r.returncode == 0, r.stderr
    r, fs = _library_findings_from(library_engine, b2)
    assert fid not in _keys(fs)
    det = sum(1 for f in fs if f.get("resolution") != "judgment")
    jud = sum(1 for f in fs if f.get("resolution") == "judgment")
    expected = ("library retcon-check: %d deterministic findings, %d "
                "judgment-flagged (muse/kb-lead review)" % (det, jud))
    assert expected in r.stderr


def test_retcon_apply_merges_and_refuses_frozen_ordinals(
        library, library_engine):
    # A row's new_by_book is merged onto the existing by-book map, and a
    # row that changes a published ordinal is refused without the explicit
    # override (freeze doctrine, spec 12).
    (library / "reports").mkdir(exist_ok=True)
    plan = library / "reports" / "retcon-plan-merge.md"

    def write(body):
        plan.write_text(body, encoding="utf-8", newline="\n")

    head = "---\napproved: true\nbook_ordinal: 2\n"
    row = ("- entity: char:lena-popescu\n  field: status\n"
           "  new_by_book: %s\n"
           '  author_words: "Author words."\n')
    # a draft-book plan that rewrites book 1's frozen value: refused
    write(head + "---\n\n## Rows\n\n" + row % '{"1": "unknown", "2": "g"}')
    r = library_engine("retcon", "--root", ".", "--apply", str(plan))
    assert r.returncode == 2
    assert "override_published" in r.stderr
    # with the explicit override it applies
    write(head + "override_published: true\n---\n\n## Rows\n\n"
          + row % '{"1": "unknown", "2": "g"}')
    r = library_engine("retcon", "--root", ".", "--apply", str(plan))
    assert r.returncode == 0, r.stderr
    # a partial map only changes the ordinals it names: book 1's pinned
    # value survives the merge instead of being destroyed
    write(head + "---\n\n## Rows\n\n" + row % '{"2": "calm"}')
    r = library_engine("retcon", "--root", ".", "--apply", str(plan))
    assert r.returncode == 0, r.stderr
    bible = json.loads((library / "series" / "bible.json").read_text(
        encoding="utf-8"))
    field = bible["entities"]["char:lena-popescu"]["fields"]["status"]
    assert field["by-book"] == {"1": "unknown", "2": "calm"}


def test_established_before_requires_explicit_coordinate(
        library, library_engine):
    # No fabricated chapter-01 provenance: the coordinate is required.
    (library / "reports").mkdir(exist_ok=True)
    plan = library / "reports" / "retcon-plan-nocoord.md"
    plan.write_text(
        "---\napproved: true\nbook_ordinal: 2\n---\n\n## Rows\n\n"
        "- entity: timeline\n  kind: established-before\n"
        "  when: 2011-08\n  summary: The hidden archive opens.\n"
        '  author_words: "The archive predates the scene."\n',
        encoding="utf-8", newline="\n")
    r = library_engine("retcon", "--root", ".", "--apply", str(plan))
    assert r.returncode == 2
    assert "coordinate" in r.stderr


def test_validate_ignores_sidecars_of_other_libraries(
        library, library_engine):
    # A book linked to a sibling library is not this manifest's defect:
    # only sidecars whose series_root resolves to this library are
    # half-linked here (no false positives).
    foreign = library.parent / "foreign-book"
    (foreign / ".vellum").mkdir(parents=True)
    (foreign / ".vellum" / "series-link.json").write_text(
        '{"book_uuid":"foreign-uuid","series_root":"../elsewhere"}\n',
        encoding="utf-8")
    r = library_engine("validate", "--root", str(library))
    fs = [json.loads(l) for l in r.stdout.splitlines() if l.startswith("{")]
    assert "series:half-linked:foreign-uuid" not in _keys(fs)


def test_structural_dismissal_survives_library_rewrites(
        library, library_engine):
    # Validate-scope structural findings are dismissed without an entity
    # hash: link/unlink/--fix rewrites never stale them into a nag loop.
    fid = "series:timeline-unparsed-when:E002"
    r = library_engine("dismiss", "--root", ".", fid,
                       "--reason", "The feast date is mythical by design.")
    assert r.returncode == 0, r.stderr
    doc = json.loads((library / "series" / "exemptions.json").read_text(
        encoding="utf-8"))
    assert doc["dismissals"][0]["finding_id"] == fid
    assert "expires_on_entity_hash" not in doc["dismissals"][0]
    r = library_engine("validate", "--root", str(library), "--fix")
    assert r.returncode == 1
    fs = [json.loads(l) for l in r.stdout.splitlines() if l.startswith("{")]
    assert fid not in _keys(fs)


def test_knowledge_reveal_planned_is_opt_out(
        library, library_engine, library_books):
    # A planned cross-book reveal (dramatic irony) is deliberately claimed
    # learned in a later book: reveal-planned: true suppresses the check.
    b2 = library_books[1]
    p = b2 / "kb" / "knowledge" / "knowledge-academy.md"
    p.write_text(p.read_text(encoding="utf-8").replace(
        "audience-learned-in: 3:chapter-01",
        "audience-learned-in: 3:chapter-01\nreveal-planned: true"),
        encoding="utf-8", newline="\n")
    _, fs = _library_findings_from(library_engine, b2)
    assert not any(k.startswith("series:knowledge-anachronism")
                   for k in _keys(fs))


def test_bootstrap_apply_seeds_established_in_from_provenance(
        library, library_engine, library_books):
    # The bible is engine-write-only, so bootstrap --apply must seed
    # established-in from the kb provenance frontmatter; otherwise the
    # do-not-re-explain register, open-thread-carry, and the handoff
    # register stay permanently empty (spec 4.2).
    b2 = library_books[1]
    (library / "reports").mkdir(exist_ok=True)
    plan = library / "reports" / "bootstrap-plan-est.md"
    plan.write_text(
        "---\napproved: true\nkind: bootstrap-plan\nbook_ordinal: 2\n"
        "---\n\n## Exact matches (auto-join)\n\n"
        "- entity: promise-vault\n  kind: promises\n  tier: exact\n"
        "  series_id: promise:the-vault-promise\n\n"
        "## Alias matches (auto-join, series:id-mismatch advisory)\n\n"
        "(none)\n\n## [?] Ambiguity rows (human resolution required)\n\n"
        "(none)\n", encoding="utf-8", newline="\n")
    r = library_engine("bootstrap", "--root", str(library), "--apply", plan,
                       str(b2))
    assert r.returncode == 0, r.stderr
    bible = json.loads((library / "series" / "bible.json").read_text(
        encoding="utf-8"))
    est = bible["entities"]["promise:the-vault-promise"]["established-in"]
    assert "2:chapter-01" in est


def test_author_words_quoting_is_preserved_verbatim(library, library_engine):
    # Words that genuinely begin or end with a quote character are content:
    # only the plan format's single symmetric wrapper pair is unquoted.
    (library / "reports").mkdir(exist_ok=True)
    plan = library / "reports" / "retcon-plan-verbatim.md"
    plan.write_text(
        "---\napproved: true\nbook_ordinal: 2\n---\n\n## Rows\n\n"
        "- entity: char:lena-popescu\n  field: status\n"
        '  new_by_book: {"2": "alive"}\n'
        '  author_words: ""She said she is fine.""\n',
        encoding="utf-8", newline="\n")
    r = library_engine("retcon", "--root", ".", "--apply", str(plan))
    assert r.returncode == 0, r.stderr
    row = json.loads((library / "series" / "retcons.jsonl").read_text(
        encoding="utf-8").strip().splitlines()[-1])
    assert row["author_words"] == '"She said she is fine."'


# ---------------------------------------------------------------------------
# T9 second bullet: book-scope exemptions are invisible to library commands
# ---------------------------------------------------------------------------

def test_book_scope_exemptions_never_read_or_written_by_library(
        library, library_engine, library_books):
    # spec 17 T9: a kb/exemptions.json entry for an id that also fires as a
    # series finding must NOT suppress the series finding (series exemptions
    # live and die in the library, spec 6/16-L3), and library commands must
    # never read or write the book's exemption file.
    b2 = library_books[1]
    p = b2 / "kb" / "exemptions.json"
    doc = {
        "schema_version": 1,
        "exemptions": [{
            "key": "series:canon-divergence:char:lena-popescu:status:2",
            "status": "active",
            "reason": "book-local dismissal of a series finding id",
        }],
    }
    p.write_text(json.dumps(doc, indent=2) + "\n", encoding="utf-8",
                 newline="\n")
    before = p.read_bytes()
    # the series finding still fires: book-scope exemptions are not read
    _, fs = _library_findings_from(library_engine, b2)
    assert "series:canon-divergence:char:lena-popescu:status:2" in _keys(fs)
    assert p.read_bytes() == before
    # link / unlink / retcon --apply leave the file byte-identical
    assert library_engine("unlink", "--root", ".", str(b2)).returncode == 0
    assert library_engine("link", "--root", ".", str(b2)).returncode == 0
    assert p.read_bytes() == before
    (library / "reports").mkdir(exist_ok=True)
    plan = library / "reports" / "retcon-plan-t9.md"
    plan.write_text(
        "---\napproved: true\nbook_ordinal: 2\n---\n\n## Rows\n\n"
        "- entity: char:lena-popescu\n  field: status\n"
        '  new_by_book: {"2": "grieving"}\n'
        '  author_words: "Confirmed as written."\n',
        encoding="utf-8", newline="\n")
    assert library_engine("retcon", "--root", ".", "--apply",
                          str(plan)).returncode == 0
    assert p.read_bytes() == before


# ---------------------------------------------------------------------------
# Repair-sweep round 2: BOM tolerance, UTF-8 streams, sidecars, and flow maps
# ---------------------------------------------------------------------------

def test_bom_kb_entity_joins_fully(library, library_engine, library_books):
    """A BOM must not hide an exact-name match or leave a half-join."""
    b2 = library_books[1]
    p = b2 / "kb" / "characters" / "character-maria.md"
    p.write_bytes(b"\xef\xbb\xbf" + p.read_bytes())

    r = library_engine("bootstrap", "--root", str(library), str(b2))
    assert r.returncode == 1, r.stderr
    plan = _latest_plan(library, "bootstrap-plan-")
    body = plan.read_text(encoding="utf-8")
    exact = body.split("## Alias matches", 1)[0]
    ambiguity = body.split("## [?] Ambiguity rows", 1)[1]
    assert "- entity: character-maria" in exact
    assert "- entity: character-maria" not in ambiguity

    body = body.replace("approved: false", "approved: true")
    body = _fill_ambiguities(
        body, "__no_selected_row__", "local", "unused",
        "All remaining ambiguous rows stay book-local.")
    plan.write_text(body, encoding="utf-8", newline="\n")
    r = library_engine("bootstrap", "--root", str(library), "--apply",
                       str(plan), str(b2))
    assert r.returncode == 0, r.stderr
    assert "series-id: char:maria-popescu" in p.read_text(encoding="utf-8")

    # The fixture has unrelated baseline findings; none may be an id-mismatch
    # for the entity that was joined from the BOM'd file.
    r = library_engine("validate", "--root", str(library))
    assert r.returncode != 2, r.stderr
    findings = [json.loads(line) for line in r.stdout.splitlines()
                if line.startswith("{")]
    assert not any(
        f.get("technique") == "id-mismatch"
        and "character-maria" in str(f.get("location", {}))
        for f in findings)


def test_bootstrap_apply_refuses_kb_file_without_frontmatter(
        library, library_engine, library_books):
    """A malformed joined file fails before the bible or earlier rows mutate."""
    b2 = library_books[1]
    p = b2 / "kb" / "characters" / "character-nofm.md"
    p.write_text("Just prose, no frontmatter.\n", encoding="utf-8",
                 newline="\n")
    (library / "reports").mkdir(exist_ok=True)
    plan = library / "reports" / "bootstrap-plan-nofm.md"
    plan.write_text(
        "---\napproved: true\nkind: bootstrap-plan\nbook_ordinal: 2\n"
        "---\n\n## Exact matches (auto-join)\n\n"
        "- entity: character-nofm\n  kind: characters\n  tier: exact\n"
        "  series_id: char:uncle-radu\n\n"
        "## Alias matches (auto-join, series:id-mismatch advisory)\n\n"
        "(none)\n\n## [?] Ambiguity rows (human resolution required)\n\n"
        "(none)\n", encoding="utf-8", newline="\n")

    r = library_engine("bootstrap", "--root", str(library), "--apply",
                       str(plan), str(b2))
    assert r.returncode == 2
    assert "cannot inject series-id into" in r.stderr
    assert "series-id:" not in p.read_text(encoding="utf-8")
    bible = json.loads((library / "series" / "bible.json").read_text(
        encoding="utf-8"))
    assert "2" not in bible["entities"]["char:uncle-radu"]["fields"][
        "status"]["by-book"]


def test_engine_stdout_is_utf8_without_pythonioencoding(library):
    """Piped library output remains UTF-8 on a platform ANSI codepage."""
    env = dict(os.environ)
    env.pop("PYTHONIOENCODING", None)
    env.pop("PYTHONUTF8", None)
    r = subprocess.run(
        [sys.executable, str(PLUGIN_ROOT / "scripts" / "library.py"),
         "state", "--root", str(library), "--card-line",
         str(library.parent / "book-1")],
        cwd=str(library), env=env, capture_output=True, timeout=120)
    assert r.returncode == 0, r.stderr
    output = r.stdout.decode("utf-8")
    assert "—" in output


def test_bom_in_library_json_files_is_tolerated(library, library_engine):
    """BOM'd manifest, bible, and JSONL remain readable by read-only commands."""
    for rel in ("library.json", "series/bible.json", "series/retcons.jsonl"):
        path = library / rel
        path.write_bytes(b"\xef\xbb\xbf" + path.read_bytes())

    r = library_engine("validate", "--root", str(library))
    assert r.returncode != 2, r.stderr
    r = library_engine("state", "--root", str(library),
                       str(library.parent / "book-1"))
    assert r.returncode == 0, r.stderr


def test_bom_sidecar_is_not_misdiagnosed_as_stale(
        library, library_engine, library_books):
    """The common BOM sidecar case parses normally instead of becoming stale."""
    b2 = library_books[1]
    path = b2 / ".vellum" / "series-link.json"
    path.write_bytes(b"\xef\xbb\xbf" + path.read_bytes())
    r = library_engine("validate", "--root", str(library))
    findings = [json.loads(line) for line in r.stdout.splitlines()
                if line.startswith("{")]
    uuid = "3f2c9a1e-2222-4aaa-9bbb-000000000002"
    keys = _keys(findings)
    assert "series:sidecar-unreadable:" + uuid not in keys
    assert "series:half-linked:" + uuid not in keys
    assert not any("stale series-link sidecar" in f.get("issue", "")
                   for f in findings)


def test_unreadable_sidecar_reports_distinct_finding_and_is_repairable(
        library, library_engine, library_books):
    """Malformed JSON is reported as unreadable, then validate --fix repairs it."""
    b2 = library_books[1]
    path = b2 / ".vellum" / "series-link.json"
    path.write_text("{ not json\n", encoding="utf-8", newline="\n")
    uuid = "3f2c9a1e-2222-4aaa-9bbb-000000000002"

    r = library_engine("validate", "--root", str(library))
    findings = [json.loads(line) for line in r.stdout.splitlines()
                if line.startswith("{")]
    keys = _keys(findings)
    assert "series:sidecar-unreadable:" + uuid in keys
    assert not any("stale series-link sidecar" in f.get("issue", "")
                   for f in findings)

    r = library_engine("validate", "--root", str(library), "--fix")
    assert r.returncode != 2, r.stderr
    assert json.loads(path.read_text(encoding="utf-8"))["book_uuid"] == uuid
    # findings are computed before the fix runs, so a clean re-check proves
    # the repair cleared the unreadable sidecar
    r = library_engine("validate", "--root", str(library))
    findings = [json.loads(line) for line in r.stdout.splitlines()
                if line.startswith("{")]
    assert "series:sidecar-unreadable:" + uuid not in _keys(findings)


def test_flow_map_unquotes_keys_and_preserves_quoted_commas():
    """resolution_notes flow maps must survive commas inside quoted values."""
    scripts = str(PLUGIN_ROOT / "scripts")
    if scripts not in sys.path:
        sys.path.insert(0, scripts)
    from vellum_lib import util

    fm, body, _ = util.parse_frontmatter(
        "---\nresolution_notes: {\"char-lena\": \"note one, with comma\", "
        "\"char-radu\": \"plain\"}\n---\n\nBody.\n")
    assert fm["resolution_notes"] == {
        "char-lena": "note one, with comma", "char-radu": "plain"}
    assert body == "\nBody.\n"


def test_bootstrap_apply_accepts_comma_bearing_resolution_notes(
        library, library_engine, library_books):
    """Frontmatter resolution_notes supplies fallback notes end to end."""
    b2 = library_books[1]
    r = library_engine("bootstrap", "--root", str(library), str(b2))
    assert r.returncode == 1, r.stderr
    plan = _latest_plan(library, "bootstrap-plan-")
    body = plan.read_text(encoding="utf-8")
    body = body.replace("approved: false", "approved: true")
    body = body.replace(
        "resolution_notes: {}",
        'resolution_notes: {"character-vegg": "Vegg stays local, one-off.", '
        '"promise-bursary": "Paid off, keep it local, end of story.", '
        '"knowledge-city-map": "The map is local, by design."}')

    # Resolve every ambiguity as local while deliberately leaving each row's
    # author_words empty, forcing the flow-map fallback lookup.
    lines = []
    in_ambiguity = False
    for line in body.split("\n"):
        if line.startswith("## "):
            in_ambiguity = "Ambiguity" in line or "[?]" in line
        if in_ambiguity and line.strip() == "resolution:":
            lines.append("  resolution: local")
        else:
            lines.append(line)
    plan.write_text("\n".join(lines), encoding="utf-8", newline="\n")

    r = library_engine("bootstrap", "--root", str(library), "--apply",
                       str(plan), str(b2))
    assert r.returncode == 0, r.stderr
    assert "series-id: char:maria-popescu" in (
        b2 / "kb" / "characters" / "character-maria.md"
    ).read_text(encoding="utf-8")
