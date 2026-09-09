# Seed script for the sample fixture project (design-spec.md section 14).
# Run: python seed.py <target-dir>
# Seeds one instance of every deterministic error class so test_engine can
# assert exact finding keys. Imported by tests/conftest.py as well.
import json
import os
import sys

FILLER = ("She counted the coins twice, then again. The road north was closed "
          "since the frost, and the ferryman wanted silver he had not earned. "
          "Mira pulled her collar up and said nothing. Old trouble keeps its "
          "own schedule, her mother used to say. The wind came off the water "
          "and took the warmth with it. She thought about the ring in her "
          "pocket, how it had weight now, more than metal. Somewhere behind "
          "her a door slammed. She did not look back. The town smelled of "
          "tar and wet rope, and gulls argued over something dead on the "
          "steps. She walked. The road did not care what she owed or to "
          "whom, and that was almost a comfort. By the second mile the rain "
          "found her, thin and sideways, and the road turned to mud. "
          "At the toll bridge a boy sat under the arch with a cup of "
          "something hot, and he watched her pass the way watchmen watch, "
          "not curious, just doing the work. She paid the toll with two of "
          "the coins and got one back, bitten, which told her everything "
          "about the bridge keeper's opinions of strangers. The far bank "
          "was a line of black pines, and the wind moved through them like "
          "it was reading. She kept walking. Her boots were wrong for this "
          "weather and her coat was wrong for this road, and none of it "
          "mattered, because the letter in her inner pocket was dry, and "
          "dry was the only thing that counted. Twice she stopped and "
          "listened for the dog. Twice there was nothing, which was worse "
          "than barking. Dusk came down like a lid.")

CHAPTERS = {
    1: {
        "fm": ('---\ntitle: "The Ferry"\nnumber: 1\nstatus: final\n'
               'approved-outline: work/outline/chapter-01.md\n'
               'pov: character-mira-tarn\n'
               'characters: [character-mira-tarn, character-old-tom]\n'
               'mentions: [character-vess]\n'
               'promises-advanced: [promise-ring-of-oath]\n'
               'word-target: 3200\nword-count: null\n---\n'),
        "body": FILLER,
    },
    # POV-not-in-cast: pov not in characters; broken ref via mentions
    2: {
        "fm": ('---\ntitle: "The Road"\nnumber: 2\nstatus: final\n'
               'approved-outline: work/outline/chapter-02.md\n'
               'pov: character-vess\n'
               'characters: [character-mira-tarn]\n'
               'mentions: [character-ghost-ref]\n'
               'promises-advanced: [promise-overdue-setup]\n'
               'word-target: 3200\nword-count: null\n---\n'),
        "body": FILLER,
    },
    # dead-character reappearance: old-tom (died ch 1) in-scene in ch 3
    3: {
        "fm": ('---\ntitle: "The Grave"\nnumber: 3\nstatus: final\n'
               'approved-outline: work/outline/chapter-03.md\n'
               'pov: character-mira-tarn\n'
               'characters: [character-mira-tarn, character-old-tom]\n'
               'mentions: []\n'
               'promises-advanced: []\n'
               'word-target: 3200\nword-count: null\n---\n'),
        "body": FILLER,
    },
    # frontmatter-incomplete (missing characters/mentions/promises-advanced)
    4: {
        "fm": ('---\ntitle: "The Crossing"\nnumber: 4\nstatus: final\n'
               'approved-outline: work/outline/chapter-04.md\n'
               'pov: character-mira-tarn\n'
               'word-target: 3200\nword-count: null\n---\n'),
        "body": FILLER,
    },
    # word-band violation: 250 words against a 3200 target
    5: {
        "fm": ('---\ntitle: "The Toll"\nnumber: 5\nstatus: final\n'
               'approved-outline: work/outline/chapter-05.md\n'
               'pov: character-mira-tarn\n'
               'characters: [character-mira-tarn]\n'
               'mentions: []\n'
               'promises-advanced: [promise-late-payoff]\n'
               'custody: [prop-destroyed-lantern]\n'
               'word-target: 3200\nword-count: null\n---\n'),
        "body": FILLER,
    },
    # accepted chapter missing an outline-verbatim line (outline ch6 lists one)
    6: {
        "fm": ('---\ntitle: "The Gate"\nnumber: 6\nstatus: accepted\n'
               'approved-outline: work/outline/chapter-06.md\n'
               'pov: character-mira-tarn\n'
               'characters: [character-mira-tarn]\n'
               'mentions: []\n'
               'promises-advanced: [promise-overdue-setup]\n'
               'custody: [prop-destroyed-lantern]\n'
               'word-target: 3200\nword-count: null\n---\n'),
        "body": FILLER,
    },
}

CHARACTERS = {
    "character-mira-tarn": (
        "---\nid: character-mira-tarn\ntype: character\nname: \"Mira Tarn\"\n"
        "status: alive\ndied-in: null\naliases: []\npov-eligible: true\n---\n"
        "POV character. Carrier of the ring.\n"),
    "character-old-tom": (
        "---\nid: character-old-tom\ntype: character\nname: \"Old Tom\"\n"
        "status: deceased\ndied-in: chapter-01\naliases: [\"Thomas Reave\"]\n"
        "pov-eligible: false\n---\n\nDied in chapter 1.\n"),
    "character-vess": (
        "---\nid: character-vess\ntype: character\nname: \"Vess\"\n"
        "status: alive\ndied-in: null\naliases: []\npov-eligible: true\n---\n"
        "Rival courier.\n"),
    # schema violation: invalid status enum + bad id casing caught by validate
    "character-bad-schema": (
        "---\nid: character-bad-schema\ntype: character\nname: \"Bad\"\n"
        "status: undead\ndied-in: null\naliases: []\npov-eligible: true\n---\n"
        "Deliberate schema violation for the fixture.\n"),
}

PROMISES = {
    # valid promise (referenced by chapter-01): planted, target in the future
    "promise-ring-of-oath": (
        "---\nid: promise-ring-of-oath\ntype: promise\n"
        "title: \"The ring must be returned to the House\"\nstatus: planted\n"
        "planted-in: chapter-01\nreinforced: [chapter-04]\npayoff-in: null\n"
        "target-by: chapter-09\nabandoned-reason: null\n---\n\n"
        "The promise as the reader experiences it.\n"),
    # promise planted after payoff (ordering violation)
    "promise-late-payoff": (
        "---\nid: promise-late-payoff\ntype: promise\n"
        "title: \"The debt repaid\"\nstatus: planted\n"
        "planted-in: chapter-05\nreinforced: []\npayoff-in: chapter-03\n"
        "target-by: null\nabandoned-reason: null\n---\n\nOrdering violation.\n"),
    # unfired setup past target-by
    "promise-overdue-setup": (
        "---\nid: promise-overdue-setup\ntype: promise\n"
        "title: \"The letter delivered\"\nstatus: planted\n"
        "planted-in: chapter-02\nreinforced: []\npayoff-in: null\n"
        "target-by: chapter-04\nabandoned-reason: null\n---\n\n"
        "Overdue setup.\n"),
    # dormant: planted ch 2, no reinforcement, latest chapter 6
    "promise-dormant-thread": (
        "---\nid: promise-dormant-thread\ntype: promise\n"
        "title: \"The sister's promise\"\nstatus: planted\n"
        "planted-in: chapter-02\nreinforced: []\npayoff-in: null\n"
        "target-by: null\nabandoned-reason: null\n---\n\nDormant thread.\n"),
}

QUESTIONS = {
    "question-bad-state": (
        "---\nid: question-bad-state\ntype: question\n"
        "title: \"Who burned the annex?\"\nstatus: answered\n"
        "raised-in: chapter-02\nanswered-in: null\nanswer: null\n---\n\n"
        "Answered without answered-in/answer.\n"),
}

KNOWLEDGE = {
    # learned-in violation: holder learned it in ch 5 but is not in ch5 cast
    "knowledge-bad-learned": (
        "---\nid: knowledge-bad-learned\ntype: knowledge\n"
        "title: \"Vess reads the manifests\"\n"
        "statement: \"Vess can read the harbor manifests.\"\n"
        "holders:\n  - character: character-vess\n    learned-in: chapter-05\n"
        "    certainty: knows\naudience-learned-in: chapter-05\n"
        "superseded-by: null\n---\n\nLearned-in violation.\n"),
}

PROPS = {
    # custody drift: destroyed prop still listed in ch5/ch6 custody:
    "prop-destroyed-lantern": (
        "---\nid: prop-destroyed-lantern\ntype: prop\n"
        "title: \"Harbor lantern\"\nintroduced-in: chapter-02\n"
        "custody:\n  owner: character-mira-tarn\n  location: \"the mud\"\n"
        "  status: destroyed\nhistory:\n  - {chapter: 3, change: \"Shattered\"}\n"
        "---\n\nDestroyed but still carried.\n"),
}

OUTLINES = {
    # approved outline for ch 6 whose verbatim line is absent from ch 6
    6: ('---\nchapter: 6\ntitle: "The Gate"\napproved: true\npivotal: false\n'
        'word-target: 3200\nverbatim:\n  - "THIS VERBATIM LINE IS NOT IN THE CHAPTER"\n'
        '---\n## Beats\n1. Gate stand-off — quota 3200 — POV Mira\n'),
    1: ('---\nchapter: 1\ntitle: "The Ferry"\napproved: true\npivotal: false\n'
        'word-target: 3200\nverbatim: []\n---\n## Beats\n1. Ferry — quota 3200\n'),
    2: ('---\nchapter: 2\ntitle: "The Road"\napproved: true\npivotal: false\n'
        'word-target: 3200\nverbatim: []\n---\n## Beats\n1. Road — quota 3200\n'),
    3: ('---\nchapter: 3\ntitle: "The Grave"\napproved: true\npivotal: false\n'
        'word-target: 3200\nverbatim: []\n---\n## Beats\n1. Grave — quota 3200\n'),
    4: ('---\nchapter: 4\ntitle: "The Crossing"\napproved: true\npivotal: false\n'
        'word-target: 3200\nverbatim: []\n---\n## Beats\n1. Crossing — quota 3200\n'),
    5: ('---\nchapter: 5\ntitle: "The Toll"\napproved: true\npivotal: false\n'
        'word-target: 3200\nverbatim: []\n---\n## Beats\n1. Toll — quota 3200\n'),
}


def _write(path, content):
    d = os.path.dirname(path)
    if d and not os.path.isdir(d):
        os.makedirs(d, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(content)


def seed(root):
    for num, c in CHAPTERS.items():
        _write(os.path.join(root, "manuscript", "chapters",
                            "chapter-%02d.md" % num), c["fm"] + c["body"])
    for cid, content in CHARACTERS.items():
        _write(os.path.join(root, "kb", "characters", cid + ".md"), content)
    for pid, content in PROMISES.items():
        _write(os.path.join(root, "kb", "promises", pid + ".md"), content)
    for qid, content in QUESTIONS.items():
        _write(os.path.join(root, "kb", "questions", qid + ".md"), content)
    for kid, content in KNOWLEDGE.items():
        _write(os.path.join(root, "kb", "knowledge", kid + ".md"), content)
    for prid, content in PROPS.items():
        _write(os.path.join(root, "kb", "props", prid + ".md"), content)
    for num, content in OUTLINES.items():
        _write(os.path.join(root, "work", "outline",
                            "chapter-%02d.md" % num), content)
    _write(os.path.join(root, "kb", "story.md"),
           '---\ntitle: "The Salt Road"\nschema-version: 2\n'
           'book-uuid: "6f1c6e2e-0000-4000-8000-000000000001"\n'
           'author: "Fixture Author"\nyear: 2026\n---\n\nPremise prose.\n')
    _write(os.path.join(root, "kb", "clock.md"),
           "| thread | started | position as of | clock reading | last chapter |\n"
           "|---|---|---|---|---|\n"
           "| siege-countdown | ch 4 | day 9 of 30 | 21 days remain | 7 |\n"
           "| debt-run | ch 3 | day 2 | grows | 1 |\n")
    _write(os.path.join(root, "kb", "project-config.json"), json.dumps(
        {"drift_interval": 5, "voice_debt_gate": False, "stop_gate": False,
         "default_word_target": 3200, "word_band": 0.15}, indent=2) + "\n")
    _write(os.path.join(root, "kb", "exemptions.json"), json.dumps(
        {"schema_version": 1, "exemptions": []}, indent=2) + "\n")
    _write(os.path.join(root, "kb", "styles", "baseline.md"),
           "---\nschema-version: 1\nsample-chapters: [1,2,3]\n---\n"
           "| metric | author rate (per 1k words) |\n|---|---|\n"
           "| em-dash | 2.1 |\n| hedge | 0.8 |\n| tier1-hit | 0.0 |\n"
           "| dialogue-ratio | 0.38 |\n| ttr | 0.51 |\n| burstiness | 0.62 |\n")
    for d in ("state", os.path.join("work", "critique-reports"),
              os.path.join("work", "cold-reads", "2026-09"),
              os.path.join("work", "drafts"), "export"):
        os.makedirs(os.path.join(root, d), exist_ok=True)


if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else "."
    seed(target)
    print("seeded %s" % os.path.abspath(target))
