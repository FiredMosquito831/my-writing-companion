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


def test_style_stats_baseline_accepts_both_argument_orders(engine, project):
    # v0.1.1: `--baseline` is order-insensitive. The documented order
    # (`style stats <file> --baseline`) and the hoisted order
    # (`style --baseline stats <file>`) must both parse and run.
    r1 = engine("style", "stats", "manuscript/chapters/chapter-01.md",
                "--baseline")
    assert r1.returncode == 0, r1.stderr
    assert "drift report" in r1.stdout
    r2 = engine("style", "--baseline", "stats",
                "manuscript/chapters/chapter-01.md")
    assert r2.returncode == 0, r2.stderr
    assert "drift report" in r2.stdout


# ---------------------------------------------------------------------------
# style stats --dialogue (ADD-5: per-character dialogue fingerprint)
# ---------------------------------------------------------------------------

def _write_test_chapter(project, num, fm_lines, body):
    p = project / "manuscript" / "chapters" / ("chapter-%02d.md" % num)
    p.write_text("---\n" + fm_lines + "---\n\n" + body, encoding="utf-8")
    return p


def _cast_fm(num, cast, extra=""):
    return ("title: \"D\"\nnumber: %d\nstatus: draft\n"
            "pov: character-mira-tarn\ncharacters: [%s]\nmentions: []\n"
            "promises-advanced: []\nword-target: 3200\nword-count: null\n%s"
            % (num, ", ".join(cast), extra))


MIRA_TAGGED = "\n\n".join(
    "— %s, spuse Mira." % line
    for line in ("Ai banii", "Atunci rămân aici", "Pentru odihnă",
                 "Nu mă ating", "Plecăm acum", "Bine", "Închide ușa",
                 "Mă duc înainte"))
VESS_TAGGED = "\n\n".join(
    "— %s, răspunse Vess cu răbdarea unui om care mai trecuse odată pe "
    "drumurile acestea și nu se mai grăea către nimic." % line
    for line in ("Am toate la mine", "Cât costă trecerea aici",
                 "Prea mult pentru ce avem", "Atunci așteptăm până seara",
                 "Pentru că drumul e lung", "Odihna se găsește în drum",
                 "Nimeni nu ne urmărește", "Fă cum vrei, dar repede"))


def test_style_stats_dialogue_reports_speakers(engine, project):
    _write_test_chapter(project, 7,
                        _cast_fm(7, ["character-mira-tarn",
                                     "character-vess"]),
                        MIRA_TAGGED + "\n\n" + VESS_TAGGED)
    r = engine("style", "stats", "manuscript/chapters/chapter-07.md",
               "--dialogue")
    assert r.returncode == 0, r.stderr
    assert ("dialogue manuscript/chapters/chapter-07.md: "
            "16 line(s) attributed, 0 unattributed") in r.stdout
    assert "speaker character-mira-tarn (Mira Tarn): 8 line(s)" in r.stdout
    assert "speaker character-vess (Vess): 8 line(s)" in r.stdout
    assert "mean utterance" in r.stdout
    assert "top tokens:" in r.stdout
    assert "dialogue-convergence" not in r.stdout


def test_style_stats_dialogue_excludes_unattributed_lines(engine, project):
    _write_test_chapter(project, 8,
                        _cast_fm(8, ["character-mira-tarn",
                                     "character-vess"]),
                        "— Cineva trece pe aici.\n\n"
                        "— Nicăieri nu mai e nimeni.")
    r = engine("style", "stats", "manuscript/chapters/chapter-08.md",
               "--dialogue")
    assert r.returncode == 0, r.stderr
    assert ("dialogue manuscript/chapters/chapter-08.md: "
            "0 line(s) attributed, 2 unattributed") in r.stdout
    assert "speaker character-" not in r.stdout


def test_style_stats_dialogue_quotes_convention(engine, project):
    body = ("Mira puse cana pe masă. \"Nu azi.\"\n\n"
            "Mira privea spre geam. \"Mai târziu.\"\n\n"
            "\"Nu mai ține minte,\" spuse Mira și închise ușa.")
    _write_test_chapter(project, 9,
                        _cast_fm(9, ["character-mira-tarn"]), body)
    r = engine("style", "stats", "manuscript/chapters/chapter-09.md",
               "--dialogue")
    assert r.returncode == 0, r.stderr
    assert ("dialogue manuscript/chapters/chapter-09.md: "
            "3 line(s) attributed, 0 unattributed") in r.stdout
    assert "speaker character-mira-tarn (Mira Tarn): 3 line(s)" in r.stdout


def test_style_stats_dialogue_convergence_flag(findings, engine, project):
    # Same-shape lines from both speakers: both mechanical idiolect axes
    # collapse -> the pairwise convergence flag fires (report-only, exit 0).
    lines = []
    for _ in range(8):
        lines.append("— Nu am văzut nimic aici, spuse Mira.")
        lines.append("— Nu am găsit nimic aici, răspunse Vess.")
    _write_test_chapter(project, 10,
                        _cast_fm(10, ["character-mira-tarn",
                                      "character-vess"]),
                        "\n\n".join(lines))
    r = engine("style", "stats", "manuscript/chapters/chapter-10.md",
               "--dialogue")
    assert r.returncode == 0, r.stderr
    fs = [f for f in findings("style", "stats",
                              "manuscript/chapters/chapter-10.md",
                              "--dialogue")
          if f["technique"] == "dialogue-convergence"]
    assert len(fs) == 1
    f = fs[0]
    assert f["key"] == "voice:dialogue-convergence-mira-tarn-vess"
    assert f["severity"] == "suggestion"
    assert f["audit"] == "voice"
    assert "blind attribution test" in f["issue"]


# ---------------------------------------------------------------------------
# style stats --morphology (ADD-6: Romanian tense/person morphology scan)
# ---------------------------------------------------------------------------

def test_style_stats_morphology_clean_present_is_silent(engine, project):
    # Declared present/third and the narration obeys: distribution printed,
    # zero findings.
    body = ("Orașul se trezește încet. Lena traversează piața și observă "
            "tarabele abia montate. Vânzătorii glumesc între ei și "
            "aranjează merele în piramide. Un vânt rece coboară dinspre "
            "vale și împrăștie mirosul de cafea. Ea se oprește la colț și "
            "verifică adresa pe bilețel.\n\n"
            "Clădirea dinspre est adăpostește librăria veche. Înăuntru, "
            "directorul deschide registrul și întâmpină vizitatorii cu o "
            "formalitate uscată. Lena anunță scopul vizitei și așteaptă "
            "răspunsul. Directorul îi explică regulile casei și îi arată "
            "sala de lectură. Ea își notează totul și mulțumește la "
            "plecare. Ea reprojează traseul înapoi și desenează rapid "
            "schița fațadei.")
    _write_test_chapter(project, 7,
                        _cast_fm(7, ["character-mira-tarn"],
                                 "tense: present\npov-person: third\n"),
                        body)
    r = engine("style", "stats", "manuscript/chapters/chapter-07.md",
               "--morphology")
    assert r.returncode == 0, r.stderr
    assert ("morphology manuscript/chapters/chapter-07.md: present=") \
        in r.stdout
    assert "narration person 1st=" in r.stdout
    assert "{" not in r.stdout  # silent when clean: no finding lines


def test_style_stats_morphology_flags_tense_drift(findings, engine, project):
    # Declared present, narration in perfect compus: voice:tense-drift.
    body = ("Mira a mers până la pod. A așteptat un ceas întreg. A văzut "
            "lumini pe apă și a pornit spre oraș. Nu a găsit pe nimeni "
            "acolo. A revenit acasă târziu și a adormit devreme.\n\n"
            "A visat lucruri vechi toată noaptea. Dimineața a plecat fără "
            "să spună ceva. A promis că va reveni și a adus cheia înapoi.")
    _write_test_chapter(project, 8,
                        _cast_fm(8, ["character-mira-tarn"],
                                 "tense: present\n"),
                        body)
    r = engine("style", "stats", "manuscript/chapters/chapter-08.md",
               "--morphology")
    assert r.returncode == 0, r.stderr
    fs = findings("style", "stats", "manuscript/chapters/chapter-08.md",
                  "--morphology")
    keys = {f["key"] for f in fs}
    assert "voice:tense-drift" in keys
    drift = [f for f in fs if f["key"] == "voice:tense-drift"][0]
    assert drift["severity"] == "suggestion"
    assert "tense:skip valve" in drift["issue"]


def test_style_stats_morphology_flags_person_drift(findings, engine, project):
    # Declared third-person narration, narration speaks in 1st person:
    # voice:person-drift.
    body = ("Eu deschid ușa și mă opresc în prag. Nu-mi place liniștea "
            "din casă. Mi-e teamă de ce urmează și nu-mi vine să cred că "
            "am ajuns aici. Eu prefer să merg încet, dar mă mișc repede "
            "când cineva mă cheamă.\n\n"
            "Seara eu continui desenul și îmi verific liniile de sus până "
            "jos. Nu mă opresc până târziu. Eu beau o cafea și plec acasă.")
    _write_test_chapter(project, 9,
                        _cast_fm(9, ["character-mira-tarn"],
                                 "tense: present\npov-person: third\n"),
                        body)
    r = engine("style", "stats", "manuscript/chapters/chapter-09.md",
               "--morphology")
    assert r.returncode == 0, r.stderr
    fs = findings("style", "stats", "manuscript/chapters/chapter-09.md",
                  "--morphology")
    keys = {f["key"] for f in fs}
    assert "voice:person-drift" in keys
    assert "voice:tense-drift" not in keys  # present is dominant, no drift


def test_style_stats_morphology_honors_tense_skip_valve(engine, project):
    # The per-line tense:skip valve removes deliberate past-tense lines from
    # the scan's denominator: without the valve the chapter drifts, with it
    # the chapter is clean.
    present = ("Orașul se trezește devreme. Vânzătorii glumesc între ei. "
               "Lena se oprește la colț și notează adresa pe bilețel.")
    past_sentences = ("Mira a mers până la pod.", "A așteptat un ceas.",
                      "A văzut lumini pe apă.", "A pornit spre oraș.",
                      "A găsit poarta închisă.", "A revenit acasă târziu.",
                      "A adormit devreme.")
    past_lines = "\n".join(s + " <!-- tense:skip -->"
                           for s in past_sentences)
    drifted = past_lines.replace(" <!-- tense:skip -->", "")
    _write_test_chapter(project, 10,
                        _cast_fm(10, ["character-mira-tarn"],
                                 "tense: present\n"),
                        present + "\n\n" + past_lines)
    r = engine("style", "stats", "manuscript/chapters/chapter-10.md",
               "--morphology")
    assert r.returncode == 0, r.stderr
    assert "perfect-compus=0" in r.stdout
    assert "{" not in r.stdout
    _write_test_chapter(project, 10,
                        _cast_fm(10, ["character-mira-tarn"],
                                 "tense: present\n"),
                        present + "\n\n" + drifted)
    r = engine("style", "stats", "manuscript/chapters/chapter-10.md",
               "--morphology")
    assert r.returncode == 0, r.stderr
    assert "voice:tense-drift" in r.stdout


def test_style_stats_morphology_english_text_is_gated(engine, project):
    # The Romanian-confidence gate keeps the morphology pass silent on
    # non-Romanian prose: English narration tripwires the perfect-compus
    # heuristic on "a rest" / "a moment" patterns and, with a declared
    # tense, would surface spurious voice:tense-drift findings on every
    # post-write scan. Below the confidence threshold the scan reports low
    # confidence and emits no findings.
    body = ("She took a rest after lunch and made a list of the things the "
            "cast still needed for the test. The moment passed quietly and "
            "the rest of them said nothing. He set the list on the table "
            "and waited for the test to begin.\n\n"
            "The cast failed anyway. He made another list, took a rest, "
            "and told himself the next test would be the last one this "
            "town would ever get from him. Then the rain came and the "
            "list went into the fire with the rest of the papers.")
    _write_test_chapter(project, 11,
                        _cast_fm(11, ["character-mira-tarn"],
                                 "tense: present\n"),
                        body)
    r = engine("style", "stats", "manuscript/chapters/chapter-11.md",
               "--morphology")
    assert r.returncode == 0, r.stderr
    assert "no confident Romanian verb markers found" in r.stdout
    assert "perfect-compus=" not in r.stdout  # distribution not printed
    assert "{" not in r.stdout  # silent when clean: no finding lines


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


def test_readiness_accepts_self_recorded_run_stamp(engine, project):
    # v0.1.1 provenance redesign: the reader agent self-records a run stamp
    # in its report frontmatter at run time; the muse transcribes it
    # verbatim. The stamp alone (no transcript) satisfies the provenance
    # binding; a stamp naming the wrong agent or carrying a mismatched
    # verdict does not.
    engine("state", "rebuild")
    report = project / "work" / "critique-reports" / "readiness-report.md"
    report.parent.mkdir(parents=True, exist_ok=True)
    body = ("---\nverdict: PASS\nscore: 8.0\n"
            "axes: {voice: 8, structure: 8, depth: 8, specificity: 8, "
            "reader: 8}\n"
            "put_down_points: []\nread_at: 2026-09-09\nreaders: 4\n"
            "run_stamp: beta-reader PASS 2026-09-10T12:00:00Z\n"
            "---\n\nReport body.\n")
    report.write_text(body, encoding="utf-8")
    r = engine("readiness")
    assert r.returncode == 1  # fixture chapters are not all final
    assert "provenance" not in r.stderr
    assert "run_stamp" not in r.stderr
    # wrong agent in the stamp
    report.write_text(body.replace(
        "run_stamp: beta-reader", "run_stamp: cold-reader"), encoding="utf-8")
    r = engine("readiness")
    assert "must cite a beta-reader run" in r.stderr
    # stamp verdict disagrees with the report verdict
    report.write_text(body.replace(
        "run_stamp: beta-reader PASS", "run_stamp: beta-reader REVISE"),
        encoding="utf-8")
    r = engine("readiness")
    assert "internally inconsistent" in r.stderr
    # malformed stamp (no verdict / no date)
    report.write_text(body.replace(
        "run_stamp: beta-reader PASS 2026-09-10T12:00:00Z",
        "run_stamp: beta-reader"), encoding="utf-8")
    r = engine("readiness")
    assert "run_stamp" in r.stderr and "malformed" in r.stderr


def test_state_check_blind_artifact_accepts_run_stamp(engine, project):
    # The blind artifact's provenance binding accepts the reader's
    # self-recorded run stamp. The single-agent fallback qualifier is
    # author-enabled: without `blind_gate_fallback: true` in
    # kb/project-config.json the engine rejects it; with the flag it passes.
    engine("state", "rebuild")
    outline = project / "work" / "outline" / "chapter-06.md"
    outline.write_text(outline.read_text(encoding="utf-8").replace(
        "pivotal: false", "pivotal: true"), encoding="utf-8")
    blind = project / "work" / "critique-reports" / "blind-chapter-06.md"
    blind.parent.mkdir(parents=True, exist_ok=True)
    stamp = "---\nverdict: ENGAGED\nrun_stamp: %s\n---\n\n> From @blind-reader\n"
    blind.write_text(stamp % "blind-reader ENGAGED 2026-09-10T12:00:00Z",
                     encoding="utf-8")
    r = engine("state", "check")
    assert r.returncode == 2
    # provenance satisfied; the open transaction is what blocks now
    assert "pending_capture" in (r.stderr or "")
    blind.write_text(
        stamp % "blind-reader (single-agent fallback) ENGAGED "
                "2026-09-10T12:00:00Z", encoding="utf-8")
    r = engine("state", "check")
    assert r.returncode == 2
    # fallback stamp without the author's flag: provenance failure
    assert "blind artifact provenance" in (r.stderr or "")
    assert "blind_gate_fallback" in (r.stderr or "")
    # the author enables the fallback at the decision point; the artifact
    # then satisfies provenance and the open transaction is what blocks
    cfg = project / "kb" / "project-config.json"
    doc = json.loads(cfg.read_text(encoding="utf-8"))
    doc["blind_gate_fallback"] = True
    cfg.write_text(json.dumps(doc, indent=2), encoding="utf-8")
    r = engine("state", "check")
    assert r.returncode == 2
    assert "pending_capture" in (r.stderr or "")
    assert "blind_gate_fallback" not in (r.stderr or "")
    blind.write_text(
        stamp % "beta-reader ENGAGED 2026-09-10T12:00:00Z", encoding="utf-8")
    r = engine("state", "check")
    assert r.returncode == 2
    assert "must cite a blind-reader run" in (r.stderr or "")


def test_readiness_rejects_fallback_stamp_without_author_flag(engine, project):
    # The (single-agent fallback) qualifier marks self-attested provenance;
    # the engine accepts it only when the author has enabled the no-subagent
    # fallback in kb/project-config.json.
    engine("state", "rebuild")
    report = project / "work" / "critique-reports" / "readiness-report.md"
    report.parent.mkdir(parents=True, exist_ok=True)
    body = ("---\nverdict: PASS\nscore: 8.0\n"
            "axes: {voice: 8, structure: 8, depth: 8, specificity: 8, "
            "reader: 8}\n"
            "put_down_points: []\nread_at: 2026-09-09\nreaders: 4\n"
            "run_stamp: beta-reader (single-agent fallback) PASS "
            "2026-09-10T12:00:00Z\n"
            "---\n\nReport body.\n")
    report.write_text(body, encoding="utf-8")
    r = engine("readiness")
    assert r.returncode == 1
    assert "blind_gate_fallback" in r.stderr
    assert "single-agent fallback" in r.stderr
    cfg = project / "kb" / "project-config.json"
    doc = json.loads(cfg.read_text(encoding="utf-8"))
    doc["blind_gate_fallback"] = True
    cfg.write_text(json.dumps(doc, indent=2), encoding="utf-8")
    r = engine("readiness")
    assert r.returncode == 1  # fixture chapters are not all final
    assert "blind_gate_fallback" not in r.stderr


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


# ---------------------------------------------------------------------------
# revision status (ADD-3 optional engine follow-up — report-only cross-check)
# ---------------------------------------------------------------------------

def _write_plan(project, text):
    d = project / "work"
    d.mkdir(exist_ok=True)
    (d / "revision-plan.md").write_text(text, encoding="utf-8")


def _write_issues(project, text, month="2026-09"):
    d = project / "work" / "cold-reads" / month
    d.mkdir(parents=True, exist_ok=True)
    (d / "issues.md").write_text(text, encoding="utf-8")


ISSUES_TRIAGED = (
    "CR-001 | ch 3:12 | MAJOR | STRUCT | \"quote\" | flipped back | fix | SCENE\n"
    "CR-001 | triage | fixed | fixed in the ch3 revision pass\n"
    "CR-002 | ch 5:4 | MINOR | VOICE | \"quote\" | skimmed | fix | LINE\n"
    "CR-002 | triage | deferred-with-author-signoff | author signed off\n")

ISSUES_OPEN = (
    "CR-003 | ch 7:40 | MODERATE | PACE | \"quote\" | skimmed to break | fix | SCENE\n")

ISSUES_MISSING = ""  # no file at all


def test_revision_status_no_plan_is_clean(engine):
    r = engine("revision", "status")
    assert r.returncode == 0, r.stderr
    assert "no revision plan" in r.stdout


def test_revision_status_counts_and_clean_plan(engine, project):
    _write_issues(project, ISSUES_TRIAGED)
    _write_plan(project,
                "## Round 2026-09\nDoD: all big-picture rows done.\n"
                "REV-001 | cold-read:CR-001 | ch 3:12 | big-picture | high | medium | cut | resolved\n"
                "REV-002 | cold-read:CR-002 | ch 5:4 | line | low | small | n/a | resolved | beta deferred\n"
                "REV-003 | beta:readiness-report | ch 2 | character | medium | medium | expand | open\n"
                "REV-004 | critique:critique-chapter-02.md | ch 2:8 | line | low | small | cut | declined | author: intentional echo, keep\n")
    r = engine("revision", "status")
    assert r.returncode == 0, r.stderr
    assert "REV-00" not in r.stdout or "stale" not in r.stdout.lower()
    assert "resolved 2" in r.stdout and "open 1" in r.stdout
    assert "declined 1" in r.stdout
    assert "no stale or malformed rows" in r.stdout


def test_revision_status_flags_stale_resolved_row(engine, project, findings):
    _write_issues(project, ISSUES_OPEN)
    _write_plan(project,
                "REV-001 | cold-read:CR-003 | ch 7:40 | big-picture | high | large | move | resolved\n")
    r = engine("revision", "status")
    assert r.returncode == 1
    keys = {f["key"] for f in findings("revision", "status")}
    assert "revision:REV-001-stale" in keys
    stale = [f for f in findings("revision", "status") if f["key"] == "revision:REV-001-stale"][0]
    assert stale["technique"] == "stale-resolved"
    assert stale["severity"] == "warning"
    assert "CR-003" in stale["issue"]


def test_revision_status_missing_source_is_note_not_finding(engine, project):
    _write_issues(project, ISSUES_MISSING)
    _write_plan(project,
                "REV-001 | cold-read:CR-099 | ch 9:1 | line | low | small | n/a | resolved\n")
    r = engine("revision", "status")
    assert r.returncode == 0, r.stderr
    assert "CR-099" in r.stdout and "not found" in r.stdout


def test_revision_status_declined_row_requires_reason(engine, project, findings):
    _write_plan(project,
                "REV-001 | beta:readiness-report | ch 1 | line | low | small | n/a | declined\n")
    assert any(f["key"] == "revision:REV-001-declined-no-reason" for f in findings("revision", "status"))


def test_revision_status_malformed_row_reported(engine, project, findings):
    _write_plan(project,
                "REV-001 | cold-read:CR-001 | ch 3 | big-picture | high | open\n")
    assert any(f["key"] == "revision:REV-001-malformed" for f in findings("revision", "status"))


# ---------------------------------------------------------------------------
# library / series layer (library-spec.md section 17)
# ---------------------------------------------------------------------------
#
# The `library` fixture (conftest.py) seeds a two-book series library:
# book 1 (published, ordinal 1) and book 2 (draft, ordinal 2) sharing one
# series/bible.json outside both book roots. The seed plants deliberate
# series retcons the detection catalog must catch:
#   - char:uncle-radu deceased as of book 2's start yet cast in chapter-01
#   - a world-level knowledge fact claiming audience-learned-in 3:chapter-01
#     (learned in a later book than the one using it: anachronism) next to a
#     book-local bare chapter-03 fact (carve-out)
#   - the vault promise still open in the draft though established in the
#     published book 1 (open-thread carry, fires in both books)
#   - char:lena-popescu.status divergence (book kb 'grieving' vs canon
#     'alive') and an iron-clash on the role field
#   - retcon R002 recorded in retcons.jsonl but not applied to the bible
#     (retcon-log-orphan) and an established-in ref to a missing chapter
#   - an alias-joined entity (character-radu) with a mismatched kb id
#   - a shared-bible character (Maria) cast in book 2 without series-id
# Clean cases the checks must pass:
#   - character-radu appears in chapter-02 `mentions:` (mentions exempt)
#   - knowledge-city-map's bare `chapter-03` audience-learned-in is
#     current-book-local, never cross-book

EXPECTED_BOOK2_SERIES_KEYS = {
    "series:deceased-as-of-start:char:uncle-radu:2:chapter-01",
    "series:open-thread-carry:promise:the-vault-promise:2",
    "series:knowledge-anachronism:knowledge:academy-founded:2",
    "series:canon-divergence:char:lena-popescu:status:2",
    "series:iron-clash:char:lena-popescu:role:2",
    "series:unqualified-ref:errata:chapter-04",
    "series:id-mismatch:character-radu:2",
    "series:retcon-log-orphan:prop:brass-key:R002",
    "series:established-ref-missing:prop:brass-key:1:chapter-09",
    "series:unlinked-cast:char:maria-popescu:2:chapter-02",
}

EXPECTED_BOOK1_SERIES_KEYS = {
    "series:open-thread-carry:promise:the-vault-promise:1",
    "series:canon-divergence:prop:brass-key:location:1",
    "series:unqualified-ref:errata:chapter-04",
    "series:retcon-log-orphan:prop:brass-key:R002",
    "series:established-ref-missing:prop:brass-key:1:chapter-09",
}


def _library_findings(library_engine, book_root, *extra):
    r = library_engine("retcon-check", "--root", ".", str(book_root), *extra)
    out = [json.loads(l) for l in r.stdout.splitlines()
           if l.startswith("{")]
    return r, out


def test_retcon_check_emits_exact_series_keys(library_engine, library_books):
    r, fs = _library_findings(library_engine, library_books[1])
    assert r.returncode == 1, r.stderr
    assert _keys(fs) == EXPECTED_BOOK2_SERIES_KEYS
    # additive finding fields, no schema-version bump (spec 16-C2).
    # `book` carries the ordinal the finding pertains to: the checked book
    # for catalog rows, the referenced ordinal for bible-coordinate rows.
    for f in fs:
        assert f["series_scope"] is True
        assert isinstance(f["book"], int)
        assert f["audit"] == "series"
    # deterministic vs judgment split counted separately (spec 16-C8/L8)
    assert ("library retcon-check: 9 deterministic findings, 1 "
            "judgment-flagged (muse/kb-lead review)") in r.stderr
    unlinked = [f for f in fs if f["key"].startswith("series:unlinked-cast")]
    assert unlinked[0]["resolution"] == "judgment"
    # the iron divergence elevates via the iron-clash key; shared finding
    # severity stays inside the schema enum (warning, spec 16-C2)
    iron = [f for f in fs if f["key"].startswith("series:iron-clash")]
    assert iron[0]["severity"] == "warning"


def test_retcon_check_clean_cases_pass(library_engine, library_books):
    _, fs = _library_findings(library_engine, library_books[1])
    keys = _keys(fs)
    # mentions: are exempt everywhere — Radu appears in chapter-02 mentions
    assert not any("2:chapter-02" in k for k in keys
                   if k.startswith("series:deceased-as-of-start"))
    # bare chapter-NN audience-learned-in is current-book-local: no finding
    assert not any("city-map" in k for k in keys)
    # per-book promise (no series-id) never enters series checks
    assert not any("promise-bursary" in k for k in keys)
    # unpublished draft rows are deterministic, never judgment-flagged
    div = [f for f in fs
           if f["key"] == "series:canon-divergence:char:lena-popescu:status:2"]
    assert "resolution" not in div[0]


def test_retcon_check_published_book_judgment_rows(library_engine,
                                                   library_books):
    r, fs = _library_findings(library_engine, library_books[0])
    assert r.returncode == 1, r.stderr
    assert _keys(fs) == EXPECTED_BOOK1_SERIES_KEYS
    # freeze doctrine (spec 12): against published canon the divergence is
    # emitted as judgment with the retcon-record-required default
    div = [f for f in fs
           if f["key"] == "series:canon-divergence:prop:brass-key:location:1"]
    assert div[0]["resolution"] == "judgment"
    assert "retcon record required" in div[0]["issue"]


def test_retcon_check_series_dismissal_and_stale_rearm(library_engine,
                                                       library_books):
    b2 = library_books[1]
    fid = "series:canon-divergence:char:lena-popescu:status:2"
    r = library_engine("dismiss", "--root", ".", fid,
                       "--reason", "Lena grieves through book two on purpose.",
                       "--book-root", str(b2))
    assert r.returncode == 0, r.stderr
    _, fs = _library_findings(library_engine, b2)
    assert fid not in _keys(fs)
    # series-scope dismissal lives and dies in the library (spec 6)
    doc = json.loads((library_books[1].parent / "library" / "series"
                      / "exemptions.json").read_text(encoding="utf-8"))
    entry = doc["dismissals"][0]
    assert entry["finding_id"] == fid
    assert entry["scope"] == "series"
    assert entry["reason_author_words"] == \
        "Lena grieves through book two on purpose."
    assert entry["expires_on_entity_hash"].startswith("sha256:")
    # a direct kb edit flips the hash: the dismissal goes stale and the
    # finding re-fires (uniform rule, spec 6.3/16-M2)
    p = b2 / "kb" / "characters" / "character-lena.md"
    p.write_text(p.read_text(encoding="utf-8") + "\n", encoding="utf-8")
    _, fs = _library_findings(library_engine, b2)
    hit = [f for f in fs if f["key"] == fid]
    assert hit and "went stale" in hit[0]["issue"]


def test_retcon_plan_rows_and_apply_transaction(library_engine, library,
                                                library_books):
    b2 = library_books[1]
    r = library_engine("retcon-plan", "--root", ".", str(b2))
    assert r.returncode == 1, r.stderr
    import glob
    import os
    plans = sorted(glob.glob(str(library / "reports" / "retcon-plan-*.md")))
    assert plans
    plan_text = open(plans[-1], encoding="utf-8").read()
    assert "approved: false" in plan_text
    assert "- entity: char:lena-popescu" in plan_text
    assert "field: status" in plan_text
    assert '{"1": "alive", "2": "alive"}' in plan_text
    # apply refusals (spec 8.7)
    plan = library / "reports" / "retcon-plan-test.md"
    plan.write_text(
        "---\napproved: true\nbook_ordinal: 2\n---\n\n## Rows\n\n"
        "- entity: char:lena-popescu\n  field: status\n"
        '  new_by_book: {"1": "alive", "2": "grieving"}\n'
        '  author_words: ""\n', encoding="utf-8", newline="\n")
    assert library_engine("retcon", "--root", ".", "--apply",
                          str(plan)).returncode == 2
    plan.write_text(plan.read_text(encoding="utf-8").replace(
        "approved: true", "approved: false"), encoding="utf-8",
        newline="\n")
    assert library_engine("retcon", "--root", ".", "--apply",
                          str(plan)).returncode == 2
    # unparseable new_by_book
    plan.write_text(
        "---\napproved: true\nbook_ordinal: 2\n---\n\n## Rows\n\n"
        "- entity: char:lena-popescu\n  field: status\n"
        "  new_by_book: not-json\n"
        '  author_words: "words"\n', encoding="utf-8", newline="\n")
    assert library_engine("retcon", "--root", ".", "--apply",
                          str(plan)).returncode == 2
    # the successful transaction (spec 8.7: one per row)
    plan.write_text(
        "---\napproved: true\nbook_ordinal: 2\n---\n\n## Rows\n\n"
        "- entity: char:lena-popescu\n  field: status\n"
        '  new_by_book: {"1": "alive", "2": "grieving"}\n'
        '  coordinate: 2/chapter-01\n'
        '  author_words: "Lena grieves all through book two."\n',
        encoding="utf-8", newline="\n")
    r = library_engine("retcon", "--root", ".", "--apply", str(plan))
    assert r.returncode == 0, r.stderr
    log = (library / "series" / "retcons.jsonl").read_text(
        encoding="utf-8").strip().splitlines()
    assert len(log) == 3
    row = json.loads(log[-1])
    assert row["rid"] == "R003"
    assert row["kind"] == "fact-change"
    assert row["author_words"] == "Lena grieves all through book two."
    assert row["new_by_book"] == {"1": "alive", "2": "grieving"}
    bible = json.loads((library / "series" / "bible.json").read_text(
        encoding="utf-8"))
    field = bible["entities"]["char:lena-popescu"]["fields"]["status"]
    assert field["by-book"] == {"1": "alive", "2": "grieving"}
    assert bible["entities"]["char:lena-popescu"]["last_touched"] == "R003"
    manifest = json.loads((library / "library.json").read_text(
        encoding="utf-8"))
    assert manifest["series"]["next_retcon_id"] == 4


def test_retcon_apply_published_canon_frozen(library, library_engine):
    # spec 12: against a published book the author must explicitly override
    (library / "reports").mkdir(exist_ok=True)
    plan = library / "reports" / "retcon-plan-frozen.md"
    body = ("---\napproved: true\nbook_ordinal: 1\n"
            "override_published: false\n---\n\n## Rows\n\n"
            "- entity: prop:brass-key\n  field: location\n"
            '  new_by_book: {"1": "library shelf", "2": "vault"}\n'
            '  author_words: "The printed book says the shelf."\n')
    plan.write_text(body, encoding="utf-8", newline="\n")
    r = library_engine("retcon", "--root", ".", "--apply", str(plan))
    assert r.returncode == 2
    assert "override_published" in r.stderr
    plan.write_text(body.replace("override_published: false",
                                 "override_published: true"),
                    encoding="utf-8", newline="\n")
    r = library_engine("retcon", "--root", ".", "--apply", str(plan))
    assert r.returncode == 0, r.stderr
    # touching published-canon wording is recorded as errata (spec 8.7)
    row = json.loads((library / "series" / "retcons.jsonl").read_text(
        encoding="utf-8").strip().splitlines()[-1])
    assert row["kind"] == "errata"


def test_archived_book_is_fully_quiet(library, library_engine,
                                      library_books):
    # spec 12: archived = frozen for writes, exempt from all findings
    manifest_path = library / "library.json"
    doc = json.loads(manifest_path.read_text(encoding="utf-8"))
    doc["books"][1]["status"] = "archived"
    manifest_path.write_text(json.dumps(doc, indent=2), encoding="utf-8")
    r, fs = _library_findings(library_engine, library_books[1])
    assert r.returncode == 0
    assert fs == []
    assert "0 deterministic findings, 0 judgment-flagged" in r.stderr


def test_bootstrap_tiers_and_resolution_gate(library, library_engine,
                                            library_books):
    import re
    b2 = library_books[1]
    # strip the explicit join key: name "Radu" matches the bible alias
    # whole-string -> alias tier with the id-mismatch advisory (spec 8.5)
    radu = b2 / "kb" / "characters" / "character-radu.md"
    radu.write_text(radu.read_text(encoding="utf-8").replace(
        "series-id: char:uncle-radu\n", ""), encoding="utf-8")
    r = library_engine("bootstrap", "--root", ".", str(b2))
    assert r.returncode == 1, r.stderr
    import glob
    import os
    plans = sorted(glob.glob(str(library / "reports" / "bootstrap-plan-*.md")))
    assert plans and "5 exact, 1 alias, 3 [?]" in r.stderr
    plan_path = plans[-1]
    body = open(plan_path, encoding="utf-8").read()
    assert "- entity: character-radu" in body
    assert re.search(r"tier: alias\n  series_id: char:uncle-radu\n"
                     r"  advisory: series:id-mismatch", body)
    # --apply refuses an unapproved plan (spec 8.5)
    assert library_engine("bootstrap", "--root", ".", "--apply", plan_path,
                          str(b2)).returncode == 2
    # resolution notes required for every [?] row (the author's words)
    filled = body.replace("approved: false", "approved: true")
    filled = filled.replace(
        "tier: ambiguity\n  resolution: \n  author_words: \"\"",
        "tier: ambiguity\n  resolution: local\n"
        '  author_words: "These three stay book-local."')
    open(plan_path, "w", encoding="utf-8", newline="\n").write(filled)
    open(plan_path, "w", encoding="utf-8", newline="\n").write(
        filled.replace('author_words: "These three stay book-local."',
                       'author_words: ""'))
    assert library_engine("bootstrap", "--root", ".", "--apply", plan_path,
                          str(b2)).returncode == 2
    open(plan_path, "w", encoding="utf-8", newline="\n").write(filled)
    r = library_engine("bootstrap", "--root", ".", "--apply", plan_path,
                       str(b2))
    assert r.returncode == 0, r.stderr
    # the alias row joined and wrote the series-id back
    assert "series-id: char:uncle-radu" in radu.read_text(encoding="utf-8")
    # [?] rows resolved to local wrote nothing and promoted no canon
    vegg = (b2 / "kb" / "characters" / "character-vegg.md").read_text(
        encoding="utf-8")
    assert "series-id" not in vegg
    bible = json.loads((library / "series" / "bible.json").read_text(
        encoding="utf-8"))
    assert not any("vegg" in k for k in bible["entities"])


def test_sidecar_unknown_schema_version_fails_loud(library, library_engine,
                                                   library_books):
    # spec 17 T10: a sidecar declaring an unknown schema_version is a
    # fail-loud exit 2 for both link and validate - never guessed.
    sidecar = library_books[1] / ".vellum" / "series-link.json"
    doc = json.loads(sidecar.read_text(encoding="utf-8"))
    doc["schema_version"] = 99
    sidecar.write_text(json.dumps(doc, indent=2), encoding="utf-8")
    r = library_engine("validate", "--root", ".")
    assert r.returncode == 2
    assert "schema_version" in r.stderr
    r = library_engine("link", "--root", ".", str(library_books[1]))
    assert r.returncode == 2
    assert "schema_version" in r.stderr


def test_validate_emits_expected_findings(library, library_engine,
                                          library_books):
    r = library_engine("validate", "--root", ".")
    assert r.returncode == 1
    fs = [json.loads(l) for l in r.stdout.splitlines() if l.startswith("{")]
    assert _keys(fs) == {
        "series:engine-copy-lag:2",                       # old scripts/ copy
        "series:established-ref-missing:prop:brass-key:1:chapter-09",
        "series:timeline-unparsed-when:E002",
        "series:established-ref-missing:timeline:E011:1:chapter-03",
        "series:retcon-log-orphan:prop:brass-key:R002",
    }
    # manifest entry without sidecar = half-linked (spec 8.2/8.4)
    sidecar = library_books[1] / ".vellum" / "series-link.json"
    sidecar.unlink()
    r = library_engine("validate", "--root", ".")
    fs = [json.loads(l) for l in r.stdout.splitlines() if l.startswith("{")]
    assert "series:half-linked:3f2c9a1e-2222-4aaa-9bbb-000000000002" \
        in _keys(fs)
    # --fix regenerates stale book-side sidecars from the manifest
    r = library_engine("validate", "--root", ".", "--fix")
    assert sidecar.exists()
    fixed = json.loads(sidecar.read_text(encoding="utf-8"))
    assert fixed["book_uuid"] == "3f2c9a1e-2222-4aaa-9bbb-000000000002"
    assert fixed["ordinal"] == 2
    r = library_engine("validate", "--root", ".")
    fs = [json.loads(l) for l in r.stdout.splitlines() if l.startswith("{")]
    assert not any(k.startswith("series:half-linked") for k in _keys(fs))


def test_library_init_refuses_book_project_and_creates_tree(
        library_engine, library_books, tmp_path):
    # spec 1.4: never initialized inside a book project
    r = library_engine("init", "--root", str(library_books[0]))
    assert r.returncode == 2
    # clean dir: the full tree per spec 1.1
    target = tmp_path / "fresh-library"
    r = library_engine("init", "--root", str(target), "--title",
                       "Test Series")
    assert r.returncode == 0, r.stderr
    assert sorted(p.name for p in target.iterdir()) == \
        ["handoff", "library.json", "reports", "series"]
    assert sorted(p.name for p in (target / "series").iterdir()) == \
        ["bible.json", "errata.md", "exemptions.json", "retcons.jsonl"]
    manifest = json.loads((target / "library.json").read_text(
        encoding="utf-8"))
    assert manifest["kind"] == "vellum-library"
    assert manifest["schema_version"] == 1
    assert manifest["books"] == []
    assert manifest["engine_min_version_global"] == "0.1.1"
    # a manifest without the kind marker is not a library (fail-loud)
    (target / "library.json").write_text('{"kind": "other"}',
                                         encoding="utf-8")
    r = library_engine("validate", "--root", str(target))
    assert r.returncode == 2


def test_library_link_lifecycle_idempotent_and_half_linked(
        library, library_engine, library_books, tmp_path):
    import shutil
    book = tmp_path / "book-copy"
    shutil.copytree(str(library_books[0]), str(book))
    sidecar = book / ".vellum" / "series-link.json"
    sidecar.unlink()  # start unlinked
    libroot = tmp_path / "new-library"
    assert library_engine("init", "--root", str(libroot)).returncode == 0
    r = library_engine("link", "--root", str(libroot), str(book))
    assert r.returncode == 0, r.stderr
    manifest = json.loads((libroot / "library.json").read_text(
        encoding="utf-8"))
    sc = json.loads(sidecar.read_text(encoding="utf-8"))
    assert len(manifest["books"]) == 1
    assert manifest["books"][0]["book_uuid"] == sc["book_uuid"]
    assert manifest["books"][0]["ordinal"] == 1
    assert manifest["books"][0]["status"] == "draft"
    # uuid lives in manifest + sidecar only — never in kb/story.md
    assert sc["book_uuid"] not in (book / "kb" / "story.md").read_text(
        encoding="utf-8")
    # re-link is idempotent: no duplicate entries (spec 8.2)
    r = library_engine("link", "--root", str(libroot), str(book))
    assert r.returncode == 0
    manifest = json.loads((libroot / "library.json").read_text(
        encoding="utf-8"))
    assert len(manifest["books"]) == 1
    # crash between the two writes: sidecar survives, manifest entry lost;
    # validate reports the half-state and re-link completes it (spec 16-A4)
    manifest["books"] = []
    (libroot / "library.json").write_text(json.dumps(manifest, indent=2),
                                          encoding="utf-8")
    r = library_engine("validate", "--root", str(libroot), str(book))
    fs = [json.loads(l) for l in r.stdout.splitlines() if l.startswith("{")]
    assert any(k.startswith("series:half-linked") for k in _keys(fs))
    assert library_engine("link", "--root", str(libroot),
                          str(book)).returncode == 0
    manifest = json.loads((libroot / "library.json").read_text(
        encoding="utf-8"))
    assert len(manifest["books"]) == 1
    assert manifest["books"][0]["book_uuid"] == sc["book_uuid"]
    # unlink removes the sidecar and marks the manifest (spec 8.3)
    r = library_engine("unlink", "--root", str(libroot), str(book))
    assert r.returncode == 0
    assert not sidecar.exists()
    manifest = json.loads((libroot / "library.json").read_text(
        encoding="utf-8"))
    assert manifest["books"][0]["unlinked_at"] is not None


def test_unlink_retains_orphan_canon(library, library_engine,
                                     library_books):
    # spec 8.3/10 #6: canon remembers detached books
    r = library_engine("unlink", "--root", ".", str(library_books[0]))
    assert r.returncode == 0, r.stderr
    assert "5 orphan canon reference(s)" in r.stderr
    _, fs = _library_findings(library_engine, library_books[1])
    orphans = [f for f in fs
               if f["key"].startswith("series:orphan-book-ref")]
    assert len(orphans) == 5
    assert all(f["book"] == 1 for f in orphans)


def test_lock_contention_times_out(library, library_engine, monkeypatch):
    monkeypatch.setenv("VELLUM_LIB_LOCK_TIMEOUT", "1")
    lock = library / ".lock"
    lock.write_text("999 contention-test", encoding="utf-8")
    try:
        r = library_engine("dismiss", "--root", ".", "series:x:1",
                           "--reason", "test reason")
        assert r.returncode == 2
        assert "locked by another process" in r.stderr
    finally:
        lock.unlink(missing_ok=True)


def test_series_exit_codes(library_engine, library, library_books):
    # spec 8 exit table: 2 on usage/schema errors, 0 on clean success
    assert library_engine().returncode == 2                    # no subcommand
    assert library_engine("no-such-command").returncode == 2   # unknown verb
    assert library_engine("retcon-check",
                          str(library_books[1])).returncode == 2  # no --root
    assert library_engine("init", "--root",
                          str(library_books[0])).returncode == 2  # in a book
    r = library_engine("state", "--root", ".", "--card-line",
                       str(library_books[1]))
    assert r.returncode == 0
    assert r.stdout.startswith("series Aethelgard — this book: ordinal 2 "
                               "(draft)")


def test_timeline_orders_iso_when_and_flags_unparseable(library,
                                                        library_engine):
    r = library_engine("timeline", "--root", ".")
    assert r.returncode == 1
    lines = [l for l in r.stdout.splitlines() if l.startswith("E")]
    # structured ISO-8601 `when` sorts; the unparseable row is flagged last
    assert [l.split(" | ")[0] for l in lines] == ["E001", "E011", "E002"]
    assert any("[UNPARSEABLE WHEN]" in l for l in lines)
    assert "unparseable" in r.stderr


def test_state_card_fixed_sections_and_cap(library, library_engine,
                                           library_books):
    r = library_engine("state", "--root", ".", str(library_books[1]))
    assert r.returncode == 0, r.stderr
    card = r.stdout
    for section in ("## Series state", "do not re-explain", "Open retcons:",
                    "Iron facts:", "Recent retcons:"):
        assert section in card
    assert "Lena Popescu — established in 1/chapter-01" in card
    assert "- R001 [fact-change] char:lena-popescu" in card
    assert len(card.encode("utf-8")) <= 12 * 1024


def test_handoff_document_generated(library, library_engine,
                                    library_books):
    r = library_engine("handoff", "--root", ".", str(library_books[1]))
    assert r.returncode == 0, r.stderr
    doc = library / "handoff" / "handoff-3.md"
    assert doc.exists()
    text = doc.read_text(encoding="utf-8")
    for section in ("## Frozen canon snapshot", "## Iron facts",
                    "## Do-not-re-explain register", "## Open retcons",
                    "## Errata posture", "## One-line fact register"):
        assert section in text
    # frozen canon snapshot: highest-ordinal by-book values
    assert "location = 'vault' (book 2)" in text


def _without_generated_stamp(text):
    return "\n".join(l for l in text.split("\n")
                     if not l.startswith("Generated by `vellum state"))


def test_vellum_state_series_section_injection(engine, project,
                                               library_engine, tmp_path):
    # spec 8.8/13.5/T3: the series card rides the existing `vellum state`
    # output; an unlinked book's output is byte-identical to v0.1.1.
    import os
    assert engine("state", "rebuild").returncode == 0
    baseline = (project / "state" / "state-card.md").read_text(
        encoding="utf-8")
    libroot = tmp_path / "injected-library"
    assert library_engine("init", "--root", str(libroot)).returncode == 0
    assert library_engine("link", "--root", str(libroot),
                          str(project)).returncode == 0
    assert engine("state", "rebuild").returncode == 0
    linked = (project / "state" / "state-card.md").read_text(
        encoding="utf-8")
    # only the series section is appended; the v0.1.1 card is untouched
    # (modulo the rebuild timestamp line)
    assert _without_generated_stamp(linked).startswith(
        _without_generated_stamp(baseline))
    assert "## Series state" in linked
    assert linked.count("## Series state") == 1


def test_series_modules_absent_leaves_vellum_state_unchanged(
        engine, project, plugin_root, library_engine, tmp_path):
    # spec 17-T2: with the v0.2.0 series modules deleted the full v0.1.1
    # surface is untouched (fail-open import in state.py).
    import os
    assert engine("state", "rebuild").returncode == 0
    baseline = (project / "state" / "state-card.md").read_text(
        encoding="utf-8")
    surface_args = [
        ("ledger", "check"), ("bible", "validate"), ("wordcount",),
        ("knowledge", "character-vess", "--as-of", "5"),
    ]
    baseline_surface = [(args, engine(*args).returncode,
                        engine(*args).stdout) for args in surface_args]
    libroot = tmp_path / "t2-library"
    library_engine("init", "--root", str(libroot))
    library_engine("link", "--root", str(libroot), str(project))
    assert engine("state", "rebuild").returncode == 0
    linked = (project / "state" / "state-card.md").read_text(
        encoding="utf-8")
    assert "## Series state" in linked  # the link is live while modules exist
    lib_dir = plugin_root / "scripts" / "vellum_lib"
    renamed = []
    targets = [lib_dir / "series_bible.py", lib_dir / "series_checks.py",
               lib_dir / "series_cli.py", plugin_root / "scripts" / "library.py"]
    try:
        for p in targets:
            backup = p.with_name(p.name + ".t2bak")
            p.rename(backup)
            renamed.append((p, backup))
        r = engine("state", "rebuild")
        assert r.returncode == 0, r.stderr
        without_surface = [(args, engine(*args).returncode,
                            engine(*args).stdout) for args in surface_args]
        assert without_surface == baseline_surface
        without = (project / "state" / "state-card.md").read_text(
            encoding="utf-8")
        # Rebuild stamps the generated-at time; normalize that derived line
        # while asserting every other v0.1.1 byte is preserved.
        assert _without_generated_stamp(without) == \
            _without_generated_stamp(baseline)  # byte-identical otherwise
    finally:
        for original, backup in renamed:
            backup.rename(original)
