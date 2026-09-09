# Vellum deterministic engine — knowledge queries (spec 5.2).
# Original code (base design credited in ATTRIBUTION.md).
"""Queryable knowledge backend: `knowledge <character-id> --as-of N` prints
the facts the character holds as of chapter N with certainty levels;
`--audience` adds the audience-knowledge view for dramatic-irony checks."""
import sys

from . import util
from .util import EXIT_OK, EXIT_ERROR, chapter_num_val


def _load(root):
    try:
        return util.load_entity_dir(root, "knowledge")
    except util.FmError as e:
        util.die(str(e))


def run(root, character_id, as_of, audience=False):
    entries = _load(root)
    known = []       # (id, title, statement, certainty, learned_in)
    audience_knows = []  # (id, title, statement, audience_learned_in)
    for k in entries:
        fm = k["fm"]
        kid = fm.get("id", k["name"][:-3])
        title = fm.get("title", kid)
        statement = fm.get("statement", "")
        if audience:
            al = chapter_num_val(fm.get("audience-learned-in"))
            if al is not None and as_of is not None and al <= as_of:
                audience_knows.append((kid, title, statement, al))
        holders = fm.get("holders")
        if not isinstance(holders, list):
            continue
        for h in holders:
            if not isinstance(h, dict):
                continue
            if h.get("character") != character_id:
                continue
            learned = chapter_num_val(h.get("learned-in"))
            if learned is None or as_of is None:
                continue
            if learned <= as_of:
                known.append((kid, title, statement,
                              h.get("certainty", "?"), learned))

    if not known and not audience_knows:
        sys.stdout.write("no matching knowledge for %s as of chapter %s.\n"
                         % (character_id, as_of))
        return EXIT_OK

    sys.stdout.write("knowledge held by %s as of chapter %s:\n"
                     % (character_id, as_of))
    if known:
        for kid, title, statement, cert, learned in sorted(known, key=lambda x: x[4]):
            sys.stdout.write("- [%s] %s (%s, learned chapter %d): %s\n"
                             % (cert, title, kid, learned, statement))
    else:
        sys.stdout.write("- (nothing)\n")

    if audience:
        # dramatic-irony view: what the READER knows that the character
        # does not (or holds only at half-glimpse).
        held = {k[0]: k[3] for k in known}
        irony = [a for a in audience_knows
                 if a[0] not in held or held[a[0]] != "knows"]
        sys.stdout.write("audience knows as of chapter %s "
                         "(dramatic-irony view):\n" % as_of)
        if irony:
            for kid, title, statement, al in sorted(irony, key=lambda x: x[3]):
                held_note = ""
                if kid in held:
                    held_note = " (character holds only: %s)" % held[kid]
                else:
                    held_note = " (character does not know)"
                sys.stdout.write("- %s (%s, audience learned chapter %d): "
                                 "%s%s\n" % (title, kid, al, statement, held_note))
        else:
            sys.stdout.write("- (nothing beyond the character)\n")
    return EXIT_OK
