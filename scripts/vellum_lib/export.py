# Vellum deterministic engine — readiness / export build (spec 5.2, 10.2).
# Original code (base design credited in ATTRIBUTION.md).
"""`readiness` evaluates the section-10 preconditions and prints PASS or a
prioritized missing list. `export build --out DIR [--epub]` assembles the
markdown bundle (title page, copyright placeholder, joined chapters) and
manifest.md with sha256 checksums + per-chapter gate provenance; --epub
builds a stdlib-zipfile EPUB with the stable urn:uuid from kb/story.md."""
import hashlib
import json
import os
import re
import sys
import zipfile
from datetime import date
from xml.sax.saxutils import escape as xml_escape

from . import util
from .util import EXIT_OK, EXIT_FINDINGS, EXIT_ERROR

SEV_RE = re.compile(r"CR-\d+\s*\|[^|]*\|\s*(BLOCKER|MAJOR|MODERATE|MINOR)\s*\|",
                    re.IGNORECASE)
TRIAGE_NOTE = re.compile(r"\|\s*(fixed|deferred-with-author-signoff|"
                         r"accepted-limitation)\s*\|", re.IGNORECASE)


# ---------------------------------------------------------------------------
# readiness
# ---------------------------------------------------------------------------

def readiness(root):
    missing = []

    chapters = util.list_chapters(root)
    if not chapters:
        missing.append("no chapters under manuscript/chapters/ — nothing to "
                       "export.")

    # 1. every chapter final + frontmatter complete
    for c in chapters:
        fm = c["fm"]
        if fm.get("status") != "final":
            missing.append("%s has status %r (required: final)."
                           % (c["file"], fm.get("status")))
        for req in ("number", "pov", "characters", "mentions",
                    "promises-advanced", "word-count"):
            if fm.get(req) is None and c["words"] >= 200:
                missing.append("%s frontmatter missing %r."
                               % (c["file"], req))

    # bible validate clean (or exempted) — findings after exemption filter
    from . import bible as bible_mod
    bfindings, _ = bible_mod._validate_all(root)
    bfindings += bible_mod._validate_chapter_xrefs(root)
    bfindings = util.filter_findings(bfindings, util.load_exemptions(root))
    for f in bfindings:
        missing.append("bible: [%s] %s (%s)"
                       % (f["severity"], f["issue"], f["key"]))

    # 2. ledger check clean
    from . import ledgers as ledgers_mod
    lfindings = ledgers_mod._collect(root)
    for f in lfindings:
        missing.append("ledger: [%s] %s (%s)"
                       % (f["severity"], f["issue"], f["key"]))

    # cold-read issues: no open BLOCKER; MAJOR/MODERATE need a triage note
    issues_path = _latest_issues(root)
    if issues_path is not None:
        lines = util.read_file(issues_path).split("\n")
        for i, line in enumerate(lines):
            m = SEV_RE.search(line)
            if not m:
                continue
            sev = m.group(1).upper()
            window = "\n".join(lines[i:i + 3])
            triaged = bool(TRIAGE_NOTE.search(window))
            if sev == "BLOCKER" and not triaged:
                missing.append("cold-read open BLOCKER: %s (%s)"
                               % (line.strip()[:80],
                                  os.path.relpath(issues_path, root)))
            elif sev in ("MAJOR", "MODERATE") and not triaged:
                missing.append("cold-read %s without triage note (fixed / "
                               "deferred-with-author-signoff / "
                               "accepted-limitation): %s"
                               % (sev, line.strip()[:80]))

    # 3. readiness report exists, internally consistent, PASS rule
    report = util.project_file(root, "work", "critique-reports",
                               "readiness-report.md")
    if not os.path.exists(report):
        missing.append("work/critique-reports/readiness-report.md is missing "
                       "(beta-reader verdict on disk).")
    else:
        fm, _ = util.strip_frontmatter_text(util.read_file(report))
        problems = _report_problems(fm)
        for p in problems:
            missing.append("readiness report: %s" % p)
        for p in _transcript_problems(root, fm):
            missing.append("readiness report: %s" % p)

    # 4. word-budget report: wordcount band compliance
    from . import wordcount as wordcount_mod
    band_findings = []
    cfg = util.load_config(root)
    for c in chapters:
        target = c["fm"].get("word-target")
        if not isinstance(target, int):
            target = cfg.get("default_word_target")
        band = float(cfg.get("word_band", 0.15))
        if c["fm"].get("status") in ("draft", "revised", "accepted", "final") \
                and isinstance(target, int) and target > 0:
            lo, hi = target * (1 - band), target * (1 + band)
            if not (lo <= c["words"] <= hi):
                band_findings.append("%s is %d words against a %d target."
                                     % (c["file"], c["words"], target))
    if band_findings:
        missing.append("word budget: %d chapter(s) outside band — %s"
                       % (len(band_findings), "; ".join(band_findings[:3])))

    # 5. pivotal chapters have blind artifacts (verdict != LOST, with the
    #    same transcript provenance binding as the readiness report)
    outlines = util.outline_files(root)
    for num, o in sorted(outlines.items()):
        if o["fm"].get("pivotal") is True:
            verdict = _blind_verdict(root, num)
            if verdict is None:
                missing.append("pivotal chapter %02d has no blind-reader "
                               "artifact (work/critique-reports/"
                               "blind-chapter-NN.md)." % num)
            elif verdict == "LOST":
                missing.append("pivotal chapter %02d blind verdict is LOST — "
                               "acceptance blocked." % num)
            for p in _blind_transcript_problems(root, num):
                missing.append("pivotal chapter %02d: %s" % (num, p))

    if missing:
        sys.stderr.write("readiness: NOT READY — %d item(s), prioritized:\n"
                         % len(missing))
        for i, m in enumerate(missing, 1):
            sys.stderr.write("%d. %s\n" % (i, m))
        return EXIT_FINDINGS
    sys.stdout.write("readiness: PASS — all section-10 preconditions "
                     "satisfied.\n")
    return EXIT_OK


def _transcript_problems(root, fm, allowed=("PASS", "REVISE")):
    """Provenance binding for a gate artifact (spec 10.2 gate provenance).
    Subagents are barred from writing work/critique-reports/ — the muse is
    the artifact's only writer, and it is the agent that wants the gate to
    pass — so the artifact must cite the subagent transcript it transcribes,
    and that transcript must exist and carry the verdict. A self-consistent
    fabricated report with no run behind it fails here instead of passing
    the gate. Used for the readiness report (PASS|REVISE) and the blind
    artifacts (ENGAGED|STALLED|LOST)."""
    verdict = fm.get("verdict")
    if verdict not in allowed:
        return []  # verdict validity is reported by the verdict checks
    tr = fm.get("transcript")
    if not isinstance(tr, str) or not tr.strip():
        return ["transcript provenance missing — frontmatter `transcript:` "
                "must cite the beta-reader subagent transcript path (the "
                "muse records it when persisting the report)."]
    tr = tr.strip().replace("\\", "/")
    tp = tr if os.path.isabs(tr) else util.project_file(root, *tr.split("/"))
    if not os.path.isfile(tp):
        return ["transcript %r does not exist — the report cites no "
                "beta-reader run." % tr]
    try:
        with open(tp, "r", encoding="utf-8", errors="replace") as f:
            text = f.read()
    except OSError:
        return ["transcript %r is unreadable." % tr]
    if not re.search(r"\b%s\b" % verdict, text):
        return ["transcript %r contains no %s verdict — the report does not "
                "match the run it cites." % (tr, verdict)]
    return []


def _blind_verdict(root, num):
    for pad in ("%02d", "%03d", "%d"):
        p = util.project_file(root, "work", "critique-reports",
                              ("blind-chapter-%s.md" % pad) % num)
        if os.path.exists(p):
            fm, _ = util.strip_frontmatter_text(util.read_file(p))
            return fm.get("verdict")
    return None


def _blind_transcript_problems(root, num):
    """Provenance binding for the blind artifact itself (same asymmetry as
    the readiness report: muse transcribes blind-chapter-NN.md and wants
    acceptance, so the artifact must cite the blind-reader subagent
    transcript that carries the verdict it records)."""
    for pad in ("%02d", "%03d", "%d"):
        p = util.project_file(root, "work", "critique-reports",
                              ("blind-chapter-%s.md" % pad) % num)
        if os.path.exists(p):
            fm, _ = util.strip_frontmatter_text(util.read_file(p))
            return _transcript_problems(
                root, fm, allowed=("ENGAGED", "STALLED", "LOST"))
    return []


def _report_problems(fm):
    """Internal-consistency + PASS-rule checks on the readiness report
    (provenance binding: the artifact must at least agree with itself)."""
    problems = []
    verdict = fm.get("verdict")
    if verdict not in ("PASS", "REVISE"):
        problems.append("verdict %r is not PASS | REVISE." % verdict)
        return problems
    axes = fm.get("axes")
    if not isinstance(axes, dict) or not axes:
        problems.append("axes missing or not a map of five 1-10 scores.")
        return problems
    vals = []
    for k, v in sorted(axes.items()):
        if not isinstance(v, (int, float)) or not (1 <= v <= 10):
            problems.append("axis %s = %r is not a 1-10 score." % (k, v))
        else:
            vals.append(float(v))
    if vals:
        mean = sum(vals) / len(vals)
        score = fm.get("score")
        if not isinstance(score, (int, float)):
            problems.append("score missing (must be the mean of the axes).")
        elif abs(score - mean) > 0.051:
            problems.append("score %s does not equal the mean of the axes "
                            "(%.2f) — the artifact is internally "
                            "inconsistent." % (score, mean))
        if verdict == "PASS":
            below = [k for k, v in sorted(axes.items())
                     if isinstance(v, (int, float)) and v < 7]
            if below:
                problems.append("verdict PASS but axis(es) below 7: %s."
                                % ", ".join(below))
            if mean < 7.5:
                problems.append("verdict PASS but axis mean %.2f < 7.5."
                                % mean)
    put = fm.get("put_down_points")
    if isinstance(put, list) and verdict == "PASS":
        early = [p for p in put
                 if isinstance(p, int) and 1 <= p <= 3]
        if early:
            problems.append("verdict PASS but put-down points in chapters "
                            "1-3: %s." % early)
    if fm.get("readers") is None:
        problems.append("readers count missing.")
    elif not isinstance(fm.get("readers"), int) or fm["readers"] < 1:
        problems.append("readers count %r is not a positive integer."
                        % fm.get("readers"))
    if fm.get("read_at") is None:
        problems.append("read_at date missing.")
    return problems


def _latest_issues(root):
    base = util.project_file(root, "work", "cold-reads")
    if not os.path.isdir(base):
        return None
    best = None
    for name in sorted(os.listdir(base)):
        p = os.path.join(base, name, "issues.md")
        if os.path.exists(p):
            best = p
    return best


# ---------------------------------------------------------------------------
# export build
# ---------------------------------------------------------------------------

def _chapter_provenance(root, chapters):
    """Per-chapter gate provenance for the manifest (spec 10.2): outline
    approval, blind verdict, demolition log presence. Never silent —
    missing artifacts are listed as such."""
    outlines = util.outline_files(root)
    prov = {}
    for c in chapters:
        num = c["num"]
        o = outlines.get(num)
        row = {
            "outline": o["file"] if o else None,
            "approved": bool(o and o["fm"].get("approved") is True),
            "pivotal": bool(o and o["fm"].get("pivotal") is True),
            "blind-verdict": _blind_verdict(root, num),
            "status": c["fm"].get("status"),
            "overrides": [],
        }
        prov[c["file"]] = row
    # logged overrides: stale exemptions the author re-armed or accepted
    for e in util.load_exemptions(root).get("exemptions", []):
        if e.get("status") == "stale":
            for row in prov.values():
                row["overrides"].append("stale exemption %s (%s)"
                                        % (e.get("key"), e.get("stale_note", "")))
    return prov


def _matter_files(root, sub):
    """Sorted .md files from manuscript/<sub>/ (front-matter / back-matter),
    per assembly.md's order of parts. Missing directory -> empty list."""
    d = util.project_file(root, "manuscript", sub)
    out = []
    if os.path.isdir(d):
        for name in sorted(os.listdir(d)):
            p = os.path.join(d, name)
            if name.endswith(".md") and os.path.isfile(p):
                out.append(p)
    return out


def _matter_page(path):
    """(title, body) for a front/back matter file (frontmatter stripped)."""
    fm, body = util.strip_frontmatter_text(util.read_file(path))
    return (str(fm.get("title") or os.path.basename(path)[:-3]),
            body.strip())


def build(root, out_dir, epub=False):
    chapters = [c for c in util.list_chapters(root)
                if c["fm"].get("status") == "final"]
    if not chapters:
        util.die("export build: no chapters with status: final — run "
                 "'vellum readiness' first.")
    story = util.load_story(root)
    title = story.get("title", "Untitled")
    author = story.get("author", "")
    year = story.get("year", str(date.today().year))
    book_uuid = story.get("book-uuid", "")

    out_dir = os.path.join(root, out_dir) if not os.path.isabs(out_dir) else out_dir
    os.makedirs(out_dir, exist_ok=True)

    front = [_matter_page(p) for p in _matter_files(root, "front-matter")]
    back = [_matter_page(p) for p in _matter_files(root, "back-matter")]

    # Title page + copyright placeholder (spec 10.2), then front matter,
    # chapters, back matter in assembly.md's order of parts.
    parts = []
    parts.append("# %s\n" % title)
    if author:
        parts.append("by %s\n" % author)
    parts.append("%s\n" % year)
    parts.append("\n---\n\nCopyright © %s %s. All rights reserved.\n\n"
                 "This is a copyright placeholder — replace before "
                 "publication.\n" % (year, author or "the author"))
    for _mt, body in front:
        parts.append("\n\n---\n\n")
        parts.append(body + "\n")
    for c in chapters:
        parts.append("\n\n---\n\n")
        fm, body = util.strip_frontmatter_text(util.read_file(c["path"]))
        parts.append("# %s\n\n" % (fm.get("title") or c["name"][:-3]))
        body = re.sub(r"^\s*\*\s*\*\s*\*\s*$", "* * *",
                      body, flags=re.MULTILINE)  # scene-break convention
        parts.append(body.strip() + "\n")
    for _mt, body in back:
        parts.append("\n\n---\n\n")
        parts.append(body + "\n")

    md_path = os.path.join(out_dir, "manuscript.md")
    md_content = "".join(parts)
    util.atomic_write(md_path, md_content)

    # manifest with checksums + gate provenance
    prov = _chapter_provenance(root, chapters)
    lines = ["# Export Manifest", ""]
    lines.append("Built %s from %d final chapter(s). Source of truth: "
                 "`manuscript/` (untouched)." % (date.today().isoformat(),
                                                 len(chapters)))
    lines.append("")
    lines.append("| chapter | words | sha256 | approved outline | pivotal | blind verdict |")
    lines.append("|---|---|---|---|---|---|")
    for c in chapters:
        row = prov[c["file"]]
        with open(c["path"], "rb") as f:
            digest = hashlib.sha256(f.read()).hexdigest()
        lines.append("| %s | %d | %s | %s | %s | %s |" % (
            c["file"], c["words"], digest[:16],
            row["approved"], row["pivotal"],
            row["blind-verdict"] or "none"))
    lines.append("")
    if any(row["overrides"] for row in prov.values()):
        lines.append("## Logged overrides")
        lines.append("")
        for f, row in prov.items():
            for o in row["overrides"]:
                lines.append("- %s: %s" % (f, o))
        lines.append("")
    if book_uuid:
        lines.append("Stable EPUB identifier: `urn:uuid:%s` (highlights "
                     "survive rebuilds)." % book_uuid)
    lines.append("DOCX/PDF: via pandoc when present; otherwise convert the "
                 "markdown bundle with your editor of choice.")
    lines.append("")
    util.atomic_write(os.path.join(out_dir, "manifest.md"), "\n".join(lines))

    if epub:
        _build_epub(out_dir, title, author, book_uuid, chapters, year,
                    front, back)

    sys.stdout.write("export build: wrote %s (%d chapter(s), %d front-matter "
                     "file(s), %d back-matter file(s)); manifest at %s\n"
                     % (os.path.relpath(md_path, root), len(chapters),
                        len(front), len(back),
                        os.path.relpath(os.path.join(out_dir, "manifest.md"),
                                        root)))
    return EXIT_OK


def _build_epub(out_dir, title, author, book_uuid, chapters, year,
                front=(), back=()):
    uuid = book_uuid or ("urn:uuid:%s" % hashlib.sha256(
        (title + author).encode("utf-8")).hexdigest())
    if not uuid.startswith("urn:"):
        uuid = "urn:uuid:%s" % uuid
    epub_path = os.path.join(out_dir, "manuscript.epub")
    container = ('<?xml version="1.0"?>\n<container version="1.0" '
                 'xmlns="urn:oasis:names:tc:opendocument:xmlns:container">\n'
                 '  <rootfiles>\n    <rootfile full-path="OEBPS/content.opf" '
                 'media-type="application/oebps-package+xml"/>\n  </rootfiles>\n'
                 '</container>\n')
    manifest, spine = [], []
    files = {}
    files["OEBPS/title.xhtml"] = (
        '<?xml version="1.0" encoding="utf-8"?>\n<!DOCTYPE html>'
        '\n<html xmlns="http://www.w3.org/1999/xhtml"><head>'
        '<title>%s</title></head><body><h1>%s</h1><p>%s</p><p>%s</p>'
        '</body></html>' % (xml_escape(title), xml_escape(title),
                            xml_escape(author), xml_escape(str(year))))
    manifest.append('<item id="title" href="title.xhtml" '
                    'media-type="application/xhtml+xml"/>')
    spine.append('<itemref idref="title"/>')

    def _add_page(page_id, heading, body_text):
        paras = "\n".join("<p>%s</p>" % xml_escape(p.strip())
                          for p in body_text.split("\n\n") if p.strip())
        files["OEBPS/%s.xhtml" % page_id] = (
            '<?xml version="1.0" encoding="utf-8"?>\n<!DOCTYPE html>'
            '\n<html xmlns="http://www.w3.org/1999/xhtml"><head>'
            '<title>%s</title></head><body><h2>%s</h2>%s</body></html>'
            % (xml_escape(heading), xml_escape(heading), paras))
        manifest.append('<item id="%s" href="%s.xhtml" '
                        'media-type="application/xhtml+xml"/>' % (page_id,
                                                                  page_id))
        spine.append('<itemref idref="%s"/>' % page_id)

    # Front matter / back matter pages (same order of parts as the bundle).
    for j, (mt, body) in enumerate(front, 1):
        _add_page("front%03d" % j, mt, body)
    for i, c in enumerate(chapters, 1):
        fm, body = util.strip_frontmatter_text(util.read_file(c["path"]))
        ctitle = xml_escape(fm.get("title") or c["name"][:-3])
        paras = "\n".join("<p>%s</p>" % xml_escape(p.strip())
                          for p in body.strip().split("\n\n") if p.strip())
        files["OEBPS/ch%03d.xhtml" % i] = (
            '<?xml version="1.0" encoding="utf-8"?>\n<!DOCTYPE html>'
            '\n<html xmlns="http://www.w3.org/1999/xhtml"><head>'
            '<title>%s</title></head><body><h2>%s</h2>%s</body></html>'
            % (ctitle, ctitle, paras))
        manifest.append('<item id="ch%03d" href="ch%03d.xhtml" '
                        'media-type="application/xhtml+xml"/>' % (i, i))
        spine.append('<itemref idref="ch%03d"/>' % i)
    for j, (mt, body) in enumerate(back, 1):
        _add_page("back%03d" % j, mt, body)
    opf = ('<?xml version="1.0" encoding="utf-8"?>\n'
           '<package xmlns="http://www.idpf.org/2007/opf" version="3.0" '
           'unique-identifier="bookid">\n'
           '<metadata xmlns:dc="http://purl.org/dc/elements/1.1/">\n'
           '<dc:identifier id="bookid">%s</dc:identifier>\n'
           '<dc:title>%s</dc:title>\n<dc:creator>%s</dc:creator>\n'
           '<dc:language>en</dc:language>\n'
           '<meta property="dcterms:modified">%s</meta>\n'
           '</metadata>\n<manifest>\n%s\n</manifest>\n<spine>\n%s\n</spine>\n'
           '</package>\n'
           % (uuid, xml_escape(title), xml_escape(author),
              date.today().strftime("%Y-%m-%dT00:00:00Z"),
              "\n".join(manifest), "\n".join(spine)))
    nav = ('<?xml version="1.0" encoding="utf-8"?>\n<!DOCTYPE html>\n'
           '<html xmlns="http://www.w3.org/1999/xhtml" '
           'xmlns:epub="http://www.idpf.org/2007/ops"><head>'
           '<title>Contents</title></head><body><nav epub:type="toc">'
           '<ol><li><a href="title.xhtml">Title</a></li>' +
           "".join('<li><a href="ch%03d.xhtml">Chapter %d</a></li>' % (i, i)
                   for i in range(1, len(chapters) + 1)) +
           '</ol></nav></body></html>')
    with zipfile.ZipFile(epub_path, "w") as z:
        z.writestr("mimetype", "application/epub+zip",
                   compress_type=zipfile.ZIP_STORED)
        z.writestr("META-INF/container.xml", container)
        z.writestr("OEBPS/content.opf", opf)
        z.writestr("OEBPS/nav.xhtml", nav)
        for name, content in files.items():
            z.writestr(name, content)
    sys.stdout.write("export build: epub at %s\n"
                     % os.path.relpath(epub_path, os.path.dirname(out_dir)
                                       or "."))
