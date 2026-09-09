# Tiered Slop Tables

Mechanism credited to NousResearch/autonovel; no source text or code copied. Supplemental lists adapted from `conorbronsdon/avoid-ai-writing` (MIT) and `hardikpandya/stop-slop` (MIT) — used only through the fiction-carveouts filter (`fiction-carveouts.md`). Changes: re-cast as a fiction-prose tier taxonomy; word lists re-derived and supplemented from the MIT sources; stop-slop entries kept only where they do not collide with deliberate voice register.

The post-write prose net (`check-prose-after-write.sh` / `prose_core.py`) enforces a **fiction-tuned subset of these tables** (`prose_core.py TIER1`) — the AI-frequency markers most predictive in fiction, plus the filler and tier-2 cluster patterns; business-register rows (robust, synergy, best practices, thought leadership) are deliberately left to the judgment layer. This file is the **full standing reference** for writers and critics: a row that the net does not flag mechanically is still a rewrite on sight in prose. Three tiers, one law: **the measured author profile overrides every ban** (see `voice/resources/voice-profile.md` and the measured-profile law below).

## The measured-profile law

Bans never override the measured author profile. If the author uses em-dashes at 4 per 1,000 words, 4/1k is correct for *this* book — the cap adapts to `kb/styles/baseline.md` rather than judging the author's voice a violation. Tier-1/tier-2 hits are measured against the author's own per-1k rates; only statistically significant over-shoot vs. the author's baseline is a finding. Under-shoot is reported too — you cannot edit toward a voice you haven't measured.

`<!-- voice:skip -->` anywhere in a chapter suppresses tier-1 debt accrual for that chapter (author escape hatch for deliberate register choices).

## Tier 1 — kill on sight

These are statistically overrepresented in LLM output vs. human prose. One appearance is enough to flag; in an accepted chapter, rewrite the sentence. Split into two bands — both are always replaced, but a flag means different things:

- **1A — AI-frequency markers**: a cluster of these is evidence about how a passage was produced.
- **1B — clarity edits**: wordiness and inflated formality. Good writing regardless of authorship; a 1B hit is **not** evidence of machine origin.

### Tier 1A — AI frequency markers

| Replace | With |
|---|---|
| delve / delve into | dig into, look at, examine |
| landscape (metaphor) | field, space, situation |
| tapestry (of) | describe the actual thing |
| realm | area, field, domain |
| paradigm | model, approach, framework |
| embark (on) | start, begin |
| testament (to) | shows, proves, demonstrates |
| robust | strong, solid, reliable |
| comprehensive | thorough, complete, full |
| cutting-edge | latest, newest, advanced |
| leverage (verb) | use |
| pivotal | important, key, central |
| underscores | highlights, shows |
| meticulous / meticulously | careful, detailed, precise |
| seamless / seamlessly | smooth, easy, without friction |
| game-changer / game-changing | describe what specifically changed |
| nestled | is located, sits, is in |
| vibrant | describe what makes it active, or cut |
| thriving | growing, active (or cite a number) |
| showcasing | showing, demonstrating (or cut the clause) |
| deep dive / dive into | look at, examine, explore |
| unpack / unpacking | explain, break down, walk through |
| bustling | busy, active (or cite what makes it busy) |
| intricate / intricacies | complex, detailed (or name the specific complexity) |
| ever-evolving | changing, growing (or describe how) |
| enduring | lasting, long-running (or cite how long) |
| daunting | hard, difficult, challenging |
| holistic / holistically | complete, full, whole (or describe what is included) |
| actionable | practical, useful, concrete |
| impactful | effective, significant (or describe the impact) |
| synergy / synergies | describe the actual combined effect |
| interplay | relationship, connection, interaction |
| genuinely / genuine (as intensifier) | cut — just state the fact |
| symphony (metaphor) | describe the actual coordination |
| embrace (metaphor) | adopt, accept, use, switch to |
| beacon (metaphor) | example, guide (name what provides it) |
| cornerstone | foundation, basis, core |
| paramount | most important, top priority |
| overarching | main, central, broad |
| burgeoning | growing, emerging (or cite a number) |
| nascent | new, early-stage, emerging |
| quintessential | typical, classic, defining |
| revolutionize | change, transform, reshape (or describe what changed) |
| illuminate | clarify, explain, show |
| elucidate | explain, clarify, spell out |
| juxtapose | compare, contrast, set side by side |
| transformative / transformation | describe what changed and how |
| unprecedented | name the precedent it breaks (or cut) |
| exceptional / exceptionally | cite what makes it an exception |
| remarkable / remarkably | say what is worth remarking on |
| sophisticated | describe the sophistication |
| instrumental | say what role it played |
| the future looks bright | cut — say something specific or nothing |
| only time will tell | cut — say something specific or nothing |
| at its core | cut — just state the thing |
| thought leader / thought leadership | expert, authority (or describe the contribution) |
| best practices | what works, proven methods, standard approach |

### Tier 1B — clarity edits (wordiness, not authorship evidence)

| Replace | With |
|---|---|
| utilize | use |
| in order to | to |
| due to the fact that | because |
| serves as | is |
| features (verb) | has, includes |
| boasts | has |
| presents (inflated) | is, shows, gives |
| commence | start, begin |
| ascertain | find out, determine, learn |
| endeavor | effort, attempt, try |

## Tier 2 — suspicious in clusters of three

Fine alone. Two or more in the same paragraph is a strong signal; three in one paragraph = rewrite that paragraph. These are legitimate words that AI simply overuses.

| Replace | With |
|---|---|
| harness | use, take advantage of |
| navigate / navigating | work through, handle, deal with |
| foster | encourage, support, build |
| elevate | improve, raise, strengthen |
| unleash | release, enable, unlock |
| streamline | simplify, speed up |
| empower | enable, let, allow |
| bolster | support, strengthen, back up |
| spearhead | lead, drive, run |
| resonate / resonates with | connect with, appeal to, matter to |
| facilitate / facilitates | enable, help, allow, run |
| underpin / underpinnings | support, form the basis of, foundation |
| nuanced (as vague praise) | specific, subtle, detailed (or name the actual nuance) |
| crucial | important, key, necessary |
| multifaceted | describe the actual facets, or cut |
| ecosystem (metaphor) | system, community, network, market |
| myriad | many, numerous (or give a number) |
| plethora | many, a lot of (or give a number) |
| encompass | include, cover, span |
| catalyze | start, trigger, accelerate |
| reimagine | rethink, redesign, rebuild |
| galvanize | motivate, rally, push |
| augment | add to, expand, supplement |
| cultivate | build, develop, grow |
| quiet (as in "quietly, ...") | cut, or name the concrete contrast |
| poised (to) | ready, set, about to |

## Tier 3 — filler phrases (delete on sight)

These add zero information. The sentence is always better without them. Adapted from `hardikpandya/stop-slop` (MIT) and `conorbronsdon/avoid-ai-writing` (MIT); nonfiction-tuned entries filtered through `fiction-carveouts.md`.

- "It's worth noting that..." → just state it
- "It's important to note that..." → just state it
- "Importantly, ..." / "Notably, ..." / "Interestingly, ..." → just state it
- "Let's dive into..." / "Let's explore..." / "Let's examine..." → start with the content
- "As we can see..." → they can see
- "Furthermore, ..." / "Moreover, ..." / "Additionally, ..." → and, also, or just start a new sentence
- "In today's [fast-paced/digital/modern] world..." → delete the clause
- "At the end of the day..." → delete
- "It goes without saying..." → then don't say it
- "When it comes to..." → just talk about the thing
- "One might argue that..." → argue it or don't
- "Not just X, but Y" → restructure (the #1 LLM rhetorical crutch)
- "In conclusion, ..." / "To summarize, ..." → the reader knows
- "As mentioned earlier..." → reference the thing directly, or cut
- "This matters because" → only when it introduces a concrete consequence; cut empty restatements

## Structural slop patterns

Shapes that betray machine origin in any voice. Detector mechanics for these live in `prose_core.py` (adapted from `conorbronsdon/avoid-ai-writing/detector/patterns.js`, MIT — categories, not verbatim code).

- **Paragraph-template machine**: topic sentence → elaboration → example → wrap-up, repeated. Vary it — point last, one-sentence paragraphs, three long ones in a row.
- **Sentence-length uniformity**: every sentence 15–25 words reads synthetic. Mix fragments and long, clause-heavy sentences. Measured as burstiness (sentence-length sd/mean) in `style stats`.
- **Transition-word addiction**: consecutive paragraphs opening with "However / Furthermore / Additionally / Moreover / Nevertheless" → rewrite; start with subject, action, dialogue, sense detail.
- **Symmetry addiction**: three pros, three cons, five steps. Real writing is lumpy.
- **Hedge parade**: "may / might / could potentially / it's possible that" — pick one per page, max.
- **Em-dash overload**: more than ~2 per page is a tell (rate adapts to the author's measured baseline).
- **List abuse**: prose, not bullets — earn every list.
- **"Not just X, but Y"**: the single most overused LLM rhetorical pattern. Kill it.
- **Sycophantic openings**: "Great question!", "Absolutely!", "You raise an important consideration." — these are chat-interface tics, not prose.

## The smell test

After any passage, ask (mechanism credited to NousResearch/autonovel; rewritten):
- Read it aloud. Does it sound like a person talking?
- Is there a single surprising sentence? Human writing surprises.
- Does it say something specific? Could you swap the topic and the words would still work? Specificity kills slop.
- Would a reader think "AI wrote this"? If yes, rewrite.
