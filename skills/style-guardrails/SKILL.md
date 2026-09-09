---
name: style-guardrails
description: |
  Load for the writer and critics before drafting or critiquing prose; also drives the post-write net. The fiction-specific anti-slop reference: tiered word tables, structural caps, smell tests, and the carve-out filter that keeps the mechanical net from flattening voice. Load whenever prose is being produced, reviewed, or scored.
---

# Style Guardrails

The fiction-specific layer that keeps prose from reading as machine-generated. It has two halves: a **mechanical net** (scripts — deterministic, cheap, run on every prose write) and a **judgment layer** (these resources — loaded by writers and critics). The net catches what regex can; the judgment layer catches what regex can't. Both halves are governed by one law: **the measured author profile overrides every ban** (`voice/resources/voice-profile.md`).

## What this skill is

- A **reference**, not a pipeline. Nothing here runs automatically except the scripts it points at.
- **Self-contained**. It restates the measured-profile law and the carve-out logic so a writer or critic can apply them without loading another skill. Cross-references to `voice/` and `creative-writing-craft/` are pointers only — the content needed to act is here.
- **Fiction-tuned**. The underlying word lists and structural patterns come from general-purpose AI-slop detectors (autonovel, avoid-ai-writing, stop-slop); this skill filters them through a fiction lens so the net never flattens a deliberate voice.

## Load the resource needed

- `resources/tiers.md` — Tier-1 kill-on-sight, Tier-2 suspicious-in-clusters-of-three, Tier-3 filler tables; the measured-profile law; structural slop patterns; the smell test. The standing vocabulary reference for writers and critics.
- `resources/structural-caps.md` — numeric thresholds with fiction tuning: em-dashes per page, hedges per page, sentence-length variance (burstiness), consecutive-paragraph-opener repetition, paragraph-length uniformity, negative-setup/positive-flip shape, and the named structural anti-patterns (triadic listing, over-explain, cataloging-by-thinking, etc.).
- `resources/smell-tests.md` — four tests (read aloud, surprise, specificity, "AI wrote this?") with concrete procedures and their mapping to the mechanical net.
- `resources/fiction-carveouts.md` — the exemption rubric: when a "tell" is a voice (unreliable narrator, period dialogue, regional register, close psychic distance, stylized narration); the `<!-- voice:skip -->` escape hatch; what the carve-outs never excuse; dismissal vs. deletion.

## How the halves fit together

1. **Writer drafts** with `kb/styles/voice.md` and these guardrails in context.
2. **Post-write net** (`check-prose-after-write.sh` → `prose_core.py`) runs the mechanical scan: Tier-1/tier-2 vocabulary, filler, em-dash density, duplicated lines, truncation/refusal/placeholder markers. (Burstiness and opener variety are **report-only metrics** in `vellum style stats`, not net findings — the opener-repetition and paragraph-uniformity caps in `structural-caps.md` are judgment-layer diagnostics.) Advisory by default; writes `work/voice-debt.json`. Silent when clean.
3. **Critic** loads these resources *before* reading, judges execution against them, and emits findings in the shared schema (`gates/resources/finding-schema.md`).
4. **Muse** synthesizes. When a finding conflicts with the author's measured profile or a declared voice register, the carve-out rubric resolves it — and the author's word is ground truth (GR-09).

## The measured-profile law (restated)

Bans never override the measured author profile. Caps adapt to `kb/styles/baseline.md` (the author's own per-1k rates) rather than judging the author's voice a violation. Tier hits are measured against the author's baseline; only statistically significant over-shoot is a finding, and under-shoot is reported too. See `voice/resources/voice-profile.md` for how the baseline is built and how drift reports use it.
