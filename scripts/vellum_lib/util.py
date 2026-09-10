# Vellum deterministic engine — shared utilities (spec 5.1).
# Original code (base design credited in ATTRIBUTION.md).
# Python >= 3.8, stdlib only, zero pip dependencies.
"""Global engine rules: paths, atomic writes, lockfile, hash verification,
yaml-lite frontmatter parsing, the word rule, exemption loading, and the
shared finding schema with exit codes (0 clean / 1 findings / 2 error)."""

import hashlib
import json
import os
import re
import sys
import time

EXIT_OK = 0
EXIT_FINDINGS = 1
EXIT_ERROR = 2

SCHEMA_VERSION = 1
STATE_CARD_MAX_BYTES = 12 * 1024  # hard cap (spec 7.4)

FINDING_SCHEMA_VERSION = 1


class FmError(Exception):
    """Unparseable frontmatter — fail loudly with file + line (spec 5.1)."""


class LockError(Exception):
    """State lock held by another process."""


# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

def find_project_root():
    """Walk up from cwd looking for a vellum project marker."""
    d = os.getcwd()
    while True:
        for marker in ("kb", "manuscript", "state"):
            if os.path.isdir(os.path.join(d, marker)):
                return d
        parent = os.path.dirname(d)
        if parent == d:
            return os.getcwd()
        d = parent


def project_file(root, *parts):
    return os.path.join(root, *parts)


# ---------------------------------------------------------------------------
# Atomic writes + lockfile (spec 5.1)
# ---------------------------------------------------------------------------

def atomic_write(path, content):
    """Write <file>.tmp-<pid> then os.replace()."""
    d = os.path.dirname(path)
    if d and not os.path.isdir(d):
        os.makedirs(d, exist_ok=True)
    tmp = "%s.tmp-%d" % (path, os.getpid())
    with open(tmp, "w", encoding="utf-8", newline="\n") as f:
        f.write(content)
    os.replace(tmp, path)


_LOCK_STALE_SECONDS = 60


def lock_state(root):
    """Exclusive lock via state/.vellum.lock (O_CREAT|O_EXCL).

    Stale lock (> 60 s) -> warn + proceed. Contention -> LockError (exit 2).
    Returns a release() callable (idempotent).
    """
    lock_path = project_file(root, "state", ".vellum.lock")
    os.makedirs(os.path.dirname(lock_path), exist_ok=True)
    while True:
        try:
            fd = os.open(lock_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            os.write(fd, str(os.getpid()).encode("ascii"))
            os.close(fd)
            break
        except FileExistsError:
            try:
                age = time.time() - os.path.getmtime(lock_path)
            except OSError:
                age = 0
            if age > _LOCK_STALE_SECONDS:
                sys.stderr.write(
                    "vellum: stale state lock (held %.0fs, older than %ds) - "
                    "proceeding.\n" % (age, _LOCK_STALE_SECONDS))
                try:
                    os.unlink(lock_path)
                except OSError:
                    pass
                continue  # retry the exclusive create
            raise LockError(
                "state is locked by another vellum process (state/.vellum.lock); "
                "wait for it to finish or remove the stale lock file.")
    def release():
        try:
            os.unlink(lock_path)
        except OSError:
            pass
    return release


# ---------------------------------------------------------------------------
# Hash-verified derived files (spec 5.1)
# ---------------------------------------------------------------------------

DERIVED_FILES = ("state/_tracking-state.json", "state/state-card.md")


def _hashes_path(root):
    return project_file(root, "state", "_derived-hashes.json")


def sha256_bytes(data):
    return hashlib.sha256(data.encode("utf-8")).hexdigest()


def write_derived_hashes(root):
    """Record sha256 of the last engine-written content for each derived file."""
    mapping = {}
    for rel in DERIVED_FILES:
        p = project_file(root, *rel.split("/"))
        if os.path.exists(p):
            with open(p, "rb") as f:
                mapping[rel] = hashlib.sha256(f.read()).hexdigest()
    atomic_write(_hashes_path(root),
                 json.dumps({"schema_version": SCHEMA_VERSION,
                             "hashes": mapping}, indent=2, sort_keys=True) + "\n")


def hash_mismatches(root):
    """Return list of derived files whose current content != recorded hash."""
    hp = _hashes_path(root)
    if not os.path.exists(hp):
        return list(DERIVED_FILES)
    try:
        with open(hp, "r", encoding="utf-8") as f:
            doc = json.load(f)
    except Exception:
        return list(DERIVED_FILES)
    recorded = doc.get("hashes", {})
    out = []
    for rel in DERIVED_FILES:
        p = project_file(root, *rel.split("/"))
        if not os.path.exists(p):
            continue
        with open(p, "rb") as f:
            cur = hashlib.sha256(f.read()).hexdigest()
        if cur != recorded.get(rel):
            out.append(rel)
    return out


# ---------------------------------------------------------------------------
# yaml-lite frontmatter parser (spec 5.1)
# ---------------------------------------------------------------------------

def _strip_comment(val):
    """Strip a trailing `# comment` outside of quotes."""
    in_s = in_d = False
    for i, ch in enumerate(val):
        if ch == "'" and not in_d:
            in_s = not in_s
        elif ch == '"' and not in_s:
            in_d = not in_d
        elif ch == "#" and not in_s and not in_d:
            return val[:i].rstrip()
    return val.rstrip()


def _unquote(val):
    if len(val) >= 2 and val[0] == val[-1] and val[0] in ("'", '"'):
        return val[1:-1]
    return val


def _scalar(val):
    val = _unquote(val)
    low = val.lower()
    if low in ("null", "~", ""):
        return None
    if low == "true":
        return True
    if low == "false":
        return False
    try:
        return int(val)
    except ValueError:
        pass
    try:
        return float(val)
    except ValueError:
        pass
    return val


def _flow_list(val):
    """Parse `[a, b, c]` (flow style). Items may be quoted."""
    inner = val[1:-1].strip()
    if not inner:
        return []
    items, cur, in_s, in_d = [], "", False, False
    for ch in inner:
        if ch == "'" and not in_d:
            in_s = not in_s
            cur += ch
        elif ch == '"' and not in_s:
            in_d = not in_d
            cur += ch
        elif ch == "," and not in_s and not in_d:
            items.append(cur)
            cur = ""
        else:
            cur += ch
    items.append(cur)
    return [_scalar(_strip_comment(it.strip())) for it in items if it.strip()]


def parse_frontmatter(text, path="<text>"):
    """Parse the yaml-lite frontmatter subset (spec 5.1).

    Returns (fm_dict, body_text, body_start_line). Raises FmError with
    file + line on unparseable frontmatter. Supported: key: value scalars,
    inline flow lists `[...]`, block lists via `- `, block lists of maps
    (`- character: x` + continuation keys), inline flow maps `{a: 1}`,
    and single-level nested maps (`holders:`, `custody:`, `axes:`, ...).
    """
    lines = text.split("\n")
    if not lines or not re.match(r"^---\s*$", lines[0].rstrip("\r")):
        return {}, text, 1
    fm = {}
    n = len(lines)
    last_key = None          # current top-level key
    list_map = None          # dict under construction in a block list of maps
    list_map_indent = -1     # indent of the `- ` line that opened list_map

    def _close_list_map():
        nonlocal list_map, list_map_indent
        if list_map is not None and last_key is not None:
            if not isinstance(fm.get(last_key), list):
                fm[last_key] = []
            fm[last_key].append(list_map)
        list_map = None
        list_map_indent = -1

    i = 1
    while i < n:
        raw = lines[i].rstrip("\r")
        if re.match(r"^---\s*$", raw):
            _close_list_map()
            body = "\n".join(lines[i + 1:])
            return fm, body, i + 2  # body starts after the closing ---
        if not raw.strip() or raw.lstrip().startswith("#"):
            i += 1
            continue
        indent = len(raw) - len(raw.lstrip(" "))
        stripped = raw.strip()

        if indent == 0:
            _close_list_map()
            m = re.match(r"^([A-Za-z0-9_-]+)\s*:\s*(.*)$", stripped)
            if not m:
                raise FmError("%s: line %d: unparseable frontmatter line: %r"
                              % (path, i + 1, stripped))
            key, val = m.group(1), m.group(2)
            val = _strip_comment(val).strip()
            if val.startswith("[") and val.endswith("]"):
                fm[key] = _flow_list(val)
            elif val.startswith("{") and val.endswith("}"):
                entry = {}
                for part in _split_flow_map(val[1:-1]):
                    k, _, v = part.partition(":")
                    entry[k.strip()] = _scalar(_strip_comment(v.strip()))
                fm[key] = entry
            elif val == "":
                fm[key] = None  # may become a nested map or block list
                last_key = key
            else:
                fm[key] = _scalar(val)
                last_key = key
        elif stripped.startswith("- ") or stripped == "-":
            # block list item (possibly a map opening)
            if last_key is None:
                raise FmError("%s: line %d: list item outside a key: %r"
                              % (path, i + 1, stripped))
            if list_map is not None:
                _close_list_map()
            item = stripped[2:].strip() if stripped != "-" else ""
            km = re.match(r"^([A-Za-z0-9_-]+)\s*:\s*(.*)$", item) if item else None
            if km:
                # a map item with continuation lines expected
                list_map = {km.group(1): _scalar(_strip_comment(km.group(2)).strip())}
                list_map_indent = indent
                if fm.get(last_key) is None:
                    fm[last_key] = []
            elif item:
                item_val = _scalar(_strip_comment(item))
                cur = fm.get(last_key)
                if isinstance(cur, list):
                    cur.append(item_val)
                elif cur is None:
                    fm[last_key] = [item_val]
                else:
                    raise FmError(
                        "%s: line %d: cannot mix list and scalar under %r"
                        % (path, i + 1, last_key))
            else:
                if fm.get(last_key) is None:
                    fm[last_key] = []
        else:
            # indented continuation: either a block-map key or a list-map key
            if list_map is not None and indent > list_map_indent:
                m = re.match(r"^([A-Za-z0-9_-]+)\s*:\s*(.*)$", stripped)
                if not m:
                    raise FmError("%s: line %d: unparseable frontmatter "
                                  "line: %r" % (path, i + 1, stripped))
                list_map[m.group(1)] = _scalar(_strip_comment(m.group(2)).strip())
            else:
                m = re.match(r"^([A-Za-z0-9_-]+)\s*:\s*(.*)$", stripped)
                if m is None or last_key is None:
                    raise FmError("%s: line %d: unparseable frontmatter "
                                  "line: %r" % (path, i + 1, stripped))
                if not isinstance(fm.get(last_key), dict):
                    if fm.get(last_key) is None:
                        fm[last_key] = {}
                    else:
                        raise FmError(
                            "%s: line %d: nested map under scalar key %r"
                            % (path, i + 1, last_key))
                k, v = m.group(1), _strip_comment(m.group(2)).strip()
                fm[last_key][k] = _scalar(v)
        i += 1
    _close_list_map()
    raise FmError("%s: unclosed frontmatter (no closing ---)" % path)


def _split_flow_map(inner):
    parts, cur, depth = [], "", 0
    for ch in inner:
        if ch in "'\"":
            cur += ch
        elif ch == "," and depth == 0:
            parts.append(cur)
            cur = ""
        else:
            cur += ch
    if cur.strip():
        parts.append(cur)
    return parts


def strip_frontmatter_text(text):
    """Return (fm, body) ignoring parse errors (empty fm on failure)."""
    try:
        fm, body, _ = parse_frontmatter(text)
        return fm, body
    except FmError:
        return {}, text


def read_file(path):
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        return f.read()


# ---------------------------------------------------------------------------
# The word rule (spec 5.1, verbatim semantics from story-skills schema-v2, MIT)
# ---------------------------------------------------------------------------

_WORD_RE = re.compile(r"[^\W_]+(?:['’-][^\W_]+)*", re.UNICODE)


def count_words(text):
    """A word is a run of letters/digits in any script; apostrophes and
    hyphens join (don't -> one word, mother-in-law -> one word)."""
    return len(_WORD_RE.findall(text))


# ---------------------------------------------------------------------------
# Chapters
# ---------------------------------------------------------------------------

def chapter_num_from_name(name):
    m = re.match(r"^chapter-0*(\d+)\.md$", name, re.IGNORECASE)
    return int(m.group(1)) if m else None


def list_chapters(root):
    """All manuscript chapters as dicts, ordered by frontmatter number
    (filename order as fallback). Never includes non-chapter files."""
    chdir = project_file(root, "manuscript", "chapters")
    out = []
    if not os.path.isdir(chdir):
        return out
    for name in sorted(os.listdir(chdir)):
        if not re.match(r"^chapter-\d+\.md$", name, re.IGNORECASE):
            continue
        path = os.path.join(chdir, name)
        num = chapter_num_from_name(name)
        fm, body = strip_frontmatter_text(read_file(path))
        out.append({
            "file": "manuscript/chapters/" + name,
            "path": path,
            "name": name,
            "num": num if num is not None else 0,
            "fm": fm,
            "body": body,
            "words": count_words(body),
        })
    out.sort(key=lambda c: (c["fm"].get("number") if isinstance(c["fm"].get("number"), int) else c["num"], c["num"]))
    return out


def outline_files(root):
    """work/outline/chapter-*.md files keyed by chapter number."""
    odir = project_file(root, "work", "outline")
    out = {}
    if not os.path.isdir(odir):
        return out
    for name in sorted(os.listdir(odir)):
        num = chapter_num_from_name(name)
        if num is None:
            continue
        path = os.path.join(odir, name)
        fm, body = strip_frontmatter_text(read_file(path))
        out[num] = {"file": "work/outline/" + name, "path": path,
                    "fm": fm, "body": body}
    return out


# ---------------------------------------------------------------------------
# Exemptions (spec 5.1, 7.3)
# ---------------------------------------------------------------------------

def exemptions_path(root):
    return project_file(root, "kb", "exemptions.json")


def load_exemptions(root):
    p = exemptions_path(root)
    if not os.path.exists(p):
        return {"schema_version": 1, "exemptions": []}
    try:
        with open(p, "r", encoding="utf-8") as f:
            doc = json.load(f)
    except Exception:
        return {"schema_version": 1, "exemptions": []}
    if not isinstance(doc.get("exemptions"), list):
        doc["exemptions"] = []
    return doc


def filter_findings(findings, exemptions):
    """Drop findings whose key matches an active exemption; stale entries
    re-arm once: the finding is kept with a re-arm note (spec 5.1, 7.3)."""
    active = set()
    stale = {}
    for e in exemptions.get("exemptions", []):
        key = e.get("key")
        if not key:
            continue
        if e.get("status") == "active":
            active.add(key)
        elif e.get("status") == "stale":
            stale[key] = e
    out = []
    for f in findings:
        key = f.get("key")
        if key in active:
            continue
        if key in stale:
            f = dict(f)
            f["issue"] = f.get("issue", "") + (
                " (previously dismissed; underlying fact changed on %s - re-armed once)"
                % stale[key].get("dismissed_at", "unknown"))
        out.append(f)
    return out


# ---------------------------------------------------------------------------
# Findings (shared schema, spec 3.6)
# ---------------------------------------------------------------------------

_SEVERITIES = ("note", "suggestion", "warning", "blocker")


def make_finding(technique, severity, file, line, quote, issue, key=None,
                 confidence="deterministic", audit="continuity"):
    return {
        "audit": audit,
        "technique": technique,
        "severity": severity,
        "location": {"file": file, "line": line, "quote": quote},
        "issue": issue,
        "confidence": confidence,
        "key": key or ("%s:%s" % (audit, technique)),
    }


def emit_findings(findings):
    """Print findings as JSON lines in the shared schema (spec 3.6)."""
    for f in findings:
        sys.stdout.write(json.dumps(f, ensure_ascii=False) + "\n")


def findings_report(findings):
    """Human one-line form used by hooks/CLI summaries."""
    lines = []
    for f in findings:
        loc = f.get("location") or {}
        where = loc.get("file") or ""
        if loc.get("line"):
            where += ":%d" % loc["line"]
        lines.append("[%s] %s %s - %s" % (f.get("severity", "note"),
                                          where, f.get("technique", ""),
                                          f.get("issue", "")))
    return lines


# ---------------------------------------------------------------------------
# Config (spec 3.8)
# ---------------------------------------------------------------------------

def load_config(root):
    cfg = {
        "drift_interval": 5,
        "voice_debt_gate": False,
        "stop_gate": False,
        "blind_gate_fallback": False,
        "default_word_target": 3200,
        "word_band": 0.15,
    }
    p = project_file(root, "kb", "project-config.json")
    if os.path.exists(p):
        try:
            with open(p, "r", encoding="utf-8") as f:
                doc = json.load(f)
            if isinstance(doc, dict):
                cfg.update({k: v for k, v in doc.items() if k in cfg})
        except Exception:
            pass
    return cfg


def load_story(root):
    """kb/story.md frontmatter (premise/uuid/title), or {} when absent."""
    p = project_file(root, "kb", "story.md")
    if not os.path.exists(p):
        return {}
    fm, _ = strip_frontmatter_text(read_file(p))
    return fm


def die(msg, code=EXIT_ERROR):
    sys.stderr.write("vellum: %s\n" % msg)
    sys.exit(code)


def load_entity_dir(root, kind):
    """Read every kb/<kind>/*.md; returns list of {file, path, name, fm, body}.
    Raises FmError on unparseable frontmatter (fail loudly)."""
    d = project_file(root, "kb", kind)
    out = []
    if not os.path.isdir(d):
        return out
    for name in sorted(os.listdir(d)):
        if not name.endswith(".md") or name == "_index.md":
            continue
        path = os.path.join(d, name)
        fm, body, _ = parse_frontmatter(read_file(path), path)
        out.append({"file": "kb/%s/%s" % (kind, name), "path": path,
                    "name": name, "fm": fm, "body": body})
    return out


def entity_status_map(entities):
    return {e["fm"].get("id", e["name"][:-3]): e for e in entities}


def chapter_num_val(v):
    """chapter-NN | NN | int -> int | None."""
    if isinstance(v, int):
        return v
    if isinstance(v, str):
        m = re.match(r"^chapter-0*(\d+)$", v.strip(), re.IGNORECASE)
        if m:
            return int(m.group(1))
        m = re.match(r"^0*(\d+)$", v.strip())
        if m:
            return int(m.group(1))
    if isinstance(v, float) and v == int(v):
        return int(v)
    return None
