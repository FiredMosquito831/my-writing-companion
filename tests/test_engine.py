# Vellum engine suite (design-spec.md section 14).
"""Engine tests against tests/fixtures/sample-project — a fixture project
seeded with one instance of every deterministic error class. Each test
asserts the EXACT expected finding keys, turning the engine test from smoke
into specification. Error classes covered (spec 14):
dead-character reappearance; promise planted after payoff; unfired setup past
target-by; dormant promise; POV-not-in-cast; prop custody drift; knowledge
learned-in violation; clock non-monotonicity; schema violation;
frontmatter-incomplete; hand-edited state (hash mismatch); exemption active
vs stale; word-band violation."""
import json

import pytest

# The exact key set `ledger check` must emit for the fixture project.
EXPECTED_LEDGER_KEYS = {
    "continuity:character-old-tom",                       # dead-character reappearance
    "continuity:promise-late-payoff-ordering",            # planted after payoff
    "continuity:promise-overdue-setup-overdue",           # unfired past target-by
    "continuity:promise-dormant-thread-dormant",          # dormant promise
    "continuity:promise-overdue-setup-dormant",           # (same dormant rule)
    "continuity:question-bad-state-state",                # question state
    "continuity:chapter-02-pov-not-in-cast",              # POV-not-in-cast
    "frontmatter:chapter-04",                             # frontmatter-incomplete
    "continuity:chapter-04-pov-not-in-cast",              # (missing characters + pov)
    "continuity:prop-destroyed-lantern-custody",          # prop custody drift
    "continuity:knowledge-bad-learned-learned-in",        # knowledge learned-in violation
    "continuity:clock-debt-run",                          # clock non-monotonicity
    "continuity:chapter-06-verbatim",                     # outline-verbatim missing
}


def _keys(findings):
    return {f["key"] for f in findings}


# ---------------------------------------------------------------------------
# ledger check
# ---------------------------------------------------------------------------

def test_ledger_check_emits_exact_error_class_keys(findings, engine):
    r = engine("ledger", "check")
    assert r.returncode == 1, r.stderr
    keys = _keys(findings("ledger", "check"))
    assert keys == EXPECTED_LEDGER_KEYS


def test_ledger_check_mentions_exempted_mentions_clean(findings, engine):
    # character-old-tom appears in chapter-01's characters too — but chapter-01
    # is before died-in (chapter-01), so only chapter-03 fires. mentions: are
    # exempt everywhere (character-vess is only ever mentioned).
    fs = findings("ledger", "check")
    dead = [f for f in fs if f["technique"] == "dead-character"]
    assert [f["location"]["file"] for f in dead] == ["manuscript/chapters/chapter-03.md"]


# ---------------------------------------------------------------------------
# bible validate / links / reindex
# ---------------------------------------------------------------------------

def test_bible_validate_schema_violation(findings, engine):
    r = engine("bible", "validate")
    assert r.returncode == 1
    fs = findings("bible", "validate")
    keys = _keys(fs)
    # character-bad-schema has status: undead (invalid enum)
    assert "canon:character-bad-schema-schema" in keys
    schema = [f for f in fs if f["key"] == "canon:character-bad-schema-schema"]
    assert schema[0]["severity"] == "blocker"
    assert "undead" in schema[0]["issue"]


def test_bible_validate_clean_entities_pass(findings, engine):
    fs = findings("bible", "validate")
    # No schema findings on the well-formed entities.
    for f in fs:
        assert "character-mira-tarn" not in f["key"]
        assert "promise-ring-of-oath-schema" not in f["key"]
        assert "prop-destroyed-lantern-schema" not in f["key"]


def test_bible_links_reports_only_references(engine, findings):
    r = engine("bible", "links")
    assert r.returncode == 1
    fs = findings("bible", "links")
    assert fs, "fixture has broken references (character-ghost-ref)"
    assert all(f["technique"] == "broken-reference" for f in fs)
    assert any("character-ghost-ref" in f["issue"] for f in fs)


def test_bible_reindex_writes_registries_and_repairs(engine, project):
    (project / "kb" / "characters" / "_index.md").unlink(missing_ok=True)
    # Hand-edit derived state first: reindex must repair it. The fixture
    # leaves chapter-06 accepted, so state check still reports pending_capture
    # (a source fact, not a hash problem) — the hand-edit itself is repaired.
    card = project / "state" / "state-card.md"
    card.write_text("hand-edited garbage\n", encoding="utf-8")
    r = engine("bible", "reindex")
    assert r.returncode in (0, 1), r.stderr
    idx = (project / "kb" / "characters" / "_index.md").read_text(encoding="utf-8")
    assert "character-mira-tarn" in idx
    r2 = engine("state", "check")
    assert r2.returncode == 2
    assert "state:hand-edited" not in r2.stderr  # hash repaired by reindex
    assert "pending_capture" in r2.stderr  # remaining invariant is a source fact


# ---------------------------------------------------------------------------
# state rebuild / check / hash verification
# ---------------------------------------------------------------------------

def test_state_rebuild_creates_derived_files(engine, project):
    r = engine("state", "rebuild")
    assert r.returncode == 0, r.stderr
    assert (project / "state" / "_tracking-state.json").exists()
    assert (project / "state" / "state-card.md").exists()
    assert (project / "state" / "_derived-hashes.json").exists()
    card = (project / "state" / "state-card.md").read_text(encoding="utf-8")
    for section in ("## Story position", "## Open promises & questions",
                    "## Active cast state", "## Knowledge boundaries",
                    "## Props & clock", "## Next beats with word quotas",
                    "## Flags"):
        assert section in card


def test_state_check_flags_pending_capture(engine, project):
    engine("state", "rebuild")
    r = engine("state", "check")
    # chapter-06 sits at status: accepted -> pending_capture is true.
    assert r.returncode == 2
    assert "pending_capture" in (r.stderr or "")


def test_state_check_detects_hand_edited_state(engine, project):
    engine("state", "rebuild")
    # Make the transaction clean, then tamper with a hash-verified file.
    ch6 = project / "manuscript" / "chapters" / "chapter-06.md"
    ch6.write_text(ch6.read_text(encoding="utf-8").replace(
        "status: accepted", "status: final"), encoding="utf-8")
    r = engine("state", "rebuild")
    assert r.returncode == 0
    assert engine("state", "check").returncode == 0
    card = project / "state" / "state-card.md"
    card.write_text(card.read_text(encoding="utf-8") + "\nHand edit.\n",
                    encoding="utf-8")
    r = engine("state", "check")
    assert r.returncode == 2
    assert "state:hand-edited" in (r.stderr or "")


def test_state_card_within_size_cap(engine, project):
    r = engine("state", "rebuild")
    assert r.returncode == 0, r.stderr
    card = (project / "state" / "state-card.md")
    assert card.stat().st_size <= 12 * 1024


def test_state_check_pivotal_acceptance_requires_blind_artifact(engine, project):
    # Gate 2 acceptance precondition (spec 10.1): state check refuses while a
    # pivotal chapter sits at status: accepted without its blind artifact
    # (verdict != LOST) — mechanically, not just by muse discipline.
    engine("state", "rebuild")
    outline = project / "work" / "outline" / "chapter-06.md"
    outline.write_text(outline.read_text(encoding="utf-8").replace(
        "pivotal: false", "pivotal: true"), encoding="utf-8")
    r = engine("state", "check")
    assert r.returncode == 2
    assert "no blind-reader artifact" in (r.stderr or "")
    blind = project / "work" / "critique-reports" / "blind-chapter-06.md"
    blind.parent.mkdir(parents=True, exist_ok=True)
    # No transcript: the artifact's provenance binding fails (the muse
    # transcribes blind artifacts, so they must cite the blind-reader run).
    blind.write_text("---\nverdict: ENGAGED\n---\n\n> From @blind-reader\n",
                     encoding="utf-8")
    r = engine("state", "check")
    assert r.returncode == 2
    assert "provenance" in (r.stderr or "")
    tr = project / "work" / "critique-reports" / "blind-run.jsonl"
    tr.write_text('{"role":"assistant","content":"verdict: ENGAGED"}\n',
                  encoding="utf-8")
    blind.write_text(
        "---\nverdict: ENGAGED\n"
        "transcript: work/critique-reports/blind-run.jsonl\n"
        "---\n\n> From @blind-reader\n",
        encoding="utf-8")
    r = engine("state", "check")
    # artifact present, verdict != LOST, provenance intact: the pivotal
    # precondition passes; pending_capture (the open transaction) blocks now.
    assert r.returncode == 2
    assert "pending_capture" in (r.stderr or "")
    blind.write_text("---\nverdict: LOST\n---\n\nThe reader stopped.\n",
                     encoding="utf-8")
    r = engine("state", "check")
    assert r.returncode == 2
    assert "LOST" in (r.stderr or "")


def test_state_check_pivotal_precondition_binds_closeout_edit(engine, project):
    # The accepted -> final close-out edit (the guard passes the chapter as
    # target) is still bound by the pivotal precondition — it is the moment
    # the acceptance completes.
    engine("state", "rebuild")
    outline = project / "work" / "outline" / "chapter-06.md"
    outline.write_text(outline.read_text(encoding="utf-8").replace(
        "pivotal: false", "pivotal: true"), encoding="utf-8")
    ch6 = project / "manuscript" / "chapters" / "chapter-06.md"
    r = engine("state", "check", str(ch6))
    assert r.returncode == 2
    assert "no blind-reader artifact" in (r.stderr or "")


def test_state_check_pending_chapter_closeout_edit_allowed(engine, project):
    # The edit that closes the pending chapter's own transaction (status:
    # final) is part of that transaction: state check with that target must
    # not demand the close-out already be complete.
    engine("state", "rebuild")
    ch6 = project / "manuscript" / "chapters" / "chapter-06.md"
    r = engine("state", "check", str(ch6))
    assert r.returncode == 0, r.stderr


def test_state_check_edit_to_in_progress_chapter_allowed(engine, project):
    # The half-committed invariant fires on new-chapter starts only: with
    # chapter 7's outline approved early, an edit to the in-progress chapter
    # (target passed by the guard) is a revision, not a start.
    engine("state", "rebuild")
    ch6 = project / "manuscript" / "chapters" / "chapter-06.md"
    ch6.write_text(ch6.read_text(encoding="utf-8").replace(
        "status: accepted", "status: revised"), encoding="utf-8")
    engine("state", "rebuild")
    out7 = project / "work" / "outline" / "chapter-07.md"
    out7.parent.mkdir(parents=True, exist_ok=True)
    out7.write_text("---\nchapter: 7\ntitle: \"T\"\napproved: true\n"
                    "pivotal: false\nword-target: 3200\nverbatim: []\n---\n\n"
                    "## Beats\n1. beat — quota 3200\n", encoding="utf-8")
    # A new-chapter start (no target known) still blocks: ch6 is not closed.
    r = engine("state", "check")
    assert r.returncode == 2
    assert "half-committed" in (r.stderr or "")
    # An edit to the in-progress chapter itself passes.
    r = engine("state", "check", str(ch6))
    assert r.returncode == 0, r.stderr


def test_state_check_voice_debt_gate_blocks(engine, project):
    # Opt-in gate (kb/project-config.json voice_debt_gate: true): open
    # tier-1 debt in work/voice-debt.json blocks the loop instead of
    # accruing silently.
    ch6 = project / "manuscript" / "chapters" / "chapter-06.md"
    ch6.write_text(ch6.read_text(encoding="utf-8").replace(
        "status: accepted", "status: final"), encoding="utf-8")
    engine("state", "rebuild")
    cfg = project / "kb" / "project-config.json"
    doc = json.loads(cfg.read_text(encoding="utf-8"))
    doc["voice_debt_gate"] = True
    cfg.write_text(json.dumps(doc, indent=2), encoding="utf-8")
    assert engine("state", "check").returncode == 0  # no open debt yet
    debt = project / "work" / "voice-debt.json"
    debt.write_text(json.dumps({"schema_version": 1, "items": [
        {"id": "debt-06-001", "chapter": "chapter-06", "line": 3,
         "match": "delve", "type": "tier1", "status": "open",
         "found_at": "2026-09-09T00:00:00Z"}]}), encoding="utf-8")
    r = engine("state", "check")
    assert r.returncode == 2
    assert "voice debt gate" in (r.stderr or "")


# ---------------------------------------------------------------------------
# wordcount + band
# ---------------------------------------------------------------------------

def test_wordcount_write_updates_frontmatter(engine, project):
    r = engine("wordcount", "--write")
    assert r.returncode == 1  # band findings exist by design
    ch1 = (project / "manuscript" / "chapters" / "chapter-01.md")
    text = ch1.read_text(encoding="utf-8")
    import re
    m = re.search(r"^word-count: (\d+)$", text, re.MULTILINE)
    assert m and int(m.group(1)) > 200


def test_wordcount_band_finding_exact_key(findings, engine):
    fs = findings("wordcount")
    keys = _keys(fs)
    # fixture chapters are ~280 words against a 3200 target -> band violations
    assert "band:chapter-01" in keys
    band = [f for f in fs if f["key"] == "band:chapter-01"][0]
    assert band["technique"] == "word-band"
    assert "prose-writing.md" in band["issue"]


# ---------------------------------------------------------------------------
# knowledge --as-of (incl. dramatic irony)
# ---------------------------------------------------------------------------

def test_knowledge_as_of_filters_by_chapter(engine, project):
    # Vess learned the fact in chapter-05: not known as of chapter-04.
    r = engine("knowledge", "character-vess", "--as-of", "4")
    assert r.returncode == 0
    assert "no matching knowledge" in r.stdout
    r = engine("knowledge", "character-vess", "--as-of", "5")
    assert "harbor manifests" in r.stdout
    assert "[knows]" in r.stdout


def test_knowledge_audience_view(engine, project):
    r = engine("knowledge", "character-mira-tarn", "--as-of", "6",
               "--audience")
    assert r.returncode == 0
    assert "audience knows" in r.stdout
    assert "does not know" in r.stdout  # dramatic irony: mira doesn't hold it


# ---------------------------------------------------------------------------
# dismiss + exemption semantics (active drops, stale re-arms once)
# ---------------------------------------------------------------------------

def test_dismiss_active_drops_finding(engine, project, findings):
    r = engine("dismiss", "continuity:clock-debt-run",
               "--reason", "The debt clock runs backwards on purpose.")
    assert r.returncode == 0, r.stderr
    keys = _keys(findings("ledger", "check"))
    assert "continuity:clock-debt-run" not in keys
    doc = json.loads((project / "kb" / "exemptions.json").read_text(encoding="utf-8"))
    entry = [e for e in doc["exemptions"] if e["key"] == "continuity:clock-debt-run"][0]
    assert entry["status"] == "active"
    assert entry["reason"] == "The debt clock runs backwards on purpose."
    # entity basis recorded so bible validate can flip it to stale
    assert entry.get("entity") == "kb/clock.md" or entry.get("entity") is None


def test_dismiss_refuses_duplicate_active_key(engine, project):
    r1 = engine("dismiss", "continuity:clock-debt-run", "--reason", "one")
    assert r1.returncode == 0
    r2 = engine("dismiss", "continuity:clock-debt-run", "--reason", "two")
    assert r2.returncode == 2


def test_dismiss_requires_reason(engine, project):
    r = engine("dismiss", "continuity:clock-debt-run")
    assert r.returncode == 2


def test_stale_exemption_re_arms_finding(engine, project, findings):
    doc = json.loads((project / "kb" / "exemptions.json").read_text(encoding="utf-8"))
    doc["exemptions"].append({
        "key": "continuity:clock-debt-run", "reason": "stale already",
        "dismissed_at": "2026-01-01", "chapter": "chapter-06",
        "status": "stale", "stale_note": None,
    })
    (project / "kb" / "exemptions.json").write_text(
        json.dumps(doc, indent=2), encoding="utf-8")
    fs = findings("ledger", "check")
    stale = [f for f in fs if f["key"] == "continuity:clock-debt-run"]
    assert stale, "a stale exemption re-arms the finding once"
    assert "re-armed" in stale[0]["issue"] or "previously dismissed" in stale[0]["issue"]


# ---------------------------------------------------------------------------
# style stats + baseline
# ---------------------------------------------------------------------------

def test_style_stats_emits_profile(engine, project):
    r = engine("style", "stats", "manuscript/chapters/chapter-01.md")
    assert r.returncode == 0, r.stderr
    assert "measured per-1k voice profile" in r.stdout
    for metric in ("em-dash-per-1k", "hedge-per-1k", "tier1-hit-per-1k",
                   "dialogue-ratio", "ttr", "burstiness"):
        assert f"| {metric} |" in r.stdout


def test_style_stats_baseline_drift_report(engine, project):
    r = engine("style", "stats", "manuscript/chapters/chapter-01.md",
               "--baseline")
    assert r.returncode == 0, r.stderr
    assert "drift report" in r.stdout
    assert "restoration needed" in r.stdout or "within band" in r.stdout


# ---------------------------------------------------------------------------
# pack
# ---------------------------------------------------------------------------

def test_pack_emits_paths_and_inline(engine, project):
    engine("state", "rebuild")  # state card must exist for the pack
    r = engine("pack", "chapter-06")
    assert r.returncode == 0, r.stderr
    doc = json.loads(r.stdout)
    assert set(doc.keys()) == {"paths", "inline"}
    assert "state/state-card.md" in doc["paths"]
    assert "work/outline/chapter-06.md" in doc["paths"]
    assert "manuscript/chapters/chapter-05.md" in doc["paths"]  # prev-chapter tail
    assert any(p.startswith("kb/characters/") for p in doc["paths"])
    assert "previous-chapter tail (manuscript/chapters/chapter-05.md)" in doc["inline"]


# ---------------------------------------------------------------------------
# debt
# ---------------------------------------------------------------------------

def test_debt_list_and_clear(engine, project):
    debt = project / "work" / "voice-debt.json"
    debt.write_text(json.dumps({"schema_version": 1, "items": [
        {"id": "debt-07-001", "chapter": "chapter-07", "line": 3,
         "match": "delve", "type": "tier1", "status": "open",
         "found_at": "2026-09-09T00:00:00Z"}]}), encoding="utf-8")
    r = engine("debt", "list")
    assert "debt-07-001" in r.stdout
    r = engine("debt", "clear", "debt-07-001")
    assert r.returncode == 0, r.stderr
    doc = json.loads(debt.read_text(encoding="utf-8"))
    assert doc["items"][0]["status"] == "cleared"


# ---------------------------------------------------------------------------
# readiness (incl. blind-artifact cross-check + report consistency)
# ---------------------------------------------------------------------------

def test_readiness_lists_missing_items(engine, project):
    r = engine("readiness")
    assert r.returncode == 1
    out = r.stderr
    # pivotal=false in the fixture, but statuses are not all final, frontmatter
    # is incomplete, and no readiness report exists.
    assert "readiness-report.md" in out
    assert "frontmatter missing" in out


def test_readiness_validates_report_internal_consistency(engine, project):
    engine("state", "rebuild")
    report = project / "work" / "critique-reports" / "readiness-report.md"
    report.parent.mkdir(parents=True, exist_ok=True)
    # internally inconsistent: score 9.5 vs axis mean 8.0
    report.write_text(
        "---\nverdict: PASS\nscore: 9.5\n"
        "axes: {voice: 8, structure: 8, depth: 8, specificity: 8, reader: 8}\n"
        "put_down_points: []\nread_at: 2026-09-09\nreaders: 4\n---\n\n"
        "Report body.\n", encoding="utf-8")
    r = engine("readiness")
    assert r.returncode == 1
    assert "internally inconsistent" in r.stderr


def test_readiness_pass_rule_enforced(engine, project):
    engine("state", "rebuild")
    report = project / "work" / "critique-reports" / "readiness-report.md"
    report.parent.mkdir(parents=True, exist_ok=True)
    # consistent PASS shape but axis 6 < 7 floor
    report.write_text(
        "---\nverdict: PASS\nscore: 7.6\n"
        "axes: {voice: 7, structure: 6, depth: 8, specificity: 8, reader: 9}\n"
        "put_down_points: []\nread_at: 2026-09-09\nreaders: 4\n---\n\n"
        "Report body.\n", encoding="utf-8")
    r = engine("readiness")
    assert r.returncode == 1
    assert "below 7" in r.stderr


def test_readiness_pivotal_without_blind_artifact(engine, project):
    engine("state", "rebuild")
    outline = project / "work" / "outline" / "chapter-06.md"
    outline.write_text(outline.read_text(encoding="utf-8").replace(
        "pivotal: false", "pivotal: true"), encoding="utf-8")
    r = engine("readiness")
    assert "no blind-reader artifact" in r.stderr


def test_readiness_pivotal_lost_verdict_blocks(engine, project):
    engine("state", "rebuild")
    outline = project / "work" / "outline" / "chapter-06.md"
    outline.write_text(outline.read_text(encoding="utf-8").replace(
        "pivotal: false", "pivotal: true"), encoding="utf-8")
    blind = project / "work" / "critique-reports" / "blind-chapter-06.md"
    blind.write_text("---\nverdict: LOST\n---\n\nThe reader stopped.\n",
                     encoding="utf-8")
    r = engine("readiness")
    assert "blind verdict is LOST" in r.stderr


def test_readiness_requires_transcript_provenance(engine, project):
    # The readiness report is muse-transcribed (subagents cannot write
    # work/critique-reports/), so a self-consistent report must still cite
    # the beta-reader run behind it: the transcript must exist and carry the
    # verdict, or the gate fails.
    engine("state", "rebuild")
    report = project / "work" / "critique-reports" / "readiness-report.md"
    report.parent.mkdir(parents=True, exist_ok=True)
    body = ("---\nverdict: PASS\nscore: 8.0\n"
            "axes: {voice: 8, structure: 8, depth: 8, specificity: 8, "
            "reader: 8}\n"
            "put_down_points: []\nread_at: 2026-09-09\nreaders: 4\n"
            "---\n\nReport body.\n")
    report.write_text(body, encoding="utf-8")
    r = engine("readiness")
    assert r.returncode == 1
    assert "transcript provenance missing" in r.stderr
    report.write_text(body.replace(
        "readers: 4\n",
        "readers: 4\ntranscript: work/critique-reports/missing-run.jsonl\n"),
        encoding="utf-8")
    r = engine("readiness")
    assert "does not exist" in r.stderr
    tr = project / "work" / "critique-reports" / "beta-run.jsonl"
    tr.write_text('{"role":"assistant","content":"verdict: REVISE"}\n',
                  encoding="utf-8")
    report.write_text(body.replace(
        "readers: 4\n",
        "readers: 4\ntranscript: work/critique-reports/beta-run.jsonl\n"),
        encoding="utf-8")
    r = engine("readiness")
    assert "contains no PASS verdict" in r.stderr
    tr.write_text('{"role":"assistant","content":"verdict: PASS"}\n',
                  encoding="utf-8")
    r = engine("readiness")
    # provenance satisfied; whatever else is missing, it is not the transcript
    assert r.returncode == 1  # fixture chapters are not all final
    assert "transcript" not in r.stderr


# ---------------------------------------------------------------------------
# export build
# ---------------------------------------------------------------------------

def test_export_build_requires_final_chapters(engine, project):
    # The fixture ships chapters 1-5 as final (ch6 is accepted) — a build
    # without --epub assembles the markdown bundle + manifest.
    r = engine("export", "build", "--out", "export/x")
    assert r.returncode == 0, r.stderr
    assert (project / "export" / "x" / "manifest.md").exists()


def test_export_build_assembles_bundle_and_manifest(engine, project):
    for i in range(1, 7):
        p = project / "manuscript" / "chapters" / ("chapter-%02d.md" % i)
        p.write_text(p.read_text(encoding="utf-8").replace(
            "status: accepted", "status: final").replace(
            "status: final\napproved", "status: final\napproved"), encoding="utf-8")
    r = engine("export", "build", "--out", "export/test", "--epub")
    assert r.returncode == 0, r.stderr
    out = project / "export" / "test"
    assert (out / "manuscript.md").exists()
    assert (out / "manifest.md").exists()
    assert (out / "manuscript.epub").exists()
    manifest = (out / "manifest.md").read_text(encoding="utf-8")
    assert "sha256" in manifest.lower() or "checksum" in manifest.lower()
    assert "urn:uuid:6f1c6e2e" in manifest  # stable identifier from kb/story.md
    # manuscript untouched
    ch1 = (project / "manuscript" / "chapters" / "chapter-01.md").read_text(
        encoding="utf-8")
    assert "word-count" in ch1  # frontmatter intact


def test_export_epub_mimetype_stored_first(engine, project):
    import zipfile
    for i in range(1, 7):
        p = project / "manuscript" / "chapters" / ("chapter-%02d.md" % i)
        p.write_text(p.read_text(encoding="utf-8").replace(
            "status: accepted", "status: final"), encoding="utf-8")
    engine("export", "build", "--out", "export/test2", "--epub")
    with zipfile.ZipFile(project / "export" / "test2" / "manuscript.epub") as z:
        assert z.namelist()[0] == "mimetype"
        assert z.read("mimetype") == b"application/epub+zip"
        assert z.read("META-INF/container.xml")
