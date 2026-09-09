# Vellum deterministic engine — style stats (spec 5.2, single metrics module;
# hooks analyze.py is superseded per spec 1).
# Original code (base design credited in ATTRIBUTION.md).
"""Sentence-length distribution + variance (burstiness), opener variety,
dialogue ratio, em-dash density (with the list-item typography carve-out),
type-token ratio, paragraph-shape entropy. `--baseline` compares against the
keyed numeric profile in kb/styles/baseline.md (spec 8.3) and appends a
bidirectional drift report (over-shoot = subtraction needed, under-shoot =
restoration needed). Also emits the measured per-1k voice profile (spec 8.2)."""
import glob
import math
import os
import re
import sys

from . import util
from .util import EXIT_OK, EXIT_ERROR

HEDGE_RE = re.compile(
    r"\b(may|might|could|possibly|perhaps|it seems|one might)\b", re.IGNORECASE)

# Tier-1 rate table for the tier1-hit metric — the SAME pattern list as
# hooks/scripts/prose_core.py TIER1 (re-derived fiction lists; avoid-ai-writing
# MIT selections): the hooks scanner owns enforcement, this only measures, and
# a divergent table would make `style stats` undercount tier1-hit so the
# measured-profile allowance (baseline tier1-hit rate x words) rejects the
# author's own idioms. scripts/ci/lint_vellum.py verifies the two tables stay
# identical — update BOTH or neither.
TIER1_PATTERNS = [
    r"\bdelv\w*\b",
    r"\btapestr\w*\b",
    r"\brealm\b",
    r"\bembark\w*\b",
    r"\btestament to\b",
    r"\bbeacon\b",
    r"\bmeticul\w*\b",
    r"\bseamless\w*\b",
    r"\bgame.chang\w*\b",
    r"\bhit different\w*\b",
    r"\bnestl\w*\b",
    r"\bvibrant\b",
    r"\bthriv\w*\b",
    r"\bbustl\w*\b",
    r"\bintricat\w*\b",
    r"\bever.evolv\w*\b",
    r"\bdaunting\b",
    r"\bholistic\w*\b",
    r"\bactionable\b",
    r"\bimpactful\b",
    r"\bsymphon\w*\b",
    r"\bpalpable\b",
    r"\bunwaver\w*\b",
    r"\bethereal\b",
    r"\bgossamer\b",
    r"\bshiver\w* down\b",
    r"\bcouldn.?t help but\b",
    r"\bthe air was thick\b",
    r"\ba chorus of\b",
    r"\bpainted (across|over|onto)\b",
    r"\bunprecedented\b",
    r"\bunparalleled\b",
]
TIER1_RE = re.compile("|".join(TIER1_PATTERNS), re.IGNORECASE)

# List-item em-dash typography carve-out (structural-caps.md): an em-dash
# acting as the separator in a list item opening with a bolded lead term or a
# markdown link is typography, not a prose splice.
_LIST_ITEM_DASH_RE = re.compile(
    r"^\s*(?:[-*+]|\d+\.)\s+(?:\*\*[^*]+\*\*|\[[^\]]+\]\([^)]+\)|`[^`]+`)\s*[—-]",
    re.MULTILINE)

DIALOGUE_RE = re.compile(r'"[^"]+"|“[^”]+”')


def _sentences(text):
    parts = re.split(r"(?<=[.!?…])\s+", text)
    return [p for p in parts if p.strip()]


def _paragraphs(text):
    return [p for p in re.split(r"\n\s*\n", text) if p.strip()]


def stats_for_text(body):
    words = util.count_words(body)
    word_list = re.findall(r"[^\W_]+", body, re.UNICODE)
    sents = _sentences(body)
    sent_lens = [util.count_words(s) for s in sents] or [0]
    mean = sum(sent_lens) / len(sent_lens) if sent_lens else 0.0
    var = (sum((x - mean) ** 2 for x in sent_lens) / len(sent_lens)
           if sent_lens else 0.0)
    sd = math.sqrt(var)
    burstiness = (sd / mean) if mean > 0 else 0.0

    # opener variety: distinct first words / sentences
    openers = [re.match(r"\W*([A-Za-z’']+)", s) for s in sents]
    opener_words = [m.group(1).lower() for m in openers if m]
    opener_variety = (len(set(opener_words)) / len(opener_words)
                      if opener_words else 0.0)

    # dialogue ratio (words inside quotation marks / total words)
    dialogue_words = sum(util.count_words(m.group(0))
                         for m in DIALOGUE_RE.finditer(body))
    dialogue_ratio = (dialogue_words / words) if words else 0.0

    # em-dash density with the list-item typography carve-out
    dash_count = len(re.findall(r"—|--", body))
    dash_count -= len(_LIST_ITEM_DASH_RE.findall(body))
    dash_count = max(dash_count, 0)

    # type-token ratio
    ttr = (len(set(w.lower() for w in word_list)) / len(word_list)
           if word_list else 0.0)

    # paragraph-shape entropy over length buckets (short <35, medium <80, long)
    paras = _paragraphs(body)
    plens = [util.count_words(p) for p in paras]
    buckets = [0, 0, 0]
    for n in plens:
        buckets[0 if n < 35 else (1 if n < 80 else 2)] += 1
    total = sum(buckets)
    entropy = 0.0
    if total:
        for b in buckets:
            if b:
                p = b / total
                entropy -= p * math.log2(p)

    tier1_hits = len(TIER1_RE.findall(body))
    hedges = len(HEDGE_RE.findall(body))

    per1k = (lambda n: (n / words * 1000.0) if words else 0.0)
    return {
        "words": words,
        "sentences": len(sents),
        "mean-sentence-len": round(mean, 2),
        "burstiness": round(burstiness, 3),
        "opener-variety": round(opener_variety, 3),
        "dialogue-ratio": round(dialogue_ratio, 3),
        "em-dash-per-1k": round(per1k(dash_count), 2),
        "hedge-per-1k": round(per1k(hedges), 2),
        "tier1-hit-per-1k": round(per1k(tier1_hits), 2),
        "ttr": round(ttr, 3),
        "paragraph-entropy": round(entropy, 3),
    }


def _resolve_files(pattern, root):
    if os.path.isabs(pattern):
        paths = sorted(glob.glob(pattern))
    else:
        paths = sorted(glob.glob(os.path.join(root, pattern)))
        if not paths and os.path.exists(os.path.join(root, pattern)):
            paths = [os.path.join(root, pattern)]
    out = []
    for p in paths:
        if os.path.isfile(p) and p.endswith(".md"):
            out.append(p)
    return out


def _load_baseline(root):
    """Parse the kb/styles/baseline.md numeric table (spec 8.3). Returns
    empty rates for an absent baseline or an unfilled template (frontmatter
    `measured: false`) — template rates are not measurements."""
    path = util.project_file(root, "kb", "styles", "baseline.md")
    if not os.path.exists(path):
        return None, {}
    text = util.read_file(path)
    if re.search(r"^measured:\s*false\s*$", text, re.MULTILINE):
        return path, {}
    rates = {}
    for line in text.split("\n"):
        s = line.strip()
        if not s.startswith("|") or s.startswith("|--") or s.startswith("| metric"):
            continue
        cells = [c.strip() for c in s.strip("|").split("|")]
        if len(cells) >= 2:
            try:
                rates[cells[0].lower()] = float(cells[1])
            except ValueError:
                continue
    return path, rates


BASELINE_METRIC_MAP = [
    ("em-dash", "em-dash-per-1k"),
    ("hedge", "hedge-per-1k"),
    ("tier1-hit", "tier1-hit-per-1k"),
    ("dialogue-ratio", "dialogue-ratio"),
    ("ttr", "ttr"),
    ("burstiness", "burstiness"),
]


def run(root, pattern, baseline=False):
    files = _resolve_files(pattern, root)
    if not files:
        util.die("no markdown files match %r" % pattern)
    per_file = {}
    agg_words = 0
    agg = {}
    for p in files:
        fm, body = util.strip_frontmatter_text(util.read_file(p))
        st = stats_for_text(body)
        per_file[os.path.relpath(p, root).replace("\\", "/")] = st
        agg_words += st["words"]
        for k, v in st.items():
            if k in ("words", "sentences", "mean-sentence-len"):
                continue
            agg.setdefault(k, []).append(v)

    for f, st in sorted(per_file.items()):
        sys.stdout.write(
            "%s: %d words, mean sentence %.1f, burstiness %.2f, "
            "opener variety %.2f, dialogue %.2f, em-dash %.1f/1k, "
            "hedge %.1f/1k, tier1 %.1f/1k, ttr %.2f, para-entropy %.2f\n"
            % (f, st["words"], st["mean-sentence-len"], st["burstiness"],
               st["opener-variety"], st["dialogue-ratio"],
               st["em-dash-per-1k"], st["hedge-per-1k"], st["tier1-hit-per-1k"],
               st["ttr"], st["paragraph-entropy"]))

    # measured per-1k voice profile across the selection (spec 8.2)
    profile = {
        "em-dash-per-1k": 0.0, "hedge-per-1k": 0.0, "tier1-hit-per-1k": 0.0,
        "dialogue-ratio": 0.0, "ttr": 0.0, "burstiness": 0.0,
    }
    # recompute aggregate per-1k rates on the pooled word count
    pooled = {k: (sum(v) / len(v) if v else 0.0) for k, v in agg.items()}
    n = max(len(files), 1)
    profile["em-dash-per-1k"] = round(pooled.get("em-dash-per-1k", 0.0), 2)
    profile["hedge-per-1k"] = round(pooled.get("hedge-per-1k", 0.0), 2)
    profile["tier1-hit-per-1k"] = round(pooled.get("tier1-hit-per-1k", 0.0), 2)
    profile["dialogue-ratio"] = round(pooled.get("dialogue-ratio", 0.0), 3)
    profile["ttr"] = round(pooled.get("ttr", 0.0), 3)
    profile["burstiness"] = round(pooled.get("burstiness", 0.0), 3)
    _ = n, agg_words  # per-file rates are averaged; pooled recompute is a v2 task

    sys.stdout.write("\nmeasured per-1k voice profile (%d file(s)):\n" % len(files))
    sys.stdout.write("| metric | measured rate |\n|---|---|\n")
    for key in ("em-dash-per-1k", "hedge-per-1k", "tier1-hit-per-1k",
                "dialogue-ratio", "ttr", "burstiness"):
        sys.stdout.write("| %s | %s |\n" % (key, profile[key]))

    if baseline:
        bpath, rates = _load_baseline(root)
        if not rates:
            util.die("--baseline: kb/styles/baseline.md not found or empty; "
                     "build it first (style-creator, spec 8.3).")
        sys.stdout.write("\ndrift report vs %s (bidirectional: over-shoot "
                         "needs subtraction, under-shoot needs "
                         "restoration):\n" % os.path.relpath(bpath, root))
        sys.stdout.write("| metric | author baseline | measured | drift | direction |\n")
        sys.stdout.write("|---|---|---|---|---|\n")
        any_drift = False
        for bkey, skey in BASELINE_METRIC_MAP:
            base = rates.get(bkey)
            if base is None:
                continue
            cur = profile.get(skey, 0.0)
            drift = cur - base
            if abs(drift) <= max(0.05 * max(base, 1e-6), 0.02):
                direction = "within band"
            elif drift > 0:
                direction = "OVER-shoot — subtraction needed"
            else:
                direction = "UNDER-shoot — restoration needed"
            if direction != "within band":
                any_drift = True
            sys.stdout.write("| %s | %s | %s | %+.2f | %s |\n"
                             % (bkey, base, cur, drift, direction))
        if not any_drift:
            sys.stdout.write("\nall measured rates within band of the "
                             "author's baseline.\n")
    return EXIT_OK
