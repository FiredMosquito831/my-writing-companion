# Fixture project: tests/fixtures/sample-project

Seeded by `seed.py` (run it directly, or let `tests/conftest.py` seed a fresh
copy per test). One instance of every deterministic error class, per
design-spec.md section 14:

| Error class | Where |
|---|---|
| dead-character reappearance | character-old-tom (died ch 1) in ch 3 `characters:` |
| promise planted after payoff | kb/promises/promise-late-payoff.md |
| unfired setup past target-by | kb/promises/promise-overdue-setup.md |
| dormant promise | kb/promises/promise-dormant-thread.md (+overdue-setup) |
| POV-not-in-cast | chapter-02 (pov character-vess not in cast) |
| prop custody drift | kb/props/prop-destroyed-lantern.md listed in ch 5/6 `custody:` |
| knowledge learned-in violation | kb/knowledge/knowledge-bad-learned.md (vess learned-in ch 5, not in ch 5 cast) |
| clock non-monotonicity | kb/clock.md thread debt-run (started ch 3, last ch 1) |
| schema violation | kb/characters/character-bad-schema.md (status: undead) |
| frontmatter-incomplete | chapter-04 (missing characters/mentions/promises-advanced, 200+ words) |
| broken cross-reference | chapter-02 mentions character-ghost-ref (does not exist) |
| word-band violation | every fixture chapter (~273 words vs 3200 target) |
| hand-edited state | produced by test (tamper with state files after rebuild) |
| exemption active vs stale | produced by tests (dismiss + manual stale entry) |

Outline-verbatim check: chapter-06 (accepted) misses its outline's verbatim
line. The `knowledge --as-of` dramatic-irony query is exercised against
knowledge-bad-learned (audience knows, Mira does not).
