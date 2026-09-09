# Vellum hook-contract suite (design-spec.md section 14).
"""Hook-contract tests run through Git Bash on both ubuntu-latest and
windows-latest: block/allow matrix for the outline gate (Write path and Bash
path); E2BIG regression (>128 KiB payload via stdin); CRLF files; UTF-8 BOM;
paths with spaces; drive-letter cases; interpreter-absent / engine-absent
fail-open (bash predicates still gate); outline-copy detector >90% similarity;
gate-input protection for spawned agents."""
import json
import os
import subprocess

import pytest


def _payload(path, extra=None):
    p = {"tool_name": "Write", "tool_input": {"file_path": path}}
    if extra:
        p.update(extra)
    return p


def _bash_payload(command):
    return {"tool_name": "Bash", "tool_input": {"command": command}}


def _chapter(root, num, status="draft", approved_outline=True, create=True):
    """Return a chapter's absolute path; create the file only when asked.
    Block tests use create=False: gate 1 rules a CREATION write by outline
    frontmatter, while rewriting an existing draft re-checks state only."""
    p = root / "manuscript" / "chapters" / ("chapter-%02d.md" % num)
    if create:
        p.parent.mkdir(parents=True, exist_ok=True)
        ao = "work/outline/chapter-%02d.md" % num if approved_outline else ""
        fm_lines = [
            "---",
            'title: "T"',
            "number: %d" % num,
            "status: %s" % status,
            "approved-outline: %s" % ao,
            "pov: character-mira-tarn",
            "characters: [character-mira-tarn]",
            "mentions: []",
            "promises-advanced: []",
            "word-target: 3200",
            "word-count: null",
            "---",
            "",
            "Body.",
        ]
        p.write_text("\n".join(fm_lines) + "\n", encoding="utf-8", newline="\n")
    return str(p)


def _outline(root, num, approved=True, comment=False):
    d = root / "work" / "outline"
    d.mkdir(parents=True, exist_ok=True)
    flag = "true" if approved else "false"
    if comment:
        flag += "          # author acceptance, recorded by muse; gate 1 requires true"
    p = d / ("chapter-%02d.md" % num)
    p.write_text(
        "---\nchapter: %d\ntitle: \"T\"\napproved: %s\npivotal: false\n"
        "word-target: 3200\nverbatim: []\n---\n\n## Beats\n1. beat — quota 3200\n"
        % (num, flag), encoding="utf-8", newline="\n")
    return p



def _failing_engine(project):
    """A stand-in engine script that exits 3 (crash) — exercises the guard's
    fail-open-on-uncertainty branch (rc not 0 and not 2)."""
    s = project / "failing-engine.py"
    s.write_text("import sys\nsys.stderr.write('boom')\nsys.exit(3)\n",
                 encoding="utf-8", newline="\n")
    return str(s)


@pytest.fixture()
def gate_ready(engine, project):
    """Rebuild state and flip the accepted fixture chapter to final so the
    transactional preconditions pass."""
    ch6 = project / "manuscript" / "chapters" / "chapter-06.md"
    ch6.write_text(ch6.read_text(encoding="utf-8").replace(
        "status: accepted", "status: final"), encoding="utf-8")
    engine("state", "rebuild")
    return project


# ---------------------------------------------------------------------------
# Outline gate: Write/Edit path — block/allow matrix
# ---------------------------------------------------------------------------

def test_gate_blocks_write_without_outline(hook, project):
    target = _chapter(project, 9, create=False)
    r = hook("guard-outline-before-prose.sh", _payload(target))
    assert r.returncode == 2
    assert "no outline" in r.stderr


def test_gate_blocks_write_with_unapproved_outline(hook, project):
    target = _chapter(project, 9, create=False)
    _outline(project, 9, approved=False)
    r = hook("guard-outline-before-prose.sh", _payload(target))
    assert r.returncode == 2
    assert "not marked approved" in r.stderr


def test_gate_allows_write_with_approved_outline(hook, engine, project):
    # neutralize the fixture's accepted chapter so pending_capture is false
    ch6 = project / "manuscript" / "chapters" / "chapter-06.md"
    ch6.write_text(ch6.read_text(encoding="utf-8").replace(
        "status: accepted", "status: final"), encoding="utf-8")
    engine("state", "rebuild")
    target = _chapter(project, 9, create=False)
    _outline(project, 9, approved=True)
    r = hook("guard-outline-before-prose.sh", _payload(target))
    assert r.returncode == 0, r.stderr


def test_gate_blocks_when_state_check_fails(hook, engine, project):
    target = _chapter(project, 9, create=False)
    _outline(project, 9, approved=True)
    engine("state", "rebuild")  # pending_capture true (ch6 accepted)
    r = hook("guard-outline-before-prose.sh", _payload(target))
    assert r.returncode == 2
    assert "chapter transaction" in r.stderr


def test_gate_approved_with_inline_comment_allows(hook, engine, project):
    # Regression: the outline contract ships `approved: true   # comment ...`;
    # fm_field must strip the inline comment or gate 1 mis-blocks.
    ch6 = project / "manuscript" / "chapters" / "chapter-06.md"
    ch6.write_text(ch6.read_text(encoding="utf-8").replace(
        "status: accepted", "status: final"), encoding="utf-8")
    engine("state", "rebuild")
    target = _chapter(project, 9, create=False)
    _outline(project, 9, approved=True, comment=True)
    r = hook("guard-outline-before-prose.sh", _payload(target))
    assert r.returncode == 0, r.stderr


def test_gate_rewrite_of_draft_chapter_rechecks_state_only(hook, engine, project):
    # A draft chapter rewrite skips the outline check (re-check state only).
    ch6 = project / "manuscript" / "chapters" / "chapter-06.md"
    ch6.write_text(ch6.read_text(encoding="utf-8").replace(
        "status: accepted", "status: final"), encoding="utf-8")
    engine("state", "rebuild")
    target = _chapter(project, 3, status="draft")  # ch3 has no outline needed
    r = hook("guard-outline-before-prose.sh", _payload(target))
    assert r.returncode == 0, r.stderr


def test_gate_ignores_non_chapter_writes(hook, project):
    r = hook("guard-outline-before-prose.sh",
             _payload(str(project / "kb" / "story.md")))
    assert r.returncode == 0


def test_gate_fails_open_on_ambiguous_payload(hook, project):
    r = hook("guard-outline-before-prose.sh",
             {"tool_name": "Write", "tool_input": {"file_path": "$HOME/x.md"}})
    assert r.returncode == 0


# ---------------------------------------------------------------------------
# Outline gate: Bash alternate path
# ---------------------------------------------------------------------------

def test_bash_gate_blocks_redirect_into_chapters(hook, project):
    r = hook("guard-bash-prose-writes.sh",
             _bash_payload("echo x > manuscript/chapters/chapter-09.md"))
    assert r.returncode == 2


def test_bash_gate_compound_command_second_redirect_gated(hook, project):
    # Regression: the scanner used to gate only the FIRST redirect.
    cmd = ("echo x > scratch/tmp.md; "
           "cat manuscript/chapters/chapter-01.md > manuscript/chapters/chapter-09.md")
    (project / "scratch").mkdir(exist_ok=True)
    r = hook("guard-bash-prose-writes.sh", _bash_payload(cmd))
    assert r.returncode == 2, "second redirect in a compound command must gate"


def test_bash_gate_compound_command_second_cp_gated(hook, project):
    # Regression: only the first cp/mv fragment used to become a candidate.
    cmd = ("cp notes/a.txt scratch/b.txt; "
           "cp notes/a.txt manuscript/chapters/chapter-09.md")
    (project / "notes").mkdir(exist_ok=True)
    (project / "notes" / "a.txt").write_text("source", encoding="utf-8")
    (project / "scratch").mkdir(exist_ok=True)
    r = hook("guard-bash-prose-writes.sh", _bash_payload(cmd))
    assert r.returncode == 2, "second cp in a compound command must gate"


def test_bash_gate_allows_benign_command(hook, project):
    (project / "scratch").mkdir(exist_ok=True)
    r = hook("guard-bash-prose-writes.sh",
             _bash_payload("echo hello > scratch/out.txt"))
    assert r.returncode == 0


def test_bash_gate_tee_target_gated(hook, project):
    r = hook("guard-bash-prose-writes.sh",
             _bash_payload("echo x | tee manuscript/chapters/chapter-09.md"))
    assert r.returncode == 2


def test_bash_gate_blocks_sed_inline_chapter_write(hook, project):
    # Interpreter-embedded writes: sed -i into a chapter has no
    # redirect/tee/cp/mv shape, but the write-indicator path-token scan
    # surfaces the target and the outline predicate gates it.
    _outline(project, 9, approved=False)
    r = hook("guard-bash-prose-writes.sh",
             _bash_payload("sed -i 's/x/y/' manuscript/chapters/chapter-09.md"))
    assert r.returncode == 2
    assert "approved" in r.stderr


def test_bash_gate_allows_reads_of_chapters(hook, project):
    # Read-only commands carry no write indicator: path tokens in an rg/cat
    # are never gated.
    r = hook("guard-bash-prose-writes.sh",
             _bash_payload("rg 'salt' manuscript/chapters/chapter-01.md"))
    assert r.returncode == 0


def test_bash_gate_blocks_outline_flag_flip(hook, project, tmp_path):
    # A subagent must not set the gate flags through a shell redirect either.
    payload = {"tool_name": "Bash",
               "transcript_path": _transcript(tmp_path, True),
               "tool_input": {"command":
                              "printf 'approved: true\\n' > work/outline/chapter-09.md"}}
    r = hook("guard-bash-prose-writes.sh", payload)
    assert r.returncode == 2
    assert "gate-input" in r.stderr


def test_bash_gate_blocks_outline_copy_laundering(hook, project, tmp_path):
    # A copy/move between outlines would launder the source's approval into
    # the target; two work/outline/ references in one command are blocked.
    _outline(project, 8, approved=True)
    payload = {"tool_name": "Bash",
               "transcript_path": _transcript(tmp_path, True),
               "tool_input": {"command":
                              "cp work/outline/chapter-08.md work/outline/chapter-09.md"}}
    r = hook("guard-bash-prose-writes.sh", payload)
    assert r.returncode == 2
    assert "gate-input" in r.stderr


def test_main_session_bash_can_copy_outlines(hook, project, tmp_path):
    # Main-session rules: the muse may move outlines (the copy-laundering and
    # flag scans only bind spawned agents).
    _outline(project, 8, approved=True)
    payload = {"tool_name": "Bash",
               "transcript_path": _transcript(tmp_path, False),
               "tool_input": {"command":
                              "cp work/outline/chapter-08.md work/outline/chapter-09.md"}}
    r = hook("guard-bash-prose-writes.sh", payload)
    assert r.returncode == 0, r.stderr


# ---------------------------------------------------------------------------
# Outline-copy detector
# ---------------------------------------------------------------------------

def test_copy_detector_blocks_chapter_copy(hook, project, engine):
    # The outline gate passes (approved outline + closed transaction); the
    # copy detector is what blocks: a new chapter 100% line-identical to a
    # prior chapter.
    ch6 = project / "manuscript" / "chapters" / "chapter-06.md"
    ch6.write_text(ch6.read_text(encoding="utf-8").replace(
        "status: accepted", "status: final"), encoding="utf-8")
    engine("state", "rebuild")
    _outline(project, 9, approved=True)
    src = project / "manuscript" / "chapters" / "chapter-01.md"
    cmd = "cp %s manuscript/chapters/chapter-09.md" % src
    r = hook("guard-bash-prose-writes.sh", _bash_payload(cmd))
    assert r.returncode == 2
    assert "outline-copy" in r.stderr


def test_copy_detector_allows_original_prose(hook, project, engine):
    ch6 = project / "manuscript" / "chapters" / "chapter-06.md"
    ch6.write_text(ch6.read_text(encoding="utf-8").replace(
        "status: accepted", "status: final"), encoding="utf-8")
    engine("state", "rebuild")
    _outline(project, 9, approved=True)  # gate passes; copy detector decides
    (project / "scratch").mkdir(exist_ok=True)
    novel = project / "scratch" / "fresh.md"
    novel.write_text("\n\n".join(
        "Original prose %d with its own rhythm and specific detail." % i
        for i in range(40)), encoding="utf-8")
    cmd = "cp %s manuscript/chapters/chapter-09.md" % novel
    r = hook("guard-bash-prose-writes.sh", _bash_payload(cmd))
    assert r.returncode == 0, r.stderr


# ---------------------------------------------------------------------------
# E2BIG: the payload must travel via stdin, not the environment
# ---------------------------------------------------------------------------

def test_e2big_large_payload_still_gates(hook, project):
    big = "x" * (140 * 1024)  # > 128 KiB
    target = _chapter(project, 9, create=False)
    _outline(project, 9, approved=False)
    r = hook("guard-outline-before-prose.sh",
             _payload(target, {"tool_input": {"file_path": target,
                                              "content": big,
                                              "old_string": big}}))
    assert r.returncode == 2  # still gated, not killed by E2BIG


# ---------------------------------------------------------------------------
# CRLF / BOM / paths with spaces / drive letters
# ---------------------------------------------------------------------------

def test_gate_handles_crlf_files(hook, engine, project):
    ch6 = project / "manuscript" / "chapters" / "chapter-06.md"
    ch6.write_text(ch6.read_text(encoding="utf-8").replace(
        "status: accepted", "status: final"), encoding="utf-8", newline="\r\n")
    engine("state", "rebuild")
    target = _chapter(project, 9)
    o = _outline(project, 9, approved=True)
    o.write_text(o.read_text(encoding="utf-8"), encoding="utf-8", newline="\r\n")
    r = hook("guard-outline-before-prose.sh", _payload(target))
    assert r.returncode == 0, r.stderr


def test_gate_handles_utf8_bom(hook, engine, project):
    ch6 = project / "manuscript" / "chapters" / "chapter-06.md"
    ch6.write_text(ch6.read_text(encoding="utf-8").replace(
        "status: accepted", "status: final"), encoding="utf-8")
    engine("state", "rebuild")
    target = _chapter(project, 9)
    o = _outline(project, 9, approved=True)
    o.write_text("\ufeff" + o.read_text(encoding="utf-8"), encoding="utf-8")
    r = hook("guard-outline-before-prose.sh", _payload(target))
    assert r.returncode == 0, r.stderr


def test_gate_handles_project_path_with_spaces(tmp_path, hook, engine):
    proj = tmp_path / "my novel project"
    proj.mkdir()
    import sys
    sys.path.insert(0, str(tmp_path))
    import shutil as _sh
    _sh.rmtree(proj)
    from conftest import fixture_seed  # reuse the seeder
    fixture_seed.seed(str(proj))
    ch6 = proj / "manuscript" / "chapters" / "chapter-06.md"
    ch6.write_text(ch6.read_text(encoding="utf-8").replace(
        "status: accepted", "status: final"), encoding="utf-8")
    engine("state", "rebuild", root=proj)
    d = proj / "manuscript" / "chapters"
    target = str(d / "chapter-09.md")
    o = proj / "work" / "outline" / "chapter-09.md"
    o.parent.mkdir(parents=True, exist_ok=True)
    o.write_text("---\nchapter: 9\napproved: true\npivotal: false\n"
                 "word-target: 3200\nverbatim: []\n---\n\nbeats\n",
                 encoding="utf-8")
    r = hook("guard-outline-before-prose.sh", _payload(target), root=proj)
    assert r.returncode == 0, r.stderr


def test_gate_windows_drive_letter_path(hook, engine, project):
    # C:/ and C:\ forms must resolve as absolute (not join onto root).
    ch6 = project / "manuscript" / "chapters" / "chapter-06.md"
    ch6.write_text(ch6.read_text(encoding="utf-8").replace(
        "status: accepted", "status: final"), encoding="utf-8")
    engine("state", "rebuild")
    _outline(project, 9, approved=False)
    target = str(project / "manuscript" / "chapters" / "chapter-09.md")
    for form in (target.replace("/", "\\"), target):
        r = hook("guard-outline-before-prose.sh", _payload(form))
        assert r.returncode == 2, form  # unapproved -> block on either form


# ---------------------------------------------------------------------------
# Fail-open: interpreter/engine absent or broken -> advisory, bash still gates
# ---------------------------------------------------------------------------

def test_engine_broken_fails_open_but_bash_predicate_gates(hook, project):
    # With VELLUM_ENGINE_OVERRIDE pointed at a failing command, state check
    # cannot run (rc != 0 and != 2 -> fail open); the outline predicate still
    # blocks an unapproved chapter.
    target = _chapter(project, 9, create=False)
    _outline(project, 9, approved=False)
    r = hook("guard-outline-before-prose.sh", _payload(target),
             extra_env={"VELLUM_ENGINE_OVERRIDE": _failing_engine(project)})
    assert r.returncode == 2
    assert "not marked approved" in r.stderr


def test_engine_broken_allows_approved_chapter_fail_open(hook, engine, project):
    # Doctrine: better to miss than mis-block. The bash predicate passes
    # (approved outline); the engine is broken -> one advisory line, allow.
    ch6 = project / "manuscript" / "chapters" / "chapter-06.md"
    ch6.write_text(ch6.read_text(encoding="utf-8").replace(
        "status: accepted", "status: final"), encoding="utf-8")
    engine("state", "rebuild")
    target = _chapter(project, 9, create=False)
    _outline(project, 9, approved=True)
    r = hook("guard-outline-before-prose.sh", _payload(target),
             extra_env={"VELLUM_ENGINE_OVERRIDE": _failing_engine(project)})
    assert r.returncode == 0, r.stderr
    assert "state check could not run" in r.stderr


# ---------------------------------------------------------------------------
# Gate-input protection (spawned agents never write gate inputs)
# ---------------------------------------------------------------------------

def _transcript(tmp_path, sidechain):
    p = tmp_path / ("t-%d.jsonl" % sidechain)
    p.write_text(json.dumps({"isSidechain": sidechain}) + "\n", encoding="utf-8")
    return str(p)


def test_subagent_cannot_set_outline_gate_flags(hook, project, tmp_path):
    # A subagent write that would set the gate flags (approved: true /
    # pivotal: true) in work/outline/ is blocked — the author records outline
    # acceptance through the muse.
    target = str(_outline(project, 9, approved=False))
    payload = {"tool_name": "Write", "transcript_path": _transcript(tmp_path, True),
               "tool_input": {"file_path": target,
                              "content": "---\nchapter: 9\ntitle: \"T\"\n"
                                         "approved: true\npivotal: false\n"
                                         "word-target: 3200\nverbatim: []\n"
                                         "---\n\n## Beats\n1. beat\n"}}
    r = hook("guard-outline-before-prose.sh", payload)
    assert r.returncode == 2
    assert "gate-input" in r.stderr


def test_subagent_can_draft_outline_with_flags_false(hook, project, tmp_path):
    # The outliner legitimately creates outlines with the flags false
    # (chapter-loop step 1); gate-input protection must not block its own
    # creation path.
    target = str(project / "work" / "outline" / "chapter-09.md")
    payload = {"tool_name": "Write", "transcript_path": _transcript(tmp_path, True),
               "tool_input": {"file_path": target,
                              "content": "---\nchapter: 9\ntitle: \"T\"\n"
                                         "approved: false\npivotal: false\n"
                                         "word-target: 3200\nverbatim: []\n"
                                         "---\n\n## Beats\n1. beat\n"}}
    r = hook("guard-outline-before-prose.sh", payload)
    assert r.returncode == 0, r.stderr


def test_subagent_cannot_write_critique_reports(hook, project, tmp_path):
    target = str(project / "work" / "critique-reports" / "blind-chapter-09.md")
    r = hook("guard-outline-before-prose.sh",
             _payload(target, {"transcript_path": _transcript(tmp_path, True)}))
    assert r.returncode == 2
    assert "gate-input" in r.stderr


def test_main_session_can_write_outline_approval(hook, project, tmp_path):
    target = str(_outline(project, 9, approved=False))
    r = hook("guard-outline-before-prose.sh",
             _payload(target, {"transcript_path": _transcript(tmp_path, False)}))
    assert r.returncode == 0  # muse persists verdicts/approvals


# ---------------------------------------------------------------------------
# Post-write net: hard signals + voice-debt + voice:skip
# ---------------------------------------------------------------------------

def test_postwrite_flags_truncated_chapter(hook, project):
    target = _chapter(project, 9, status="draft")
    (project / "manuscript" / "chapters" / "chapter-09.md").write_text(
        "---\ntitle: t\nnumber: 9\nstatus: draft\n---\n\nShe ran",
        encoding="utf-8")
    r = hook("check-prose-after-write.sh", _payload(target))
    assert r.returncode == 0
    assert "truncation" in r.stdout


def test_postwrite_apology_dialogue_not_flagged(hook, project):
    # Ordinary character dialogue: apology-shaped lines without an
    # AI-context co-occurrence are fiction, not refusal markers.
    target = _chapter(project, 9, status="draft")
    (project / "manuscript" / "chapters" / "chapter-09.md").write_text(
        "---\ntitle: t\nnumber: 9\nstatus: draft\n---\n\n"
        "\"I'm sorry,\" she said. \"I cannot continue with you.\"\n\n"
        "He watched her go without answering, because the answer she had "
        "left him was not one a person says out loud, and the road took her "
        "down past the burned annex where the story would pick her up "
        "again.\n",
        encoding="utf-8")
    r = hook("check-prose-after-write.sh", _payload(target))
    assert r.returncode == 0
    assert "refusal" not in r.stdout


def test_postwrite_refusal_with_ai_context_still_flagged(hook, project):
    # A real model refusal (AI-context co-occurring with the apology shape)
    # still fires the net.
    target = _chapter(project, 9, status="draft")
    (project / "manuscript" / "chapters" / "chapter-09.md").write_text(
        "---\ntitle: t\nnumber: 9\nstatus: draft\n---\n\n"
        "As an AI language model, I'm sorry, but I cannot continue this "
        "task. The requested content falls outside my guidelines.\n\n"
        "Padding follows so the other nets stay quiet while the refusal "
        "net fires and the advisory surfaces in the author's context.\n",
        encoding="utf-8")
    r = hook("check-prose-after-write.sh", _payload(target))
    assert "refusal" in r.stdout


def test_postwrite_emits_valid_additional_context_json(hook, project):
    target = _chapter(project, 9, status="draft")
    p = project / "manuscript" / "chapters" / "chapter-09.md"
    p.write_text(
        "---\ntitle: t\nnumber: 9\nstatus: draft\n---\n\n"
        "She stopped to delve into the realm of memory, and the tab\there "
        "jumped.\n", encoding="utf-8")
    r = hook("check-prose-after-write.sh", _payload(target))
    assert r.returncode == 0
    doc = json.loads(r.stdout.strip().split("\n")[0])
    ctx = doc["hookSpecificOutput"]["additionalContext"]
    assert "tier1" in ctx or "truncation" in ctx
    import re as _re
    assert not _re.search("[" + chr(0) + "-" + chr(9) + chr(11) + "-" + chr(31) + "]", ctx)  # raw control char (an unescaped tab) would break the JSON


def test_postwrite_voice_skip_anywhere_suppresses_debt(hook, project):
    # Regression: the marker used to be honored only in the first 8 lines.
    target = _chapter(project, 9, status="draft")
    p = project / "manuscript" / "chapters" / "chapter-09.md"
    filler = "\n".join("Filler paragraph %d." % i for i in range(12))
    p.write_text(
        "---\ntitle: t\nnumber: 9\nstatus: draft\n---\n\n" + filler +
        "\n\nShe stopped to delve into the tapestry of memory.\n"
        "<!-- voice:skip -->\n", encoding="utf-8")
    r = hook("check-prose-after-write.sh", _payload(target))
    assert r.returncode == 0
    debt = project / "work" / "voice-debt.json"
    if debt.exists():
        items = [i for i in json.loads(debt.read_text(encoding="utf-8"))
                 .get("items", []) if i.get("chapter") == "chapter-9"]
        assert items == []


def test_postwrite_acceptance_runs_closeout(hook, engine, project):
    # The acceptance edit triggers the mechanical chapter transaction:
    # wordcount --write + ledger check + state rebuild; pending_capture true.
    target = _chapter(project, 9, status="accepted")
    r = hook("check-prose-after-write.sh",
             {"tool_name": "Edit",
              "tool_input": {"file_path": target,
                             "old_string": "status: draft",
                             "new_string": "status: accepted"}})
    assert r.returncode == 0
    tracking = json.loads((project / "state" / "_tracking-state.json")
                          .read_text(encoding="utf-8"))
    assert tracking["pending_capture"] is True
    ch9 = [c for c in tracking["chapters"] if c["file"].endswith("chapter-09.md")]
    assert ch9 and ch9[0]["status"] == "accepted"


# ---------------------------------------------------------------------------
# session-stop reminder
# ---------------------------------------------------------------------------

def test_session_stop_reminds_on_pending_capture(hook, engine, project):
    engine("state", "rebuild")  # ch6 accepted -> pending true
    r = hook("session-stop.sh", {})
    assert "pending_capture" in r.stdout
    assert r.returncode == 0


def test_session_stop_silent_when_clean(hook, engine, project):
    ch6 = project / "manuscript" / "chapters" / "chapter-06.md"
    ch6.write_text(ch6.read_text(encoding="utf-8").replace(
        "status: accepted", "status: final"), encoding="utf-8")
    engine("state", "rebuild")
    r = hook("session-stop.sh", {})
    assert "pending_capture" not in (r.stdout or "")
    assert r.returncode == 0


# ---------------------------------------------------------------------------
# chapter-maintenance: transcript-targeted chapter
# ---------------------------------------------------------------------------

def test_maintenance_targets_transcript_chapter(hook, engine, project, tmp_path):
    ch6 = project / "manuscript" / "chapters" / "chapter-06.md"
    ch6.write_text(ch6.read_text(encoding="utf-8").replace(
        "status: accepted", "status: final"), encoding="utf-8")
    engine("state", "rebuild")
    ch3 = project / "manuscript" / "chapters" / "chapter-03.md"
    before = ch3.read_text(encoding="utf-8")
    # transcript mentioning chapter-03 (a revision), not the highest chapter
    tr = tmp_path / "tr.jsonl"
    tr.write_text(json.dumps({"isSidechain": False}) + "\n" +
                  json.dumps({"tool_input": {"file_path": str(ch3)}}) + "\n",
                  encoding="utf-8")
    r = hook("chapter-maintenance.sh",
             {"transcript_path": str(tr)})
    assert r.returncode == 0
    import re
    m = re.search(r"^word-count: (\d+)$", ch3.read_text(encoding="utf-8"),
                  re.MULTILINE)
    assert m and int(m.group(1)) > 0, "chapter-03 word-count must be updated"


def test_maintenance_engine_absent_falls_back(hook, engine, project):
    ch6 = project / "manuscript" / "chapters" / "chapter-06.md"
    ch6.write_text(ch6.read_text(encoding="utf-8").replace(
        "status: accepted", "status: final"), encoding="utf-8")
    engine("state", "rebuild")
    r = hook("chapter-maintenance.sh", {},
             extra_env={"VELLUM_ENGINE_OVERRIDE": _failing_engine(project)})
    assert r.returncode == 0
    assert "unavailable" in r.stderr  # names the real cause, not frontmatter


def test_maintenance_silent_on_success(hook, engine, project):
    ch6 = project / "manuscript" / "chapters" / "chapter-06.md"
    ch6.write_text(ch6.read_text(encoding="utf-8").replace(
        "status: accepted", "status: final"), encoding="utf-8")
    engine("state", "rebuild")
    r = hook("chapter-maintenance.sh", {})
    assert r.stdout == ""  # stdout goes to the transcript: silent-on-success


def test_ambiguous_transcript_fails_closed_for_gate_inputs(hook, project, tmp_path):
    # Fail-closed for the protected gate inputs: when the transcript is
    # unreadable/ambiguous (context cannot be verified), a write to the gate
    # artifacts is blocked instead of silently treated as a main session.
    tp = tmp_path / "broken.jsonl"
    tp.write_bytes(b"\xff\xfe\x00garbage")  # not JSONL with isSidechain
    target = str(project / "work" / "critique-reports" / "blind-chapter-09.md")
    r = hook("guard-outline-before-prose.sh",
             _payload(target, {"transcript_path": str(tp)}))
    assert r.returncode == 2
    assert "could not be verified" in r.stderr
    # ... but a main-session write with a confirming transcript still passes.
    r = hook("guard-outline-before-prose.sh",
             _payload(target, {"transcript_path": _transcript(tmp_path, False)}))
    assert r.returncode == 0
