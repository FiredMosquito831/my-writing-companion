# Vellum deterministic engine — wordcount (spec 5.2).
# Original code (base design credited in ATTRIBUTION.md).
"""Words per chapter via the word rule; --write updates the `word-count`
frontmatter field; band check vs word-target (default +/-15% from project
config) with a pointer to prose-writing compression guidance."""
import re
import sys

from . import util
from .util import EXIT_OK, EXIT_FINDINGS, EXIT_ERROR, make_finding


def _update_word_count(path, fm, body, count):
    """Rewrite the frontmatter `word-count:` field, preserving the body."""
    text = util.read_file(path)
    lines = text.split("\n")
    if not lines or not re.match(r"^---\s*$", lines[0].rstrip("\r")):
        return  # no frontmatter: nothing to update (never inject a new block)
    for i in range(1, len(lines)):
        if re.match(r"^---\s*$", lines[i].rstrip("\r")):
            break
        if re.match(r"^word-count\s*:", lines[i]):
            lines[i] = re.sub(r"^word-count\s*:.*$", "word-count: %d" % count,
                              lines[i])
            new = "\n".join(lines)
            util.atomic_write(path, new)
            return
    # field absent: insert before the closing ---, keeping any inline comment layout
    lines.insert(i, "word-count: %d" % count)
    util.atomic_write(path, "\n".join(lines))


def run(root, write=False, chapter_paths=None):
    cfg = util.load_config(root)
    chapters = util.list_chapters(root)
    if chapter_paths:
        want = set()
        for p in chapter_paths:
            norm = p.replace("\\", "/").split("/")[-1].lower()
            want.add(norm)
        chapters = [c for c in chapters if c["name"].lower() in want]
        if not chapters:
            util.die("no matching chapters for %s" % ", ".join(chapter_paths))

    findings = []
    for c in chapters:
        fm = c["fm"]
        count = c["words"]
        if write:
            _update_word_count(c["path"], fm, c["body"], count)
            sys.stdout.write("%s: %d words (word-count updated)\n"
                             % (c["file"], count))
        else:
            sys.stdout.write("%s: %d words\n" % (c["file"], count))
        target = fm.get("word-target")
        if not isinstance(target, int):
            target = cfg.get("default_word_target")
        band = float(cfg.get("word_band", 0.15))
        if isinstance(target, int) and target > 0 and c["fm"].get("status") in (
                "draft", "revised", "accepted", "final"):
            lo, hi = target * (1 - band), target * (1 + band)
            if not (lo <= count <= hi):
                findings.append(make_finding(
                    "word-band", "suggestion", c["file"], 0,
                    "%d words" % count,
                    "chapter %s is %d words against a %d target (+/-%.0f%%) - "
                    "outside band; see creative-writing-craft/resources/"
                    "prose-writing.md for compression or expansion guidance."
                    % (c["file"], count, target, band * 100),
                    key="band:chapter-%02d" % c["num"],
                    audit="structure"))
    findings = util.filter_findings(findings, util.load_exemptions(root))
    if findings:
        util.emit_findings(findings)
        sys.stderr.write("wordcount: %d finding(s) outside band.\n" % len(findings))
        return EXIT_FINDINGS
    return EXIT_OK
