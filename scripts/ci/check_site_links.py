#!/usr/bin/env python3
"""Check the generated site for broken local references and missing SEO.

Runs after ``scripts/build_site.py``. Standard library only, so the CI site job
needs nothing beyond the site build dependency (Jinja2).

Checks:
  - every local href/src in every generated HTML page resolves to a file in docs/
  - every page carries title, description, canonical, Open Graph, Twitter card,
    and a JSON-LD script
  - sitemap.xml lists every indexable page and no missing ones
  - CNAME matches the host constant in build_site.py
  - docs/og.png exists and is exactly 1200x630 (PNG header, no Pillow)

Exit 0 on success, 1 on any finding.
"""

import json
import re
import struct
import sys
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parent.parent.parent
DOCS = ROOT / "docs"

# Import the one host constant from the site build rather than duplicating it.
sys.path.insert(0, str(ROOT / "scripts"))
from build_site import SITE_HOST as BASE_HOST  # noqa: E402

LINK_RE = re.compile(r'(?:href|src)="([^"]+)"')

problems = []


def check_page(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    rel = path.relative_to(DOCS).as_posix()

    for url in LINK_RE.findall(text):
        if not url or url.startswith(("#", "mailto:", "tel:", "data:")):
            continue
        parsed = urlparse(url)
        if parsed.scheme in ("http", "https"):
            host = parsed.netloc
            if host == BASE_HOST:
                local = parsed.path
            else:
                continue  # external link; out of scope
        elif url.startswith("//"):
            continue
        else:
            local = parsed.path
            if not local:
                continue
        local = local.split("#", 1)[0].split("?", 1)[0]
        if not local:
            continue
        if local.startswith("/"):
            target = DOCS / local.lstrip("/")
        else:
            target = (path.parent / local).resolve()
        if local.endswith("/"):
            target = target / "index.html"
        if not target.exists():
            problems.append("%s: broken reference %r" % (rel, url))

    required = [
        ("<title>", "title"),
        ('name="description"', "meta description"),
        ('rel="canonical"', "canonical link"),
        ('property="og:title"', "Open Graph title"),
        ('property="og:image"', "Open Graph image"),
        ('name="twitter:card"', "Twitter card"),
        ('application/ld+json', "JSON-LD"),
    ]
    for needle, label in required:
        if needle not in text:
            problems.append("%s: missing %s" % (rel, label))

    # The JSON-LD block must parse.
    for block in re.findall(
        r'<script type="application/ld\+json">(.*?)</script>', text, re.S
    ):
        try:
            json.loads(block)
        except json.JSONDecodeError as exc:
            problems.append("%s: invalid JSON-LD (%s)" % (rel, exc))


def png_size(path: Path):
    with path.open("rb") as handle:
        header = handle.read(24)
    if header[:8] != b"\x89PNG\r\n\x1a\n":
        return None
    width, height = struct.unpack(">II", header[16:24])
    return width, height


def main() -> int:
    if not DOCS.exists():
        print("docs/ does not exist — run python scripts/build_site.py first")
        return 1

    pages = sorted(DOCS.glob("*.html"))
    if not pages:
        problems.append("no generated HTML pages found in docs/")

    for page in pages:
        check_page(page)

    sitemap = DOCS / "sitemap.xml"
    if not sitemap.exists():
        problems.append("sitemap.xml is missing")
    else:
        sitemap_text = sitemap.read_text(encoding="utf-8")
        listed = set(re.findall(r"<loc>([^<]+)</loc>", sitemap_text))
        expected = set()
        for page in pages:
            if page.name == "404.html":
                continue
            path = "/" if page.name == "index.html" else "/" + page.name
            expected.add("https://%s%s" % (BASE_HOST, path))
        for missing in sorted(expected - listed):
            problems.append("sitemap.xml is missing %s" % missing)
        for extra in sorted(listed - expected):
            problems.append("sitemap.xml lists a page that does not exist: %s" % extra)

    cname = DOCS / "CNAME"
    if not cname.exists():
        problems.append("CNAME is missing")
    elif cname.read_text(encoding="utf-8").strip() != BASE_HOST:
        problems.append(
            "CNAME does not match build_site.py SITE_HOST (%s)" % BASE_HOST
        )

    for required_file in ("robots.txt", ".nojekyll", "og.png"):
        if not (DOCS / required_file).exists():
            problems.append("docs/%s is missing" % required_file)

    og = DOCS / "og.png"
    if og.exists():
        size = png_size(og)
        if size != (1200, 630):
            problems.append("docs/og.png must be 1200x630 (found %s)" % (size,))

    if problems:
        print("site check failed with %d finding(s):" % len(problems))
        for problem in problems:
            print("  - " + problem)
        return 1

    print(
        "site check passed: %d pages, all local references resolve, "
        "SEO fields present, sitemap/CNAME consistent" % len(pages)
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
