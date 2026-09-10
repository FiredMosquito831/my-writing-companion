# Vellum deterministic engine — style stats (spec 5.2, single metrics module;
# hooks analyze.py is superseded per spec 1).
# Original code (base design credited in ATTRIBUTION.md).
"""Sentence-length distribution + variance (burstiness), opener variety,
dialogue ratio, em-dash density (with the list-item typography carve-out),
type-token ratio, paragraph-shape entropy. `--baseline` compares against the
keyed numeric profile in kb/styles/baseline.md (spec 8.3) and appends a
bidirectional drift report (over-shoot = subtraction needed, under-shoot =
restoration needed). Also emits the measured per-1k voice profile (spec 8.2).

`--dialogue` (ADD-5) emits per-speaker dialogue stats (mean utterance length,
TTR, top idiolect tokens) over both dialogue conventions (dash-introduced
lines and quoted speech), with speaker-nearest-narration attribution only;
ambiguous lines are excluded and reported as unattributed. Pairwise
convergence flags are suggestion-severity findings — report-only, the
measured-profile law applies (voice/resources/character-dialogue-profiles.md).

`--morphology` (ADD-6) runs the rule-based Romanian verb-morphology pass:
per-chapter narrative-tense distribution (present / imperfect /
perfect-compus / mai-mult-ca-perfect confident markers) and narration-person
distribution (1st- vs 3rd-person markers outside dialogue), flagging
mid-chapter shifts and drift vs the declared `tense:` / `pov-person:`
(chapter frontmatter, inherited from kb/story.md). A Romanian-confidence
gate (distinctive function words + diacritic density over the narration)
skips the pass on non-Romanian text — English prose tripwires the
perfect-compus heuristic on "a rest" / "a moment", so below the confidence
threshold the scan reports low confidence instead of classifying (the
post-write hook stays silent on non-Romanian projects). Stdlib regex only, no
spaCy/stanza dependency (DESIGN section 1 binding); ambiguity-tolerant —
low-confidence text is excluded from the denominator rather than flagged.
Report-only, silent when clean, per-line `<!-- tense:skip -->` valve honored
(style-guardrails/resources/structural-caps.md)."""
import glob
import math
import os
import re
import sys

from collections import Counter

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


def run(root, pattern, baseline=False, dialogue=False, morphology=False):
    files = _resolve_files(pattern, root)
    if not files:
        util.die("no markdown files match %r" % pattern)
    if dialogue:
        _dialogue_report(root, files)
    if morphology:
        return _morphology_report(root, files)
    if dialogue:
        return EXIT_OK
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


# ---------------------------------------------------------------------------
# ADD-5: per-speaker dialogue stats (`style stats --dialogue`).
# Speaker attribution is nearest-narration ONLY: a speech-verb tag inside the
# dialogue paragraph, else the nearest narration paragraph naming exactly one
# cast member. Ambiguous lines are excluded from per-speaker stats and
# reported as unattributed. Both dialogue conventions are parsed: the
# dash-introduced line (— …) and quoted speech (straight + curly quotes).
# Report-only: convergence flags are suggestion-severity findings, never a
# gate; the measured-profile law applies. See
# voice/resources/character-dialogue-profiles.md for the LLM half of the test.
# ---------------------------------------------------------------------------

DIALOGUE_DASH_LINE_RE = re.compile(r"^\s*[—–]\s*(.*)$")
DIALOGUE_QUOTED_RE = re.compile(r'"([^"]+)"|“([^”]+)”')

# Speech-verb tag heuristic (the tag half of "speaker-nearest-narration").
# Bilingual: the Romanian narrative verbs + the common English tags.
SPEECH_VERB_RE = re.compile(
    r"\b(spuse|zise|răspunse|întrebă|șopti|rosti|murmura|murmură|adăugă|"
    r"continuă|exclamă|observă|said|asked|whispered|murmured|replied|"
    r"shouted|added|called)\b", re.IGNORECASE)

# A speaker's stats are shown from this many attributed lines (fewer fold
# into the per-file attributed totals only).
DIALOGUE_MIN_LINES_SHOWN = 3
# Pairwise convergence: two named characters are flagged when BOTH axes sit
# at/below the deltas below and each has >= DIALOGUE_CONV_MIN_LINES lines.
# Defaults, not laws — the measured profile outranks them.
DIALOGUE_CONV_MIN_LINES = 8
DIALOGUE_CONV_MSL_DELTA = 1.0
DIALOGUE_CONV_TTR_DELTA = 0.05

_STOPWORDS = frozenset((
    "the", "a", "an", "and", "or", "but", "of", "to", "in", "on", "at",
    "for", "with", "from", "by", "as", "is", "are", "was", "were", "be",
    "been", "being", "am", "i", "you", "he", "she", "it", "we", "they",
    "me", "him", "her", "them", "my", "his", "their", "our", "your",
    "this", "that", "these", "those", "not", "no", "nor", "so", "if",
    "then", "than", "too", "very", "just", "do", "does", "did", "done",
    "have", "has", "had", "will", "would", "can", "could", "should",
    "there", "here", "what", "who", "whom", "which", "when", "where",
    "how", "all", "any", "both", "each", "more", "most", "some", "such",
    "only", "own", "same", "out", "over", "into", "up", "down", "about",
    "after", "before", "again", "once", "don", "didn", "won",
    "de", "la", "un", "o", "în", "in", "pe", "cu", "prin", "că", "sa",
    "si", "sau", "dar", "ca", "ce", "cine", "care", "cum", "acum",
    "atunci", "apoi", "iar", "și", "să", "nu", "mai", "doar", "este",
    "e", "era", "erau", "sunt", "suntem", "sunteți", "ai", "ați", "au",
    "fi", "fost", "foarte", "tot", "toate", "toți", "te", "tu", "el",
    "ea", "ei", "ele", "lui", "le", "ne", "noi", "voi", "vouă", "mă",
    "ma", "mi", "îi", "îl", "îmi", "își", "își", "eu", "se", "îi",
))

_NAME_RE_CACHE = {}


def _name_re(lower_name):
    rex = _NAME_RE_CACHE.get(lower_name)
    if rex is None:
        rex = re.compile(
            r"(?<![\w’'\-])" + re.escape(lower_name) + r"(?![\w’'\-])",
            re.IGNORECASE | re.UNICODE)
        _NAME_RE_CACHE[lower_name] = rex
    return rex


def _load_characters(root):
    """lowercased name/alias -> (character id, display name) from
    kb/characters/ (tolerant parse). The first token of a multi-word name is
    registered too when distinctive (>= 4 letters): prose tags usually carry
    the short form ("Mira said", not "Mira Tarn said")."""
    out = {}
    d = util.project_file(root, "kb", "characters")
    if not os.path.isdir(d):
        return out
    for fname in sorted(os.listdir(d)):
        if not fname.endswith(".md") or fname == "_index.md":
            continue
        fm, _ = util.strip_frontmatter_text(
            util.read_file(os.path.join(d, fname)))
        cid = fm.get("id") if isinstance(fm.get("id"), str) else fname[:-3]
        display = (fm.get("name") if isinstance(fm.get("name"), str)
                   else cid)
        names = [display]
        aliases = fm.get("aliases")
        if isinstance(aliases, list):
            names.extend(a for a in aliases if isinstance(a, str))
        for n in names:
            nl = n.strip().lower()
            if nl and nl not in out:
                out[nl] = (cid, display)
        first = display.strip().lower().split()
        if len(first) > 1 and len(first[0]) >= 4 and first[0] not in out:
            out[first[0]] = (cid, display)
    return out


def _dialogue_spans(para):
    """Dialogue spans in one paragraph under either convention."""
    spans = []
    m = DIALOGUE_DASH_LINE_RE.match(para)
    if m and m.group(1).strip():
        spans.append(m.group(1))
    for q in DIALOGUE_QUOTED_RE.finditer(para):
        t = q.group(1) if q.group(1) is not None else q.group(2)
        if t and t.strip():
            spans.append(t)
    return spans


def _paragraph_narration_names(para, name_res):
    """Cast names mentioned in the paragraph's NARRATION. Dash paragraphs:
    only a name within the speech-verb tag window counts (a bare name inside
    speech is an addressee, not a tag). Quote paragraphs: text outside the
    quotes."""
    if DIALOGUE_DASH_LINE_RE.match(para):
        text = re.sub(r"^\s*[—–]\s*", "", para)
        names = set()
        for m in SPEECH_VERB_RE.finditer(text):
            window = text[max(0, m.start() - 48): m.end() + 48]
            names.update(lower for lower in name_res
                         if _name_re(lower).search(window))
        return names
    text = DIALOGUE_QUOTED_RE.sub(" ", para)
    return {lower for lower in name_res if _name_re(lower).search(text)}


def _attribute_speaker(idx, paragraphs, name_res):
    """Nearest-narration attribution for the dialogue paragraph at idx.
    Returns a lowercased name key, or None when ambiguous/unattributed."""
    names = _paragraph_narration_names(paragraphs[idx], name_res)
    if len(names) == 1:
        return next(iter(names))
    if len(names) > 1:
        return None  # ambiguous: excluded, not guessed
    for j in list(range(idx - 1, idx - 4, -1)) + list(range(idx + 1, idx + 3)):
        if j < 0 or j >= len(paragraphs):
            continue
        names = _paragraph_narration_names(paragraphs[j], name_res)
        if len(names) == 1:
            return next(iter(names))
        if len(names) > 1:
            return None  # ambiguous: excluded, not guessed
    return None


def _speaker_metrics(texts):
    joined = "\n".join(texts)
    sents = _sentences(joined)
    lens = [util.count_words(s) for s in sents] or [0]
    msl = sum(lens) / len(lens) if lens else 0.0
    tokens = re.findall(r"[^\W_]+", joined.lower(), re.UNICODE)
    ttr = (len(set(tokens)) / len(tokens)) if tokens else 0.0
    content = [t for t in tokens
               if t not in _STOPWORDS and len(t) >= 3]
    return {"msl": msl, "ttr": ttr, "words": util.count_words(joined),
            "top": Counter(content).most_common(5)}


def _speaker_slug(cid):
    return cid[len("character-"):] if cid.startswith("character-") else cid


def _dialogue_report(root, files):
    chars = _load_characters(root)
    per_file = []
    speaker_texts = {}
    speaker_lines = {}
    speaker_display = {}
    pair_first_file = {}
    for p in files:
        rel = os.path.relpath(p, root).replace("\\", "/")
        fm, body = util.strip_frontmatter_text(util.read_file(p))
        cast = set()
        for key in ("characters", "mentions"):
            v = fm.get(key)
            if isinstance(v, list):
                cast.update(x for x in v if isinstance(x, str))
        name_res = {lower: cid for lower, (cid, _d) in chars.items()
                    if not cast or cid in cast}
        paragraphs = [x for x in re.split(r"\n\s*\n", body) if x.strip()]
        attributed = unattributed = 0
        attributed_cids = set()
        for idx, para in enumerate(paragraphs):
            spans = _dialogue_spans(para)
            if not spans:
                continue
            lower = _attribute_speaker(idx, paragraphs, name_res)
            if lower is None:
                unattributed += len(spans)
                continue
            cid = name_res[lower]
            attributed += len(spans)
            attributed_cids.add(cid)
            speaker_texts.setdefault(cid, []).extend(spans)
            speaker_lines[cid] = speaker_lines.get(cid, 0) + len(spans)
            speaker_display[cid] = chars.get(lower, (cid, cid))[1]
        per_file.append((rel, attributed, unattributed))
        ordered = sorted(attributed_cids)
        for i in range(len(ordered)):
            for j in range(i + 1, len(ordered)):
                pair_first_file.setdefault((ordered[i], ordered[j]), rel)

    for rel, attributed, unattributed in per_file:
        if attributed or unattributed:
            sys.stdout.write(
                "dialogue %s: %d line(s) attributed, %d unattributed\n"
                % (rel, attributed, unattributed))

    metrics = {}
    for cid in sorted(speaker_lines):
        if speaker_lines[cid] >= DIALOGUE_MIN_LINES_SHOWN:
            metrics[cid] = _speaker_metrics(speaker_texts[cid])
            sys.stdout.write(
                "  speaker %s (%s): %d line(s), %d words, "
                "mean utterance %.1f, ttr %.2f\n"
                % (cid, speaker_display.get(cid, cid), speaker_lines[cid],
                   metrics[cid]["words"], metrics[cid]["msl"],
                   metrics[cid]["ttr"]))
            if metrics[cid]["top"]:
                sys.stdout.write("    top tokens: %s\n" % ", ".join(
                    "%s(%d)" % (t, c) for t, c in metrics[cid]["top"]))

    eligible = [c for c in sorted(metrics)
                if speaker_lines[c] >= DIALOGUE_CONV_MIN_LINES]
    findings = []
    for i in range(len(eligible)):
        for j in range(i + 1, len(eligible)):
            a, b = eligible[i], eligible[j]
            dmsl = abs(metrics[a]["msl"] - metrics[b]["msl"])
            dttr = abs(metrics[a]["ttr"] - metrics[b]["ttr"])
            if dmsl <= DIALOGUE_CONV_MSL_DELTA and dttr <= DIALOGUE_CONV_TTR_DELTA:
                rel0 = os.path.relpath(files[0], root).replace("\\", "/")
                findings.append(util.make_finding(
                    "dialogue-convergence", "suggestion",
                    pair_first_file.get((a, b), rel0),
                    0, "",
                    "characters %s and %s converge on the mechanical idiolect "
                    "axes (mean-utterance delta %.2f <= %.2f, ttr delta %.2f "
                    "<= %.2f; %d attributed lines each) - run the per-character "
                    "blind attribution test "
                    "(voice/resources/character-dialogue-profiles.md) before "
                    "judging; report-only, the measured-profile law applies."
                    % (a, b, dmsl, DIALOGUE_CONV_MSL_DELTA, dttr,
                       DIALOGUE_CONV_TTR_DELTA, speaker_lines[a]),
                    key="voice:dialogue-convergence-%s-%s"
                        % (_speaker_slug(a), _speaker_slug(b)),
                    audit="voice"))
    if findings:
        findings = util.filter_findings(findings,
                                        util.load_exemptions(root))
        util.emit_findings(findings)
    return EXIT_OK


# ---------------------------------------------------------------------------
# ADD-6: Romanian verb-morphology scan (`style stats --morphology`).
# Rule-based, stdlib regex only (DESIGN section 1 binding: no spaCy/stanza).
# Per chapter: narrative-tense distribution via confident verb-ending and
# auxiliary heuristics, and narration-person distribution (1st- vs 3rd-person
# markers outside dialogue). Flags: mid-chapter tense shift, narration-person
# shift, and drift vs the frontmatter `tense:` / `pov-person:` fields
# (chapter-level, inherited from kb/story.md). Ambiguity-tolerant: only
# confident classifications enter the denominator; low-confidence text is
# excluded rather than flagged. Report-only: suggestion-severity findings,
# silent when clean; the per-line `<!-- tense:skip -->` valve is honored and
# deliberate tense play is carved out per structural-caps.md.
# ---------------------------------------------------------------------------

TENSE_SKIP_MARK = "<!-- tense:skip -->"

# present: -ează/-ezi/-ești/-ește/-esc/-escă + gerunziu -ind/-ând
_PRESENT_RE = re.compile(
    r"\b\w+(ează|ezi|ești|ește|esc|escă|ind|ând)\b",
    re.IGNORECASE | re.UNICODE)
_PRESENT_EXCLUDE = frozenset(("când", "rând", "gând"))
# imperfect: high-frequency unambiguous forms + the -ea 3sg imperfect ending
_IMPERFECT_RE = re.compile(
    r"\b(era|eram|erai|erați|erau|aveam|aveai|aveați|aveau|făcea|spunea|"
    r"zicea|mergea|trecea|vedea|ținea|știa|putea|voia|dădea|stătea|părea|"
    r"credea|\w{4,}ea)\b", re.IGNORECASE | re.UNICODE)
_IMPERFECT_EXCLUDE = frozenset(("mea", "ta", "sa", "nea", "lea", "alea",
                                "chea", "asea"))
# perfect compus: auxiliary + participial ending (-t/-ut/-ât/-s); IGNORECASE
# because sentence-initial "A așteptat" is as much a pc auxiliary as "a"
_PC_RE = re.compile(r"\b(am|ai|ați|au|a)\s+\w{3,}(?:t|ut|ât|s)\b",
                    re.IGNORECASE | re.UNICODE)
# mai-mult-ca-perfect: -se pluperfect forms (+ perfect-simplu -se forms count
# with the past classes)
_MAIP_RE = re.compile(
    r"\b(fuse|fuseseră|foste|\w{2,}(?:ase|use|ise|âse|aseră|useră|iseră|"
    r"âseră))\b", re.IGNORECASE | re.UNICODE)
_MAIP_EXCLUDE = frozenset(("case", "vise", "ruse", "mise"))

_FIRST_PERSON_RE = re.compile(
    r"\b(eu|mi|mă|ma|mine|mie|nouă|nostru|noastră|noștri|noastre|ne|am)\b",
    re.IGNORECASE | re.UNICODE)
_THIRD_PERSON_RE = re.compile(
    r"\b(el|ea|ei|ele|lui|lor|îi|ii)\b", re.IGNORECASE | re.UNICODE)

_MORPH_SHIFT_MIN_MARKERS = 8    # per half, for the mid-chapter shift flags
_MORPH_DRIFT_MIN_MARKERS = 10   # chapter total, for the frontmatter drift flag
_MORPH_PERSON_SHIFT_MIN_WORDS = 150  # narration words per half
_MORPH_PERSON_SHIFT_RATE = 2.0  # per 1k; the louder half must reach this

# Romanian-confidence gate: the pass classifies Romanian verb morphology, so
# it must not fire on non-Romanian prose (an English chapter tripwires the
# perfect-compus heuristic on "a rest" / "a moment" and turns the declared
# tense into spurious drift findings). A Romanian-signal density under
# _MORPH_MIN_RO_DENSITY (or no narration at all) is reported as
# low-confidence instead of classified. Romanian narration measures far
# above the threshold (diacritized ~0.4-0.7, diacritic-free ~0.17); English
# measures near 0, so the gate restores "silent when clean" for
# non-Romanian projects without a language setting.
_MORPH_MIN_RO_DENSITY = 0.12
_RO_DIACRITIC_RE = re.compile(r"[ăâîșțĂÂÎȘȚ]")
# Distinctive Romanian function words/auxiliaries — chosen so common English
# words ("care", "a", "in", "so") are excluded; occasional loanword collisions
# ("de", "la", "un") stay far under the threshold.
_RO_SIGNAL_WORDS = frozenset((
    "de", "la", "în", "pe", "cu", "că", "sa", "să", "și", "si", "nu",
    "mai", "este", "sunt", "era", "eram", "erai", "erați", "erau", "fost",
    "pentru", "prin", "cum", "dar", "sau", "iar", "acum", "atunci",
    "foarte", "trebuie", "poate", "acest", "această", "aceste", "acești",
    "un", "o", "îi", "îl", "îmi", "își", "imi", "isi", "mi", "mă", "ma",
    "te", "ne", "noi", "voi", "se", "el", "ea", "ele", "ei", "lui", "lor",
    "din", "ca", "eu", "tu", "însă", "îi", "totuși", "decât", "cât",
    "unde", "când", "ii", "il", "erati",
))


def _romanian_density(text):
    """(signal-token density, total tokens) for the Romanian-confidence
    gate: tokens carrying a Romanian diacritic plus tokens in the
    distinctive function-word set, over all word tokens."""
    tokens = re.findall(r"[^\W_]+", text, re.UNICODE)
    if not tokens:
        return 0.0, 0
    signal = sum(1 for t in tokens
                 if _RO_DIACRITIC_RE.search(t) or t.lower() in _RO_SIGNAL_WORDS)
    return signal / len(tokens), len(tokens)


def _strip_tense_skip(text):
    return "\n".join(line for line in text.split("\n")
                     if TENSE_SKIP_MARK not in line)


def _narration_text(paragraphs):
    """Body minus dialogue: dash paragraphs dropped entirely (spoken text +
    tag), quoted spans removed from mixed paragraphs."""
    out = []
    for para in paragraphs:
        if DIALOGUE_DASH_LINE_RE.match(para):
            continue
        out.append(DIALOGUE_QUOTED_RE.sub(" ", para))
    return "\n\n".join(out)


def _tense_counts(text):
    present = sum(1 for m in _PRESENT_RE.finditer(text)
                  if m.group(0).lower() not in _PRESENT_EXCLUDE)
    imperfect = sum(1 for m in _IMPERFECT_RE.finditer(text)
                    if m.group(0).lower() not in _IMPERFECT_EXCLUDE)
    pc = len(_PC_RE.findall(text))
    maip = sum(1 for m in _MAIP_RE.finditer(text)
               if m.group(0).lower() not in _MAIP_EXCLUDE)
    return {"present": present, "imperfect": imperfect,
            "perfect-compus": pc, "mai-mult-ca-perfect": maip}


def _halves(text):
    """Split into two chunks at the paragraph boundary nearest the midpoint
    (by word count)."""
    paras = [p for p in re.split(r"\n\s*\n", text) if p.strip()]
    total = util.count_words(text)
    half = total / 2.0
    acc = 0
    first, second = [], []
    for p in paras:
        (first if acc < half else second).append(p)
        acc += util.count_words(p)
    return "\n\n".join(first), "\n\n".join(second)


def _dominant_class(counts):
    best = max(counts, key=lambda k: (counts[k], k))
    return best if counts[best] > 0 else None


def _tense_expectation(declared):
    if not isinstance(declared, str):
        return None
    d = declared.strip().lower()
    if "pres" in d or "prezent" in d:
        return "present"
    if "trecut" in d or "past" in d or "imperfect" in d or "perfect" in d:
        return "past"
    return None


def _person_expectation(declared):
    if not isinstance(declared, str):
        return None
    d = declared.strip().lower()
    if d.startswith("3") or "third" in d or "a treia" in d:
        return "third"
    if d.startswith("1") or "first" in d or "întâi" in d or "intai" in d \
            or "prima" in d:
        return "first"
    return None


def _morphology_report(root, files):
    story = util.load_story(root)
    findings = []
    for p in files:
        rel = os.path.relpath(p, root).replace("\\", "/")
        is_chapter = rel.startswith("manuscript/chapters/")
        fm, body = util.strip_frontmatter_text(util.read_file(p))
        narration = _narration_text(
            [x for x in re.split(r"\n\s*\n", _strip_tense_skip(body))
             if x.strip()])
        tense = _tense_counts(narration)
        words = util.count_words(narration)
        first_n = len(_FIRST_PERSON_RE.findall(narration))
        third_n = len(_THIRD_PERSON_RE.findall(narration))
        r_first = (first_n / words * 1000.0) if words else 0.0
        r_third = (third_n / words * 1000.0) if words else 0.0
        markers = sum(tense.values())
        past = tense["imperfect"] + tense["perfect-compus"] \
            + tense["mai-mult-ca-perfect"]
        ro_density, _ = _romanian_density(narration)
        if (ro_density < _MORPH_MIN_RO_DENSITY
                or (markers == 0 and first_n == 0 and third_n == 0)):
            sys.stdout.write(
                "morphology %s: no confident Romanian verb markers found "
                "(non-Romanian text or all dialogue)\n" % rel)
            continue
        sys.stdout.write(
            "morphology %s: present=%d imperfect=%d perfect-compus=%d "
            "mai-mult-ca-perfect=%d | narration person 1st=%.1f/1k "
            "3rd=%.1f/1k\n"
            % (rel, tense["present"], tense["imperfect"],
               tense["perfect-compus"], tense["mai-mult-ca-perfect"],
               r_first, r_third))
        if not is_chapter:
            continue  # drift/shift flags apply to manuscript chapters only

        h1, h2 = _halves(narration)
        t1, t2 = _tense_counts(h1), _tense_counts(h2)
        dom1, dom2 = _dominant_class(t1), _dominant_class(t2)
        if (dom1 and dom2 and dom1 != dom2
                and sum(t1.values()) >= _MORPH_SHIFT_MIN_MARKERS
                and sum(t2.values()) >= _MORPH_SHIFT_MIN_MARKERS):
            findings.append(util.make_finding(
                "tense-shift", "suggestion", rel, 0, "",
                "mid-chapter narrative-tense shift: dominant class is %s in "
                "the first half and %s in the second (mechanical heuristic; "
                "deliberate moves use the tense:skip valve or voice:skip - "
                "see style-guardrails/resources/structural-caps.md)."
                % (dom1, dom2),
                key="voice:tense-shift", audit="voice"))
        f1 = len(_FIRST_PERSON_RE.findall(h1))
        f2 = len(_FIRST_PERSON_RE.findall(h2))
        w1, w2 = util.count_words(h1), util.count_words(h2)
        if (w1 >= _MORPH_PERSON_SHIFT_MIN_WORDS
                and w2 >= _MORPH_PERSON_SHIFT_MIN_WORDS):
            ra = f1 / w1 * 1000.0
            rb = f2 / w2 * 1000.0
            hi, lo = max(ra, rb), min(ra, rb)
            if (hi >= _MORPH_PERSON_SHIFT_RATE and lo <= 0.25 * hi):
                findings.append(util.make_finding(
                    "person-shift", "suggestion", rel, 0, "",
                    "mid-chapter narration-person shift: 1st-person marker "
                    "rate moves %.1f/1k -> %.1f/1k between halves (mechanical "
                    "heuristic; verify by reading before judging)."
                    % (min(ra, rb), hi),
                    key="voice:person-shift", audit="voice"))

        # `or`, not .get(default): the template ships `tense: null` / the
        # parser stores present-but-null keys as None, and a .get() default
        # never fires for an existing key — omission AND explicit null must
        # both inherit the kb/story.md value (ledger-files.md inheritance
        # contract).
        declared_tense = fm.get("tense") or story.get("tense")
        exp = _tense_expectation(declared_tense)
        if exp and markers >= _MORPH_DRIFT_MIN_MARKERS:
            dom = "present" if tense["present"] > past else \
                ("past" if past > tense["present"] else None)
            if dom and dom != exp:
                findings.append(util.make_finding(
                    "tense-drift", "suggestion", rel, 0, "",
                    "chapter narration is dominantly %s against declared "
                    "tense: %s (present markers %d vs past markers %d; "
                    "mechanical heuristic - deliberate tense play uses the "
                    "tense:skip valve, see "
                    "style-guardrails/resources/structural-caps.md)."
                    % (dom, declared_tense, tense["present"], past),
                    key="voice:tense-drift", audit="voice"))
        declared_person = fm.get("pov-person") or story.get("pov-person")
        pexp = _person_expectation(declared_person)
        if pexp and (first_n + third_n) >= _MORPH_SHIFT_MIN_MARKERS:
            dom = "first" if first_n > third_n else \
                ("third" if third_n > first_n else None)
            if dom and dom != pexp:
                findings.append(util.make_finding(
                    "person-drift", "suggestion", rel, 0, "",
                    "chapter narration is dominantly %s-person against "
                    "declared pov-person: %s (1st-person markers %d vs "
                    "3rd-person markers %d; mechanical heuristic - verify by "
                    "reading; POV lurch is also a critic lens, "
                    "prose-critique/voice.md)." % (dom, declared_person,
                                                   first_n, third_n),
                    key="voice:person-drift", audit="voice"))
    if findings:
        findings = util.filter_findings(findings,
                                        util.load_exemptions(root))
        util.emit_findings(findings)
    return EXIT_OK
