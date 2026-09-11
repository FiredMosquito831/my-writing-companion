# Vellum deterministic engine package (design-spec.md section 5).
# Original code (base design credited in ATTRIBUTION.md).
# Python >= 3.8, stdlib only, zero pip dependencies.
"""vellum_lib — the deterministic engine package.

Modules (spec 5.1/5.2):
- util        paths, atomic writes, lockfile, hash verification, yaml-lite
              frontmatter parser, word rule, exemptions, findings
- state       state rebuild / state check
- ledgers     ledger check (deterministic continuity catalog)
- bible       bible validate / reindex / links
- wordcount   wordcount [--write] + band check
- knowledge   knowledge <character> --as-of N [--audience]
- style_stats style stats [--baseline] (single metrics module)
- pack        pack chapter-NN (deterministic writer context pack)
- exemptions  dismiss / debt list|clear
- export      readiness / export build [--epub]
- cli         argparse dispatch
"""

__version__ = "0.2.0"


# ---------------------------------------------------------------------------
# UTF-8 stdout/stderr (library-spec.md 8 amendment)
# ---------------------------------------------------------------------------

def _force_utf8_streams():
    """Reconfigure stdout/stderr to UTF-8 once at engine import.

    On Windows the default piped-stdout encoding is the ANSI codepage
    (cp1252 on most installs), so engine output containing em dashes or
    Romanian diacritics would reach downstream consumers as cp1252 bytes
    and break any consumer that decodes the pipe as UTF-8. All engine
    stdout/stderr is UTF-8 regardless of platform codepage; downstream
    consumers decode as UTF-8 unconditionally. Fail-safe: a closed or
    non-reconfigurable stream (e.g. a test-capture shim) is left alone.
    """
    import sys as _sys
    for _s in (_sys.stdout, _sys.stderr):
        try:
            if hasattr(_s, "reconfigure"):
                _s.reconfigure(encoding="utf-8")
        except (ValueError, OSError):
            pass


_force_utf8_streams()
