#!/usr/bin/env python3
# Vellum post-write prose net: deterministic AI-tell scanner (stdlib only, Python >= 3.8).
# Adapted from avoid-ai-writing (MIT) - detector/patterns.js category structure and the
# references/patterns.md tier tables (fiction-relevant subset re-derived for prose).
# Adapted from oh-story-claudecode/skills/story-setup/references/templates/hooks (MIT) -
# prose-net concept (adjacent duplicate-line check, truncation net) reimplemented in Python.
# Mechanism credited to NousResearch/autonovel (tier taxonomy); no source text or code copied.
# Changes: English fiction-tuned word lists; JSON-lines scan interface; voice-debt writer;
# emit-grep table export for the pure-bash fallback path.
import os
import re
import sys
import json
import hashlib
import argparse
from datetime import datetime, timezone

# ---------------------------------------------------------------------------
# Tier tables (re-derived for fiction prose). These are NOT verbatim copies of
# any upstream list; they are fiction-tuned selections from the avoid-ai-writing
# tier tables (MIT) plus a few fiction-specific tells, with the autonovel tier
# taxonomy credited ideas-only. Each entry is a (regex, label, fix) triple.
# Regexes use \b word boundaries and match inflected forms via \w*.
# ---------------------------------------------------------------------------

TIER1 = [
    (r"\bdelv\w*\b", "delve", "replace with explore / dig into / look at"),
    (r"\btapestr\w*\b", "tapestry", "describe the actual complexity, not the metaphor"),
    (r"\brealm\b", "realm", "use area / field / domain"),
    (r"\bembark\w*\b", "embark", "use start / begin"),
    (r"\btestament to\b", "testament", "use shows / proves / demonstrates"),
    (r"\bbeacon\b", "beacon", "name the example or guidance directly"),
    (r"\bmeticul\w*\b", "meticulous", "use careful / detailed / precise"),
    (r"\bseamless\w*\b", "seamless", "use smooth / easy / without friction"),
    (r"\bgame.chang\w*\b", "game-changer", "describe what specifically changed and why"),
    (r"\bhit different\w*\b", "hit-different", "say what specifically changed, or cut"),
    (r"\bnestl\w*\b", "nestled", "use is located / sits / is in"),
    (r"\bvibrant\b", "vibrant", "describe what makes it active, or cut"),
    (r"\bthriv\w*\b", "thriving", "use growing / active, or cite a number"),
    (r"\bbustl\w*\b", "bustling", "use busy / active, or cite what makes it busy"),
    (r"\bintricat\w*\b", "intricate", "use complex / detailed, or name the complexity"),
    (r"\bever.evolv\w*\b", "ever-evolving", "use changing / growing, or describe how"),
    (r"\bdaunting\b", "daunting", "use hard / difficult / challenging"),
    (r"\bholistic\w*\b", "holistic", "use complete / full / whole, or describe what is included"),
    (r"\bactionable\b", "actionable", "use practical / useful / concrete"),
    (r"\bimpactful\b", "impactful", "use effective / significant, or describe the impact"),
    (r"\bsymphon\w*\b", "symphony", "describe the actual coordination or combination"),
    (r"\bpalpable\b", "palpable", "name the concrete detail the reader can sense"),
    (r"\bunwaver\w*\b", "unwavering", "state the commitment or action directly"),
    (r"\bethereal\b", "ethereal", "describe the specific quality, not the mood word"),
    (r"\bgossamer\b", "gossamer", "name the material or quality directly"),
    (r"\bshiver\w* down\b", "shivers-down", "show the physical reaction, not the cliche"),
    (r"\bcouldn.?t help but\b", "couldnt-help-but", "state the reaction or action directly"),
    (r"\bthe air was thick\b", "air-thick", "show the sensory detail that fills the air"),
    (r"\ba chorus of\b", "chorus-of", "name the actual sounds or voices"),
    (r"\bpainted (across|over|onto)\b", "painted-across", "use a concrete verb for the expression"),
    (r"\bunprecedented\b", "unprecedented", "name the precedent it breaks, or cut"),
    (r"\bunparalleled\b", "unparalleled", "cite the comparison, or cut"),
]

TIER2 = [
    (r"\bharness\w*\b", "harness"),
    (r"\bnavigat\w*\b", "navigate"),
    (r"\bfoster\w*\b", "foster"),
    (r"\belevat\w*\b", "elevate"),
    (r"\bunleash\w*\b", "unleash"),
    (r"\bstreamlin\w*\b", "streamline"),
    (r"\bempower\w*\b", "empower"),
    (r"\bbolster\w*\b", "bolster"),
    (r"\bspearhead\w*\b", "spearhead"),
    (r"\bresonat\w*\b", "resonate"),
    (r"\brevolutioniz\w*\b", "revolutionize"),
    (r"\bfacilitat\w*\b", "facilitate"),
    (r"\bunderpin\w*\b", "underpin"),
    (r"\bnuanc\w*\b", "nuanced"),
    (r"\bcrucial\b", "crucial"),
    (r"\bmultifacet\w*\b", "multifaceted"),
    (r"\bmyriad\b", "myriad"),
    (r"\bplethora\b", "plethora"),
    (r"\bencompass\w*\b", "encompass"),
    (r"\bcatalyz\w*\b", "catalyze"),
    (r"\breimagin\w*\b", "reimagine"),
    (r"\bgalvaniz\w*\b", "galvanize"),
    (r"\baugment\w*\b", "augment"),
    (r"\bcultivat\w*\b", "cultivate"),
    (r"\billuminat\w*\b", "illuminate"),
    (r"\belucidat\w*\b", "elucidate"),
    (r"\bjuxtapos\w*\b", "juxtapose"),
    (r"\btransform\w*\b", "transformative"),
    (r"\bcornerstone\b", "cornerstone"),
    (r"\bparamount\b", "paramount"),
    (r"\bburgeon\w*\b", "burgeoning"),
    (r"\bnascent\b", "nascent"),
    (r"\bquintessen\w*\b", "quintessential"),
    (r"\boverarch\w*\b", "overarching"),
    (r"\blandscap\w*\b", "landscape"),
    (r"\bpivotal\b", "pivotal"),
    (r"\bunderscore\w*\b", "underscore"),
    (r"\bshowcas\w*\b", "showcase"),
]

FILLERS = [
    (r"\bit is important to note that\b", "important-to-note", "cut or state the point directly"),
    (r"\bit'?s worth noting that\b", "worth-noting", "cut or state the point directly"),
    (r"\bin terms of\b", "in-terms-of", "name the specific relationship"),
    (r"\bthe reality is that\b", "reality-is", "state the fact directly"),
    (r"\bat the end of the day\b", "end-of-day", "cut or make the concrete point"),
    (r"\bwhen it comes to\b", "when-it-comes-to", "name the specific subject"),
    (r"\bthat being said\b", "that-being-said", "connect the ideas or cut"),
    (r"\bneedless to say\b", "needless-to-say", "cut or state the fact"),
]

# Em-dash density default threshold (per 1k words). avoid-ai-writing sets a
# hard max of ~1/1k for nonfiction; fiction is more permissive, so the default
# net flags above 2.0/1k as advisory. The measured-profile law (spec 8.1) is
# enforced, not just promised: when kb/styles/baseline.md carries an em-dash
# rate, the cap adapts to it (baseline + 25% band, floored at this default),
# and tier-1 debt accrual is skipped while the chapter's hit rate stays within
# the author's own measured tier-1 rate.
EM_DASH_PER_1K_THRESHOLD = 2.0
EM_DASH_BASELINE_BAND = 1.25  # cap = baseline rate * band
# Tier-2 cluster rule: three or more distinct tier-2 words in one paragraph is
# the mechanical rewrite signal ("suspicious-in-clusters-of-three",
# style-guardrails/resources/tiers.md — two or more is a judgment-level strong
# signal the critic layer applies; the net flags at three).
TIER2_CLUSTER_MIN = 3
# Near-verbatim duplicate line: normalized lines equal and >= 8 chars.
DUP_MIN_LEN = 8
# voice-debt.json bound (spec 6.2): cleared items older than this many days
# are pruned on write, so the file does not grow monotonically over the life
# of the project. Open items are never pruned (they are actionable).
VOICE_DEBT_PRUNE_DAYS = 30

# Baseline metrics table (kb/styles/baseline.md, spec 8.3): rows
# `| metric | author rate (per 1k words) |`.
BASELINE_ROW_RE = re.compile(
    r"^\|\s*([a-z0-9 -]+?)\s*\|\s*([0-9.]+)\s*\|\s*$", re.MULTILINE)


def load_baseline(project_root):
    """Return {metric: rate} from kb/styles/baseline.md, or {} when absent
    or still an unfilled template (frontmatter `measured: false` — the
    shipped template carries example-shaped structure; treating template
    rates as the author's measured profile would adapt the caps to a
    measurement that never happened).

    Accepted metric keys (spec 8.3): em-dash, hedge, tier1-hit,
    dialogue-ratio, ttr, burstiness (prefix match tolerates the unit suffix).
    """
    if not project_root:
        return {}
    path = os.path.join(project_root, "kb", "styles", "baseline.md")
    if not os.path.exists(path):
        return {}
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            text = f.read()
    except OSError:
        return {}
    if re.search(r"^measured:\s*false\s*$", text, re.MULTILINE):
        return {}
    rates = {}
    for m in BASELINE_ROW_RE.finditer(text):
        key = m.group(1).strip().lower()
        try:
            rates[key] = float(m.group(2))
        except ValueError:
            continue
    return rates


def _baseline_rate(rates, key):
    """Prefix-tolerant lookup: 'em-dash' matches 'em-dash (per 1k words)'."""
    if key in rates:
        return rates[key]
    for k, v in rates.items():
        if k.startswith(key):
            return v
    return None


def _compile(tuples):
    return [(re.compile(p, re.IGNORECASE), label, *rest) for (p, label, *rest) in tuples]


TIER1_RE = _compile(TIER1)
TIER2_RE = _compile(TIER2)
FILLER_RE = _compile(FILLERS)


def _word_count(text):
    # Word rule (spec 5.1, from story-skills schema-v2): a run of letters/digits
    # in any script; apostrophes and hyphens join. \w with the UNICODE flag
    # covers letters/digits across scripts; we additionally keep internal ' and -.
    return len(re.findall(r"[^\W_]+(?:['’-][^\W_]+)*", text, re.UNICODE))


def _strip_frontmatter(text):
    lines = text.split("\n")
    if not lines or not re.match(r"^---\s*\r?$", lines[0]):
        return text, 1
    for i in range(1, len(lines)):
        if re.match(r"^---\s*\r?$", lines[i]):
            return "\n".join(lines[i + 1:]), i + 2  # body start line number
    return text, 1


def _norm_line(line):
    s = line.strip().lower()
    s = re.sub(r"\s+", " ", s)
    s = re.sub(r"[^\w ]", "", s)
    return s


def _has_voice_skip(text):
    # Spec 6.2 / hooks README: `<!-- voice:skip -->` anywhere in the chapter
    # suppresses tier-1 debt accrual — not just the head of the file.
    return "<!-- voice:skip -->" in text


# List-item em-dash typography carve-out (structural-caps.md): an em-dash
# acting as the separator in a list item that opens with a bolded lead term or
# a markdown link is typography, not a prose splice — it does not count toward
# the density rate.
_LIST_ITEM_DASH_RE = re.compile(
    r"^[ \t]*(?:[-*+]|\d+\.)[ \t]+(?:\*\*[^*]+\*\*|\[[^\]]+\]\([^)]+\)|`[^`]+`)[ \t]*[—-]",
    re.MULTILINE)


def scan_file(path, baseline=None):
    """Return a list of finding dicts for one chapter file."""
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        raw = f.read()
    body, body_start_line = _strip_frontmatter(raw)
    findings = []
    if baseline is None:
        baseline = {}

    # --- Tier 1 (kill on sight) and fillers, line by line ---
    body_lines = body.split("\n")
    for i, line in enumerate(body_lines):
        lno = body_start_line + i
        for regex, label, fix in TIER1_RE:
            m = regex.search(line)
            if m:
                findings.append({
                    "line": lno, "type": "tier1", "label": label,
                    "match": m.group(0), "fix": fix,
                })
                break  # one tier-1 per line keeps the net legible
        for regex, label, _fix in FILLER_RE:
            m = regex.search(line)
            if m:
                findings.append({
                    "line": lno, "type": "filler", "label": label,
                    "match": m.group(0),
                    "fix": "cut or replace with the specific point",
                })

    # --- Tier 2 cluster heuristic (TIER2_CLUSTER_MIN+ distinct in one paragraph) ---
    # Track each paragraph's true start line by scanning raw paragraph spans;
    # accumulating +2 per paragraph drifts when paragraphs are separated by
    # more than one blank line.
    paras = []
    for m in re.finditer(r"[^\n](?:.|\n(?!\n))*?(?=\n\s*\n|$)", body):
        span = m.group(0)
        if span.strip():
            line_no = body_start_line + body.count("\n", 0, m.start())
            paras.append((line_no, span))
    for line_no, para in paras:
        distinct = set()
        first_match = {}
        for regex, label, *_ in TIER2_RE:
            m = regex.search(para)
            if m and label not in distinct:
                distinct.add(label)
                first_match[label] = m.group(0)
        if len(distinct) >= TIER2_CLUSTER_MIN:
            findings.append({
                "line": line_no, "type": "tier2-cluster",
                "label": "tier2-cluster",
                "match": ", ".join(sorted(distinct)),
                "fix": "rewrite the paragraph with fewer stock abstractions",
            })

    # --- Em-dash density (with the list-item typography carve-out and the
    #     measured-profile baseline override) ---
    words = _word_count(body)
    if words >= 200:
        dashes = len(re.findall(r"—|--", body))
        dashes -= len(_LIST_ITEM_DASH_RE.findall(body))
        dashes = max(dashes, 0)
        per_1k = dashes / words * 1000
        threshold = EM_DASH_PER_1K_THRESHOLD
        base_rate = _baseline_rate(baseline, "em-dash")
        if base_rate is not None and base_rate > 0:
            threshold = max(threshold, base_rate * EM_DASH_BASELINE_BAND)
        if per_1k > threshold:
            findings.append({
                "line": 0, "type": "em-dash-density", "label": "em-dash-density",
                "match": f"{per_1k:.1f}/1k",
                "fix": "em-dash density above the structural cap (advisory; caps adapt to kb/styles/baseline.md)",
            })

    # --- Near-verbatim duplicated line ---
    prev_norm = None
    prev_lno = None
    for i, line in enumerate(body_lines):
        lno = body_start_line + i
        norm = _norm_line(line)
        if len(norm) >= DUP_MIN_LEN and prev_norm is not None and norm == prev_norm:
            findings.append({
                "line": lno, "type": "duplicate-line", "label": "duplicate-line",
                "match": line.strip()[:40],
                "fix": "remove or vary the repeated line",
            })
        prev_norm = norm
        prev_lno = lno

    return findings


def _parse_debt_ts(s):
    """Parse a voice-debt timestamp (ISO 8601 Z) to a unix timestamp, or None."""
    if not isinstance(s, str) or not s:
        return None
    try:
        return datetime.strptime(s, "%Y-%m-%dT%H:%M:%SZ") \
            .replace(tzinfo=timezone.utc).timestamp()
    except ValueError:
        return None


def _chapter_id(path):
    m = re.match(r"chapter-(\d+)\.md$", os.path.basename(path), re.IGNORECASE)
    return m.group(1) if m else os.path.basename(path)


def write_voice_debt(path, findings, project_root, baseline=None):
    """Append open tier-1 hits to work/voice-debt.json (spec 6.2).

    Honors voice:skip (anywhere in the chapter) and the measured-profile law:
    when kb/styles/baseline.md carries a tier1-hit rate above zero, tier-1
    hits within the author's measured rate do not accrue debt (only the
    over-shoot does)."""
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        raw = f.read()
    if _has_voice_skip(raw):
        return  # author escape hatch: suppress tier-1 debt accrual for this chapter

    if baseline is None:
        baseline = {}

    debt_path = os.path.join(project_root, "work", "voice-debt.json")
    if os.path.exists(debt_path):
        with open(debt_path, "r", encoding="utf-8") as f:
            try:
                doc = json.load(f)
            except Exception:
                doc = {"schema_version": 1, "items": []}
    else:
        doc = {"schema_version": 1, "items": []}
    items = doc.get("items", [])
    cid = _chapter_id(path)
    # Drop this chapter's existing tier-1 entries (re-scan supersedes them).
    items = [it for it in items if it.get("chapter") != cid or it.get("type") != "tier1"]
    now = datetime.now(timezone.utc)
    # Prune cleared items older than the retention window so the debt file
    # stays bounded; open items are never pruned (still actionable).
    cutoff = now.timestamp() - VOICE_DEBT_PRUNE_DAYS * 86400
    kept = []
    for it in items:
        if it.get("status") != "open":
            cleared = _parse_debt_ts(it.get("cleared_at"))
            if cleared is not None and cleared < cutoff:
                continue
        kept.append(it)
    items = kept
    now_s = now.strftime("%Y-%m-%dT%H:%M:%SZ")

    tier1_findings = [f for f in findings if f.get("type") == "tier1"]
    # Measured-profile override: skip debt accrual while the chapter's tier-1
    # rate stays within the author's own measured rate (baseline tier1-hit).
    allowed = None
    base_rate = _baseline_rate(baseline, "tier1-hit")
    if base_rate is not None and base_rate > 0:
        fm, body = _strip_frontmatter(raw)
        words = _word_count(body)
        if words >= 200:
            allowed = base_rate / 1000.0 * words
            allowed = int(allowed + 0.5)  # measured allowance in whole hits
            if len(tier1_findings) <= allowed:
                tier1_findings = []

    n = 0
    for f in tier1_findings:
        n += 1
        items.append({
            "id": f"debt-{cid}-{n:03d}",
            "chapter": f"chapter-{cid}",
            "line": f.get("line", 0),
            "match": f.get("match", ""),
            "type": "tier1",
            "status": "open",
            "found_at": now_s,
        })
    doc["items"] = items
    os.makedirs(os.path.dirname(debt_path), exist_ok=True)
    tmp = debt_path + f".tmp-{os.getpid()}"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(doc, f, indent=2, ensure_ascii=False)
        f.write("\n")
    os.replace(tmp, debt_path)


def cmd_extract_target():
    """Read hook JSON from stdin, print tool_input.file_path (or path/filePath)."""
    try:
        data = json.load(sys.stdin)
    except Exception:
        return 1
    ti = data.get("tool_input") or {}
    for key in ("file_path", "path", "filePath"):
        val = ti.get(key)
        if isinstance(val, str) and val.strip():
            sys.stdout.write(val.strip())
            return 0
    return 1


def cmd_scan(args):
    baseline = load_baseline(args.project_root) if args.project_root else {}
    findings = scan_file(args.file, baseline=baseline)
    if args.format == "text":
        for f in findings:
            where = f"line {f['line']}" if f.get("line") else "file"
            sys.stdout.write(f"[{f['type']}] {where}: {f.get('match','')} - {f.get('fix','')}\n")
    else:
        for f in findings:
            sys.stdout.write(json.dumps(f, ensure_ascii=False) + "\n")
    if args.debt:
        write_voice_debt(args.file, findings, args.project_root,
                         baseline=baseline)
    return 0


def cmd_emit_grep():
    """Print a single egrep -E pattern matching the tier-1 table (bash fallback)."""
    parts = []
    for regex, label, *_ in TIER1_RE:
        # Convert the \b...\b inflection pattern to a grep -E friendly form.
        src = regex.pattern
        src = src.replace(r"\b", "")
        parts.append(src)
    sys.stdout.write("(" + "|".join(parts) + ")\n")
    return 0


def main():
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="cmd")

    sub.add_parser("extract-target")

    sc = sub.add_parser("scan")
    sc.add_argument("file")
    sc.add_argument("--format", choices=["json", "text"], default="json")
    sc.add_argument("--debt", help="path to project root for voice-debt.json updates")
    sc.add_argument("--project_root", dest="project_root", default="")

    sub.add_parser("emit-grep")

    args = p.parse_args()
    if args.cmd == "extract-target":
        return cmd_extract_target()
    if args.cmd == "scan":
        return cmd_scan(args)
    if args.cmd == "emit-grep":
        return cmd_emit_grep()
    p.print_help()
    return 2


if __name__ == "__main__":
    sys.exit(main())
