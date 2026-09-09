# Vellum deterministic engine — pack (spec 5.2, deterministic half of spec 9).
# Original code (base design credited in ATTRIBUTION.md).
"""`pack chapter-NN` assembles the deterministic half of the writer context
pack: state card, scene brief path, previous-chapter tail (last ~600 words),
cast cards for `characters:`, relevant vocab sections, and ledger anchors
ranked by referenced entities. Emits JSON {paths, inline} on stdout."""
import json
import os
import re
import sys

from . import util
from .util import EXIT_OK, EXIT_ERROR

TAIL_WORDS = 650  # spec 9: ~500-800 words, never more


def _tail(body, words=TAIL_WORDS):
    """Last ~words of the body, cut at a paragraph boundary when possible."""
    text = body.strip()
    tokens = re.findall(r"\S+", text)
    if len(tokens) <= words:
        return text
    cut = text
    while len(re.findall(r"\S+", cut)) > words:
        idx = cut.rfind("\n\n")
        if idx <= 0:
            cut_tokens = re.findall(r"\S+", cut)[-words:]
            return "… " + " ".join(cut_tokens)
        cut = cut[idx + 2:]
    return cut


def _vocab_sections(root, terms):
    """kb/vocab.md sections whose heading or body mentions a term."""
    path = util.project_file(root, "kb", "vocab.md")
    sections = {}
    if not os.path.exists(path) or not terms:
        return sections
    text = util.read_file(path)
    blocks = re.split(r"\n(?=#+ )", text)
    low_terms = [t.lower() for t in terms]
    for b in blocks:
        low = b.lower()
        if any(t in low for t in low_terms):
            heading = (b.split("\n", 1)[0].strip("# ").strip()
                       or "section")
            sections["vocab: " + heading] = b.strip()[:1500]
    return sections


def run(root, chapter_arg):
    m = re.match(r"^chapter-0*(\d+)$", chapter_arg.strip(), re.IGNORECASE)
    if not m:
        util.die("pack expects a chapter id like 'chapter-07' (got %r)"
                 % chapter_arg)
    num = int(m.group(1))
    chapters = util.list_chapters(root)
    ch = next((c for c in chapters if c["num"] == num), None)
    if ch is None:
        util.die("chapter-%02d not found under manuscript/chapters/" % num)

    paths = []
    inline = {}

    # 2. state card
    card = util.project_file(root, "state", "state-card.md")
    if os.path.exists(card):
        paths.append("state/state-card.md")
        inline["state card"] = util.read_file(card)

    # 3. scene brief / outline
    outlines = util.outline_files(root)
    if num in outlines:
        o = outlines[num]
        paths.append(o["file"])
        inline["scene brief"] = util.read_file(o["path"])

    # 4. previous-chapter tail
    prev = [c for c in chapters if c["num"] < num]
    if prev:
        p = prev[-1]
        paths.append(p["file"])
        inline["previous-chapter tail (%s)" % p["file"]] = _tail(p["body"])

    # 5. cast cards (+ heavy mentions)
    cast = []
    for cid in (util_ledger_list(ch["fm"].get("characters"))
                + util_ledger_list(ch["fm"].get("mentions"))):
        if cid not in cast:
            cast.append(cid)
    for cid in cast:
        for pad in ("",):
            p = util.project_file(root, "kb", "characters", cid + ".md")
            if os.path.exists(p):
                paths.append("kb/characters/%s.md" % cid)
                fm, body = util.strip_frontmatter_text(util.read_file(p))
                inline["character card: %s" % cid] = body.strip()[:1200]

    # 7. relevant vocab
    terms = [re.sub(r"^character-", "", c).replace("-", " ") for c in cast]
    title = ch["fm"].get("title")
    if isinstance(title, str):
        terms += [w.lower() for w in re.findall(r"[A-Za-z]{4,}", title)]
    inline.update(_vocab_sections(root, terms))

    # 10. continuity anchors ranked by referenced entities
    anchors = []
    promises = _safe_entities(root, "promises")
    knowledge = _safe_entities(root, "knowledge")
    props = _safe_entities(root, "props")
    advanced = set(util_ledger_list(ch["fm"].get("promises-advanced")))
    for p in promises:
        pid = p["fm"].get("id", "")
        if pid in advanced:
            anchors.append("- %s — %s (advanced this chapter)"
                           % (pid, p["fm"].get("status")))
    for p in props:
        cust = p["fm"].get("custody")
        if isinstance(cust, dict) and cust.get("owner") in cast:
            anchors.append("- %s — owner %s, %s (%s)"
                           % (p["fm"].get("id"), cust.get("owner"),
                              cust.get("location"), cust.get("status")))
    for k in knowledge:
        holders = k["fm"].get("holders")
        if isinstance(holders, list):
            for h in holders:
                if isinstance(h, dict) and h.get("character") in cast:
                    anchors.append("- knowledge %s — %s holds (%s) since %s"
                                   % (k["fm"].get("id"), h.get("character"),
                                      h.get("certainty"), h.get("learned-in")))
    if anchors:
        inline["continuity anchors"] = "\n".join(anchors[:20])

    json.dump({"paths": paths, "inline": inline}, sys.stdout,
              ensure_ascii=False, indent=2)
    sys.stdout.write("\n")
    return EXIT_OK


def util_ledger_list(v):
    if isinstance(v, list):
        return [x for x in v if isinstance(x, str)]
    if isinstance(v, str):
        return [v]
    return []


def _safe_entities(root, kind):
    try:
        return util.load_entity_dir(root, kind)
    except util.FmError:
        return []
