#!/usr/bin/env python3
# Vellum CI lint (design-spec.md sections 4.7 / 14, workstream H; referenced by A's ci.yml).
# Original code (base design credited in ATTRIBUTION.md).
"""lint_vellum.py — the CI drift/leak gate. Checks, from the plugin root:

1. No Meridian vocabulary anywhere under plugin/ (word-bounded, case-insensitive
   for names; `hook.toml` matched literally). Fablecraft/Scriptorium citations
   are attribution, not leaks — the word-boundary pattern cannot match them.
2. Attribution headers: every file that appears in the REQUIRED_HEADERS map
   (derived from ATTRIBUTION.md's table, spec 3.5) carries its header; every
   "Adapted from"/"Mechanism credited" header cites an owner/repo that exists
   in ATTRIBUTION.md.
3. hooks/hooks.json parses as JSON.
4. No file under plugin/ exceeds 100 KB.
5. Frontmatter globs: agents/*.md, skills/*/SKILL.md, commands/*.md start with
   `---`.

Exit 0 clean; exit 1 with `::error` annotations otherwise.
"""
import json
import os
import re
import sys
from pathlib import Path

PLUGIN = Path(__file__).resolve().parent.parent.parent
if (PLUGIN / "hooks").is_dir():
    ROOT = PLUGIN          # running from plugin/scripts/ci/
else:
    ROOT = PLUGIN / "plugin"

KB = 1024
MAX_FILE_BYTES = 100 * KB

MERIDIAN_VOCAB = re.compile(
    r"\b(meridian|opus46|sol)\b|\bfable\b|hook\.toml", re.IGNORECASE)

ATTRIBUTION_OWNERS = [
    "haowjy/creative-writing-skills", "story-skills", "oh-story-claudecode",
    "avoid-ai-writing", "stop-slop", "autonovel", "claude-ghost-writer",
    "Velith", "fiction-forge", "fiction", "author-toolkit", "Novel-OS",
    "book-genesis-v4", "Claude-Book", "Claude-Code-Novel-Writer", "GOAT",
    "Re3", "LongWriter", "Fablecraft", "Scriptorium", "geobond13",
    "calliope-editor/writing-skills",
]

# Files that MUST carry an attribution header (spec 3.5): every file whose
# content derives from another repo. Keep in sync with ATTRIBUTION.md.
REQUIRED_HEADERS = {
    # hooks: ported from oh-story-claudecode (MIT) + avoid-ai-writing (MIT)
    "hooks/scripts/lib/common.sh",
    "hooks/scripts/guard-outline-before-prose.sh",
    "hooks/scripts/guard-bash-prose-writes.sh",
    "hooks/scripts/check-prose-after-write.sh",
    "hooks/scripts/session-start.sh",
    "hooks/scripts/pre-compact.sh",
    "hooks/scripts/session-stop.sh",
    "hooks/scripts/chapter-maintenance.sh",
    "hooks/scripts/prose_core.py",
    # story-ledgers: story-skills / oh-story / fiction-forge / Novel-OS (MIT)
    "skills/story-ledgers/resources/ledger-files.md",
    "skills/story-ledgers/resources/state-card.md",
    "skills/story-ledgers/resources/write-time-capture.md",
    # story-planning: author-toolkit (MIT) + GOAT ideas
    "skills/story-planning/resources/structure-beats.md",
    "skills/story-planning/resources/scene-cards.md",
    # style/voice: autonovel ideas-only + avoid-ai-writing/stop-slop (MIT)
    "skills/style-guardrails/resources/tiers.md",
    "skills/style-guardrails/resources/structural-caps.md",
    "skills/style-guardrails/resources/smell-tests.md",
    "skills/voice/resources/voice-profile.md",
    "skills/voice/resources/blind-tag-test.md",
    "skills/voice/resources/retune.md",
    # gates: Velith (Apache) + Fablecraft ideas
    "skills/gates/resources/quality-bar.md",
    "skills/gates/resources/genre-profiles.md",
    # cold-read: fiction-forge (MIT)
    "skills/cold-read/resources/charter.md",
    "skills/cold-read/resources/reader-ledger.md",
    "skills/cold-read/resources/issue-format.md",
    "skills/cold-read/resources/batching.md",
    # story-review personas: fiction (MIT, per source README)
    "skills/story-review/resources/prose-critique/personas/wood.md",
    "skills/story-review/resources/prose-critique/personas/king.md",
    "skills/story-review/resources/prose-critique/personas/leguin.md",
    "skills/story-review/resources/prose-critique/personas/gay.md",
    # templates derived from ported schemas
    "templates/state-card.md",
    "templates/cold-read/charter.md",
    "templates/cold-read/reader_ledger.md",
    "templates/cold-read/issues.md",
    "templates/cold-read/batch-report.md",
}

HEADER_RE = re.compile(
    r"([Aa]dapted from [^\n]*|[Mm]echanism (?:credited to|from) [^\n]*)")
errors = []


def err(path, msg):
    errors.append("%s: %s" % (path, msg))


def check_meridian_vocab():
    for path in sorted(ROOT.rglob("*")):
        rel = path.relative_to(ROOT).as_posix()
        if not path.is_file() or path.suffix in (".png", ".jpg", ".ico"):
            continue
        if rel.startswith(".git/") or "__pycache__" in rel \
                or rel.startswith(".pytest_cache/"):
            continue  # gitignored build artifacts, never shipped
        # The linter and the CI workflow mention the vocabulary by name in
        # order to check for it - they are not leaks.
        if rel.startswith("scripts/ci/") or rel.startswith(".github/"):
            continue
        # Design/validation records legitimately discuss the fork's
        # provenance, including the upstream Meridian coupling and the
        # model-tier codenames in the tiering tables. Documentation is
        # not a leak; the vocab gate exists for files that ship to users.
        if rel in ("DESIGN.md", "VALIDATION.md", "base-analysis.md"):
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        for m in MERIDIAN_VOCAB.finditer(text):
            line = text.count("\n", 0, m.start()) + 1
            err(rel, "Meridian vocabulary %r at line %d" % (m.group(0), line))


def check_attribution_headers():
    for rel in sorted(REQUIRED_HEADERS):
        path = ROOT / rel
        if not path.exists():
            err(rel, "required file missing")
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        head = text[:1200]
        if ("Adapted from" not in head and "credited to" not in head
                and "Mechanism from" not in head):
            err(rel, "missing attribution header (spec 3.5)")
            continue
        for m in HEADER_RE.finditer(head):
            cite = m.group(0)
            if not any(owner in cite for owner in ATTRIBUTION_OWNERS):
                err(rel, "header cites unknown owner/repo: %r" % cite[:60])
    # every header-bearing file must cite a known owner
    for path in sorted((ROOT / "skills").rglob("*.md")) + \
            sorted((ROOT / "hooks").rglob("*.sh")) + \
            sorted((ROOT / "hooks").rglob("*.py")) + \
            sorted((ROOT / "templates").rglob("*.md")):
        rel = path.relative_to(ROOT).as_posix()
        if rel in REQUIRED_HEADERS:
            continue
        head = path.read_text(encoding="utf-8", errors="replace")[:1200]
        for m in HEADER_RE.finditer(head):
            cite = m.group(0)
            if not any(owner in cite for owner in ATTRIBUTION_OWNERS):
                err(rel, "header cites unknown owner/repo: %r" % cite[:60])


def check_hooks_json():
    p = ROOT / "hooks" / "hooks.json"
    try:
        doc = json.loads(p.read_text(encoding="utf-8"))
        if "hooks" not in doc:
            err("hooks/hooks.json", "missing top-level 'hooks' key")
    except Exception as e:
        err("hooks/hooks.json", "JSON does not parse: %s" % e)


def check_size_cap():
    for path in sorted(ROOT.rglob("*")):
        if not path.is_file():
            continue
        rel = path.relative_to(ROOT).as_posix()
        if rel.startswith(".git/") or "__pycache__" in rel \
                or rel.startswith(".pytest_cache/"):
            continue  # gitignored build artifacts, never shipped
        size = path.stat().st_size
        if size > MAX_FILE_BYTES:
            err(rel, "file is %.1f KB (cap %d KB)"
                % (size / KB, MAX_FILE_BYTES // KB))


ALLOWED_MODELS = {"claude-opus-4-6", "claude-sonnet-5"}


def _parse_simple_frontmatter(text):
    """Parse the yaml-lite subset the plugin frontmatter uses (spec 3.2/3.3):
    top-level `key: value` scalars and `- item` block lists, `key: |` /
    `key: >` block scalars, inline flow lists. Returns (dict, error-or-None).
    None of the component validators in the claude CLI deep-check frontmatter
    (verified: a bogus model, name/filename mismatch, and no-frontmatter file
    all pass `claude plugins validate`), so CI owns these checks."""
    lines = text.split("\n")
    if not lines or lines[0].rstrip("\r").strip() != "---":
        return None, "missing YAML frontmatter"
    fm = {}
    cur = None
    for i, line in enumerate(lines[1:], start=2):
        s = line.rstrip("\r")
        if s.strip() in ("---", "..."):
            return fm, None
        if not s.strip() or s.strip().startswith("#"):
            continue
        if s[:1].isspace():
            continue  # block-scalar / nested content: not needed for checks
        if s.startswith("- ") or s == "-":
            if cur is None or not isinstance(fm.get(cur), list):
                return None, "line %d: list item outside a list key" % i
            fm[cur].append(s[1:].strip())
            continue
        m = re.match(r"^([A-Za-z0-9_-]+)\s*:\s*(.*)$", s.strip())
        if not m:
            return None, "line %d: unparseable frontmatter line: %r" % (
                i, s.strip())
        cur = m.group(1)
        val = m.group(2).strip()
        if val.startswith("[") and val.endswith("]"):
            items = [v.strip().strip("'\"")
                     for v in val[1:-1].split(",") if v.strip()]
            fm[cur] = items
            cur = None  # flow lists are complete
        elif val in ("|", ">"):
            fm[cur] = val  # block scalar marker: presence is what matters
        elif val == "":
            fm[cur] = []  # may become a block list
        else:
            fm[cur] = val.strip("'\"")
            cur = None  # scalar keys are not list targets
    return None, "unclosed frontmatter (no closing ---)"


def check_frontmatter():
    # Agents (spec 3.2): name matches filename, model is a real tiered id,
    # description present, every declared skill dir exists.
    for path in sorted(ROOT.glob("agents/*.md")):
        rel = path.relative_to(ROOT).as_posix()
        fm, e = _parse_simple_frontmatter(
            path.read_text(encoding="utf-8", errors="replace"))
        if fm is None:
            err(rel, e)
            continue
        name = fm.get("name")
        if not name:
            err(rel, "frontmatter missing name")
        elif name != path.stem:
            err(rel, "frontmatter name %r does not match filename %r"
                % (name, path.stem))
        model = fm.get("model")
        if model not in ALLOWED_MODELS:
            err(rel, "frontmatter model %r not in %s"
                % (model, sorted(ALLOWED_MODELS)))
        if not fm.get("description"):
            err(rel, "frontmatter missing description")
        for skill in fm.get("skills") or []:
            if not (ROOT / "skills" / skill / "SKILL.md").is_file():
                err(rel, "declared skill %r has no skills/%s/SKILL.md"
                    % (skill, skill))
    # Skill entry files (spec 3.3): name matches the directory, description
    # present.
    for path in sorted(ROOT.glob("skills/*/SKILL.md")):
        rel = path.relative_to(ROOT).as_posix()
        fm, e = _parse_simple_frontmatter(
            path.read_text(encoding="utf-8", errors="replace"))
        if fm is None:
            err(rel, e)
            continue
        name = fm.get("name")
        if not name:
            err(rel, "frontmatter missing name")
        elif name != path.parent.name:
            err(rel, "frontmatter name %r does not match directory %r"
                % (name, path.parent.name))
        if not fm.get("description"):
            err(rel, "frontmatter missing description")
    # Commands (spec 3.4): frontmatter with a description.
    for path in sorted(ROOT.glob("commands/*.md")):
        rel = path.relative_to(ROOT).as_posix()
        fm, e = _parse_simple_frontmatter(
            path.read_text(encoding="utf-8", errors="replace"))
        if fm is None:
            err(rel, e)
            continue
        if not fm.get("description"):
            err(rel, "frontmatter missing description")


def _tier1_patterns(text, list_name):
    """Extract the r"..." regex strings from a Python list literal
    (`TIER1 = [(r"\\b...\\b", ...), ...]` or `TIER1_PATTERNS = [r"...", ...]`)
    — the enforcement table in prose_core.py and the measurement table in
    style_stats.py must stay identical (judge-flag #15: metric drift)."""
    m = re.search(r"%s\s*=\s*\[(.*?)\n\]" % list_name, text, re.DOTALL)
    if not m:
        return None
    pats = []
    for line in m.group(1).split("\n"):
        s = re.search(r'r"([^"]+)"', line)
        if s:
            pats.append(s.group(1))
    return pats


def check_tier1_sync():
    core = ROOT / "hooks" / "scripts" / "prose_core.py"
    stats = ROOT / "scripts" / "vellum_lib" / "style_stats.py"
    try:
        core_pats = _tier1_patterns(core.read_text(encoding="utf-8"), "TIER1")
        stats_pats = _tier1_patterns(stats.read_text(encoding="utf-8"),
                                     "TIER1_PATTERNS")
    except OSError as e:
        err("scripts/ci/lint_vellum.py", "tier-1 sync check unreadable: %s" % e)
        return
    if core_pats is None or stats_pats is None:
        err("scripts/ci/lint_vellum.py",
            "tier-1 table not found in prose_core.py TIER1 / "
            "style_stats.py TIER1_PATTERNS")
        return
    if core_pats != stats_pats:
        only_core = [p for p in core_pats if p not in stats_pats]
        only_stats = [p for p in stats_pats if p not in core_pats]
        err("scripts/vellum_lib/style_stats.py",
            "tier-1 table diverges from hooks/scripts/prose_core.py TIER1 "
            "(enforced but not measured: %s; measured but not enforced: %s)"
            % (only_core or "[]", only_stats or "[]"))


def main():
    check_meridian_vocab()
    check_attribution_headers()
    check_hooks_json()
    check_size_cap()
    check_frontmatter()
    check_tier1_sync()
    if errors:
        for e in errors:
            print("::error %s" % e, file=sys.stderr)
        sys.stderr.write("lint_vellum: %d error(s).\n" % len(errors))
        return 1
    sys.stderr.write("lint_vellum: clean (vocab, headers, hooks.json, size "
                     "cap, frontmatter, tier-1 sync).\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
