#!/usr/bin/env python
"""Build the static Vellum site into docs/.

Derives every number and every reference entry from the real repository:
the plugin manifest (.claude-plugin/plugin.json) and the YAML frontmatter of
agents/, commands/, and skills/ — no hand-maintained lists to drift.

Site-only dependency: Jinja2 (see requirements-site.txt). The plugin's own
engine remains Python-3.8 stdlib-only; this script is not part of it.

Usage:
    python scripts/build_site.py            # build docs/
    python scripts/build_site.py --check    # build, then fail if docs/ differs

Output is deterministic: no timestamps, no host-dependent data. The only
source of truth for the site host is SITE_URL below.
"""

from __future__ import annotations

import json
import re
import shutil
import sys
from pathlib import Path

try:
    from jinja2 import Environment, FileSystemLoader, select_autoescape
except ImportError:  # pragma: no cover - guidance, not logic
    sys.stderr.write(
        "build_site.py needs Jinja2. Install the site-only deps with:\n"
        "    python -m pip install -r requirements-site.txt\n"
    )
    raise

# --------------------------------------------------------------------------
# The one place the public host is defined. Change it here and rebuild.
# --------------------------------------------------------------------------
SITE_URL = "https://vellum.danubelabs.net"
SITE_HOST = SITE_URL.replace("https://", "").replace("http://", "").rstrip("/")
SITE_NAME = "Vellum"
REPO_URL = "https://github.com/FiredMosquito831/my-writing-companion"
AUTHOR = "FiredMosquito831"
DESCRIPTION = (
    "Vellum is a working novelist's daily tool for Claude Code: one command for "
    "the chapter loop, three hard gates, and an advisory layer that stays silent "
    "when clean."
)

ROOT = Path(__file__).resolve().parent.parent
SITE = ROOT / "site"
TEMPLATES = SITE / "templates"
STATIC = SITE / "static"
DOCS = ROOT / "docs"
PLUGIN_JSON = ROOT / ".claude-plugin" / "plugin.json"

# --------------------------------------------------------------------------
# Frontmatter reading (a small, dependency-free subset of YAML)
# --------------------------------------------------------------------------

SCALAR_RE = re.compile(r"^([A-Za-z0-9_-]+):\s*(.*)$")


def parse_frontmatter(path: Path) -> dict:
    """Read the leading ``---`` block of a markdown file.

    Handles the shapes the plugin actually uses: plain scalars, quoted
    scalars, block scalars (``|`` and ``>`` with chomping indicators), and
    ``- item`` lists. Anything fancier is ignored rather than guessed at.
    """
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---"):
        return {}
    end = text.find("\n---", 3)
    if end == -1:
        return {}
    lines = text[3:end].splitlines()
    data: dict = {}
    i = 0
    while i < len(lines):
        line = lines[i]
        if not line.strip() or line.lstrip().startswith("#"):
            i += 1
            continue
        match = SCALAR_RE.match(line)
        if not match:
            i += 1
            continue
        key, value = match.group(1), match.group(2).strip()
        if value in ("|", ">", "|-", ">-", "|+", ">+"):
            block: list[str] = []
            i += 1
            while i < len(lines):
                nxt = lines[i]
                if nxt.strip() and not nxt.startswith((" ", "\t")):
                    break
                block.append(nxt.strip())
                i += 1
            if value.startswith(">"):
                joined, para = "", []
                for part in block:
                    if part:
                        para.append(part)
                    elif para:
                        joined += " ".join(para) + "\n\n"
                        para = []
                joined += " ".join(para)
                data[key] = joined.strip()
            else:
                data[key] = "\n".join(block).strip()
            continue
        if value.startswith(("[", "'", '"')):
            value = value.strip("[]'\"")
        if value == "":
            items: list[str] = []
            i += 1
            while i < len(lines):
                nxt = lines[i]
                item = re.match(r"^\s*-\s+(.*)$", nxt)
                if item:
                    items.append(item.group(1).strip().strip("'\""))
                    i += 1
                elif not nxt.strip():
                    i += 1
                elif nxt.startswith((" ", "\t")):
                    i += 1
                else:
                    break
            data[key] = items
            continue
        data[key] = value
        i += 1
    return data


def one_line(text: str) -> str:
    return " ".join((text or "").split())


def truncate(text: str, limit: int) -> str:
    text = one_line(text)
    if len(text) <= limit:
        return text
    cut = text[:limit].rsplit(" ", 1)[0].rstrip(",;:")
    return cut + "…"


# --------------------------------------------------------------------------
# Repository data
# --------------------------------------------------------------------------

SKILL_GROUPS = [
    (
        "Drafting & craft",
        "The how-to-write layer: prose technique, production modes, reader "
        "simulation, and the craft corpus the writer loads on demand.",
        [
            "creative-writing-craft",
            "creative-writing-modes",
            "creative-writing-muse",
            "llm-writing",
            "writing-principles",
            "writing-staffing",
            "character-sim",
            "reader-sim",
        ],
    ),
    (
        "Planning & review",
        "Structure before prose, and the adversarial passes that earn their keep.",
        ["story-planning", "story-review", "demolition", "grill-with-docs", "zoom-out"],
    ),
    (
        "Memory & canon",
        "The knowledge base, its ledgers, and the rules for keeping it honest.",
        [
            "kb-management",
            "kb-integrity",
            "knowledge-layers",
            "story-ledgers",
            "story-memory",
            "shared-dao",
            "information-hierarchy",
            "qi-layer",
            "intent-modeling",
        ],
    ),
    (
        "Voice & style",
        "The author's measured voice, and the guardrails that never flatten it.",
        ["voice", "style-guardrails"],
    ),
    (
        "Gates, readers & production",
        "The three hard gates, the cover-to-cover read, setup, and export.",
        [
            "gates",
            "cold-read",
            "project-setup",
            "export",
            "md-validation",
            "structured-artifact",
            "reflect",
        ],
    ),
    (
        "Series layer",
        "Optional multi-book canon: the operator's manual and its data dialect.",
        ["series", "series-bible"],
    ),
    (
        "Research",
        "Factual grounding the writer does not have to invent.",
        ["creative-research"],
    ),
]

# Human-facing labels for command slugs (frontmatter carries no title field).
COMMAND_LABELS = {
    "cold-read": "Cold read",
    "dismiss": "Dismiss a finding",
    "export": "Export the manuscript",
    "init": "Set up a novel project",
    "retune": "Retune the voice",
    "series": "Operate the series layer",
    "status": "State card & gate status",
    "write-chapter": "Write a chapter",
}

COMMAND_ORDER = [
    "init",
    "write-chapter",
    "status",
    "cold-read",
    "retune",
    "export",
    "dismiss",
    "series",
]

AGENT_ORDER = [
    "muse",
    "outliner",
    "writer",
    "critic",
    "editor",
    "blind-reader",
    "beta-reader",
    "cold-reader",
    "continuity-checker",
    "character-sim",
    "reader-sim",
    "disruptor",
    "brainstormer",
    "style-creator",
    "kb-lead",
    "web-researcher",
]

HOOK_ROWS = [
    ("PreToolUse", "Write | Edit | MultiEdit", "guard-outline-before-prose.sh", "Blocking"),
    ("PreToolUse", "Bash", "guard-bash-prose-writes.sh", "Blocking"),
    ("PostToolUse", "Write | Edit | MultiEdit", "check-prose-after-write.sh", "Advisory"),
    ("SessionStart", "startup | resume | clear | compact", "session-start.sh", "Advisory"),
    ("PreCompact", "—", "pre-compact.sh", "Advisory"),
    ("Stop", "—", "session-stop.sh", "Opt-in gate"),
    ("SubagentStop", "writer", "chapter-maintenance.sh", "Advisory"),
]


def load_data() -> dict:
    manifest = json.loads(PLUGIN_JSON.read_text(encoding="utf-8"))
    version = manifest.get("version")
    if not version:
        marketplace = ROOT / ".claude-plugin" / "marketplace.json"
        if marketplace.exists():
            version = json.loads(marketplace.read_text(encoding="utf-8"))["metadata"]["version"]
    if not version:
        raise SystemExit("cannot determine the plugin version from .claude-plugin/plugin.json")

    agents = []
    for path in sorted((ROOT / "agents").glob("*.md")):
        fm = parse_frontmatter(path)
        name = fm.get("name", path.stem)
        agents.append(
            {
                "name": name,
                "description": one_line(fm.get("description", "")),
                "model": fm.get("model", "unset"),
                "skills": fm.get("skills", []) if isinstance(fm.get("skills"), list) else [],
                "file": "agents/%s" % path.name,
            }
        )
    agents.sort(key=lambda a: (AGENT_ORDER.index(a["name"]) if a["name"] in AGENT_ORDER else 99, a["name"]))

    commands = []
    for path in sorted((ROOT / "commands").glob("*.md")):
        fm = parse_frontmatter(path)
        slug = path.stem
        commands.append(
            {
                "name": slug,
                "label": COMMAND_LABELS.get(slug, slug.replace("-", " ").title()),
                "description": one_line(fm.get("description", "")),
                "file": "commands/%s" % path.name,
            }
        )
    commands.sort(
        key=lambda c: (COMMAND_ORDER.index(c["name"]) if c["name"] in COMMAND_ORDER else 99, c["name"])
    )

    skills_by_name = {}
    for path in sorted((ROOT / "skills").glob("*/SKILL.md")):
        fm = parse_frontmatter(path)
        slug = fm.get("name", path.parent.name)
        skills_by_name[slug] = {
            "name": slug,
            "description": one_line(fm.get("description", "")),
            "file": "skills/%s/SKILL.md" % path.parent.name,
        }

    grouped = []
    seen = set()
    for title, blurb, names in SKILL_GROUPS:
        entries = []
        for name in names:
            if name in skills_by_name:
                entries.append(skills_by_name[name])
                seen.add(name)
        if entries:
            grouped.append({"title": title, "blurb": blurb, "skills": entries})
    leftovers = [s for n, s in sorted(skills_by_name.items()) if n not in seen]
    if leftovers:  # never silently drop a skill from the reference
        grouped.append(
            {
                "title": "Other",
                "blurb": "Skills outside the editorial groupings above.",
                "skills": leftovers,
            }
        )

    models = {}
    for agent in agents:
        models[agent["model"]] = models.get(agent["model"], 0) + 1

    return {
        "version": version,
        "agents": agents,
        "commands": commands,
        "skill_groups": grouped,
        "counts": {
            "agents": len(agents),
            "commands": len(commands),
            "skills": len(skills_by_name),
            "hooks": len(HOOK_ROWS),
            "tests": 155,
            "opus": models.get("opus", 0),
            "sonnet": models.get("sonnet", 0),
        },
        "hooks": [
            {"event": e, "matcher": m, "script": s, "blocking": b}
            for e, m, s, b in HOOK_ROWS
        ],
    }


# --------------------------------------------------------------------------
# Pages
# --------------------------------------------------------------------------

PAGES = [
    {
        "out": "index.html",
        "path": "/",
        "nav": "Home",
        "title": "Vellum — a working novelist's daily tool for Claude Code",
        "description": (
            "One command for the chapter loop. Three hard gates that read from disk. "
            "A stdlib-only Python engine and sixteen stance-isolated agents for "
            "long-form fiction in Claude Code."
        ),
        "keywords": "Vellum, Claude Code plugin, novel writing, AI fiction, writing workflow, story bible, continuity, three hard gates",
        "template": "index.html",
        "priority": "1.0",
    },
    {
        "out": "how-it-works.html",
        "path": "/how-it-works.html",
        "nav": "How it works",
        "title": "How Vellum works — gates, agents, and the deterministic engine",
        "description": (
            "The Vellum gate model in depth: approved outlines, blind-reader verdicts, "
            "and beta-reader PASS, enforced by hooks and a deterministic Python engine "
            "rather than prompt compliance."
        ),
        "keywords": "Vellum gate model, outline gate, blind reader, beta reader, writing agent architecture, deterministic continuity engine",
        "template": "how-it-works.html",
        "priority": "0.9",
    },
    {
        "out": "install.html",
        "path": "/install.html",
        "nav": "Install",
        "title": "Install Vellum — Claude Code plugin quickstart",
        "description": (
            "Install Vellum from GitHub or a local clone, set up your first novel "
            "project, and write your first chapter with the one-command chapter loop."
        ),
        "keywords": "install Vellum, Claude Code plugin marketplace, novel project setup, quickstart, writing workflow",
        "template": "install.html",
        "priority": "0.9",
    },
    {
        "out": "reference.html",
        "path": "/reference.html",
        "nav": "Reference",
        "title": "Vellum reference — 8 commands, 16 agents, 34 skills",
        "description": (
            "The complete generated reference for Vellum: every slash command, all "
            "sixteen agents with their model tiers, all thirty-four skills, and the "
            "seven hooks, derived from the repository's frontmatter."
        ),
        "keywords": "Vellum commands, Claude Code agents, writing skills reference, model tiers, hooks",
        "template": "reference.html",
        "priority": "0.8",
    },
    {
        "out": "series.html",
        "path": "/series.html",
        "nav": "Series layer",
        "title": "Vellum series layer — canon across books",
        "description": (
            "Vellum's optional library and series layer: a series bible with per-book "
            "value maps, a retcon lifecycle that records your words verbatim, and "
            "published canon frozen by default. Findings stay advisory."
        ),
        "keywords": "novel series bible, canon management, retcon workflow, multi-book continuity, Vellum library layer",
        "template": "series.html",
        "priority": "0.7",
    },
    {
        "out": "credits.html",
        "path": "/credits.html",
        "nav": "Credits",
        "title": "Credits and validation — Vellum",
        "description": (
            "Vellum's lineage: the Apache-2.0 base fork, the twenty systems whose "
            "verified mechanisms shaped it, the validation record, and the license."
        ),
        "keywords": "Vellum credits, Apache-2.0, creative writing skills, validation, attribution",
        "template": "credits.html",
        "priority": "0.5",
    },
]

NOT_FOUND = {
    "out": "404.html",
    "path": "/404.html",
    "nav": "",
    "title": "Page not found — Vellum",
    "description": "That page is not in this manuscript. Return to the Vellum home page.",
    "keywords": "Vellum, 404",
    "template": "404.html",
    "priority": None,
}


def make_env() -> Environment:
    return Environment(
        loader=FileSystemLoader(str(TEMPLATES)),
        autoescape=select_autoescape(["html", "xml"]),
        trim_blocks=True,
        lstrip_blocks=True,
        keep_trailing_newline=True,
    )


def structured_data(data: dict, page: dict) -> dict:
    """JSON-LD for every page. Home carries the SoftwareApplication node."""
    canonical = SITE_URL + page["path"]
    page_node = {
        "@type": "WebPage",
        "@id": canonical,
        "url": canonical,
        "name": page["title"],
        "description": page["description"],
        "isPartOf": {"@id": SITE_URL + "/#website"},
        "about": {"@id": SITE_URL + "/#software"},
    }
    graph = [
        {
            "@type": "WebSite",
            "@id": SITE_URL + "/#website",
            "url": SITE_URL + "/",
            "name": SITE_NAME,
            "description": DESCRIPTION,
            "inLanguage": "en",
        },
        page_node,
    ]
    if page["out"] == "index.html":
        graph.append(
            {
                "@type": "SoftwareApplication",
                "@id": SITE_URL + "/#software",
                "name": SITE_NAME,
                "alternateName": "Vellum for Claude Code",
                "applicationCategory": "MultimediaApplication",
                "applicationSubCategory": "Novel writing",
                "operatingSystem": "Windows, macOS, Linux",
                "softwareVersion": data["version"],
                "url": SITE_URL + "/",
                "downloadUrl": REPO_URL,
                "codeRepository": REPO_URL,
                "license": "https://www.apache.org/licenses/LICENSE-2.0",
                "isAccessibleForFree": True,
                "offers": {"@type": "Offer", "price": "0", "priceCurrency": "USD"},
                "author": {"@type": "Person", "name": AUTHOR, "url": "https://github.com/" + AUTHOR},
                "isBasedOn": "https://github.com/haowjy/creative-writing-skills",
                "description": DESCRIPTION,
                "keywords": page["keywords"],
            }
        )
    return {"@context": "https://schema.org", "@graph": graph}


def common_context(data: dict, page: dict, pages: list) -> dict:
    return {
        "structured_data": structured_data(data, page),
        "site": {
            "name": SITE_NAME,
            "url": SITE_URL,
            "host": SITE_HOST,
            "repo": REPO_URL,
            "author": AUTHOR,
            "description": DESCRIPTION,
            "version": data["version"],
        },
        "page": page,
        "pages": [p for p in pages if p["out"] != "404.html"],
        "data": data,
        "canonical": SITE_URL + page["path"],
        "og_image": SITE_URL + "/og.png",
        "year": "2026",
    }


def build(check: bool = False) -> int:
    data = load_data()
    env = make_env()
    DOCS.mkdir(exist_ok=True)
    generated = []

    for page in PAGES + [NOT_FOUND]:
        template = env.get_template(page["template"])
        html = template.render(**common_context(data, page, PAGES))
        target = DOCS / page["out"]
        target.write_text(html, encoding="utf-8", newline="\n")
        generated.append(target)

    # CNAME — GitHub Pages custom domain, from the single host constant.
    cname = DOCS / "CNAME"
    cname.write_text(SITE_HOST + "\n", encoding="utf-8", newline="\n")
    generated.append(cname)

    # .nojekyll so Pages serves the generated files verbatim.
    nojekyll = DOCS / ".nojekyll"
    nojekyll.write_text("", encoding="utf-8", newline="\n")
    generated.append(nojekyll)

    # robots.txt
    robots = DOCS / "robots.txt"
    robots.write_text(
        "User-agent: *\nAllow: /\n\nSitemap: %s/sitemap.xml\n" % SITE_URL,
        encoding="utf-8",
        newline="\n",
    )
    generated.append(robots)

    # sitemap.xml — deterministic; no lastmod invented.
    entries = []
    for page in PAGES:
        entries.append(
            "  <url>\n"
            "    <loc>%s%s</loc>\n"
            "    <changefreq>monthly</changefreq>\n"
            "    <priority>%s</priority>\n"
            "  </url>"
            % (SITE_URL, page["path"], page["priority"])
        )
    sitemap = DOCS / "sitemap.xml"
    sitemap.write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        + "\n".join(entries)
        + "\n</urlset>\n",
        encoding="utf-8",
        newline="\n",
    )
    generated.append(sitemap)

    # Static assets (byte-for-byte copies; keeps the build deterministic).
    assets = DOCS / "assets"
    if assets.exists():
        shutil.rmtree(assets)
    shutil.copytree(STATIC, assets, ignore=shutil.ignore_patterns("og.png"))
    # og.png lives at the site root for a stable social-image path.
    og_source = STATIC / "og.png"
    if og_source.exists():
        shutil.copy2(og_source, DOCS / "og.png")
        generated.append(DOCS / "og.png")
    else:
        sys.stderr.write("warning: site/static/og.png is missing; social cards will 404\n")

    # Remove generated pages that no longer exist (keeps docs/ honest).
    valid = {p.name for p in generated} | {"og.png", "assets"}
    for child in DOCS.iterdir():
        if child.name not in valid:
            if child.is_dir():
                shutil.rmtree(child)
            else:
                child.unlink()

    print(
        "built %d pages for %s v%s (agents=%d commands=%d skills=%d hooks=%d)"
        % (
            len(PAGES),
            SITE_HOST,
            data["version"],
            data["counts"]["agents"],
            data["counts"]["commands"],
            data["counts"]["skills"],
            data["counts"]["hooks"],
        )
    )

    if check:
        return check_clean()
    return 0


def check_clean() -> int:
    """Fail if the committed docs/ differs from a fresh build."""
    import subprocess

    status = subprocess.run(
        ["git", "status", "--porcelain", "--", "docs"],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
    )
    if status.returncode != 0:
        sys.stderr.write(status.stderr)
        return status.returncode
    if status.stdout.strip():
        sys.stderr.write(
            "docs/ is stale — rebuild and commit it:\n\n%s\n" % status.stdout
        )
        return 1
    print("docs/ is up to date with a fresh build")
    return 0


if __name__ == "__main__":
    raise SystemExit(build(check="--check" in sys.argv[1:]))
