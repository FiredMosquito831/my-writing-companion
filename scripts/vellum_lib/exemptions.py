# Vellum deterministic engine — dismiss / debt (spec 5.2).
# Original code (base design credited in ATTRIBUTION.md).
"""`dismiss <key> --reason`: appends {key, reason, dismissed_at, chapter,
status: active} to kb/exemptions.json; refuses a duplicate active key; when
the key references a kb entity, records its sha256 so `bible validate` can
flip the exemption to stale when the underlying fact changes (re-arm once).
`debt list` / `debt clear` read work/voice-debt.json (written by the
post-write hook)."""
import hashlib
import json
import os
import sys
from datetime import date

from . import util
from .util import EXIT_OK, EXIT_ERROR

VALID_CATEGORIES = ("continuity", "canon", "voice", "craft", "structure",
                    "pace", "repeat", "frontmatter", "band", "state")


def dismiss(root, key, reason, chapter=None):
    if not key or not reason:
        util.die("dismiss requires a key and --reason (the author's words, "
                 "verbatim).")
    cat = key.split(":", 1)[0]
    if cat not in VALID_CATEGORIES:
        util.die("key category %r is not valid (use <category>:<entity_id> "
                 "with category in %s)." % (cat, "|".join(VALID_CATEGORIES)))

    doc = util.load_exemptions(root)
    for e in doc.get("exemptions", []):
        if e.get("key") == key and e.get("status") == "active":
            util.die("exemption %r already exists and is active; the machine "
                     "never re-litigates a dismissed choice." % key)

    entry = {
        "key": key,
        "reason": reason,
        "dismissed_at": date.today().isoformat(),
        "chapter": chapter,
        "status": "active",
    }
    # Record an entity basis when the key references a kb entity file, so
    # bible validate can flip this to stale when the fact changes.
    entity = _entity_for_key(root, key)
    if entity:
        rel, path = entity
        with open(path, "rb") as f:
            entry["entity"] = rel
            entry["entity_hash"] = hashlib.sha256(f.read()).hexdigest()

    doc["exemptions"].append(entry)
    util.atomic_write(util.exemptions_path(root),
                      json.dumps(doc, indent=2, ensure_ascii=False) + "\n")
    sys.stdout.write("dismissed %s (active). Reason recorded verbatim: %s\n"
                     % (key, reason))
    return EXIT_OK


def _entity_for_key(root, key):
    """Map `continuity:character-old-tom` -> (kb/characters/character-old-tom.md,
    abspath) when the entity id names an existing kb file. Clock-thread keys
    (`continuity:clock-<thread>`, e.g. `continuity:clock-debt-run`) map to
    kb/clock.md so a clock dismissal flips stale when the clock table
    changes — the same re-arm-on-fact-change behavior as entity dismissals."""
    _, _, entity_id = key.partition(":")
    if not entity_id:
        return None
    if entity_id == "clock" or entity_id.startswith("clock-"):
        p = util.project_file(root, "kb", "clock.md")
        if os.path.exists(p):
            return ("kb/clock.md", p)
        return None
    for kind in ("characters", "promises", "questions", "knowledge", "props"):
        p = util.project_file(root, "kb", kind, entity_id + ".md")
        if os.path.exists(p):
            return ("kb/%s/%s.md" % (kind, entity_id), p)
    return None


def _load_debt(root):
    p = util.project_file(root, "work", "voice-debt.json")
    if not os.path.exists(p):
        return {"schema_version": 1, "items": []}, p
    try:
        with open(p, "r", encoding="utf-8") as f:
            doc = json.load(f)
    except Exception:
        return {"schema_version": 1, "items": []}, p
    if not isinstance(doc.get("items"), list):
        doc["items"] = []
    return doc, p


def debt_list(root):
    doc, _ = _load_debt(root)
    items = [it for it in doc.get("items", []) if it.get("status") == "open"]
    if not items:
        sys.stdout.write("voice debt: no open items.\n")
        return EXIT_OK
    sys.stdout.write("voice debt: %d open item(s):\n" % len(items))
    for it in items:
        sys.stdout.write("- %s [%s] %s ch %s line %s: %s\n"
                         % (it.get("id"), it.get("status"), it.get("type"),
                            it.get("chapter"), it.get("line"), it.get("match")))
    return EXIT_OK


def debt_clear(root, target):
    doc, p = _load_debt(root)
    items = doc.get("items", [])
    if target == "all":
        cleared = sum(1 for it in items if it.get("status") == "open")
        for it in items:
            if it.get("status") == "open":
                it["status"] = "cleared"
                it["cleared_at"] = date.today().isoformat()
    else:
        cleared = 0
        found = False
        for it in items:
            if it.get("id") == target:
                found = True
                if it.get("status") == "open":
                    it["status"] = "cleared"
                    it["cleared_at"] = date.today().isoformat()
                    cleared += 1
        if not found:
            util.die("voice-debt id %r not found (see 'vellum debt list')."
                     % target)
    util.atomic_write(p, json.dumps(doc, indent=2, ensure_ascii=False) + "\n")
    sys.stdout.write("voice debt: cleared %d item(s).\n" % cleared)
    return EXIT_OK
