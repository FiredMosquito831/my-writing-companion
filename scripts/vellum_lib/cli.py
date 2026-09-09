# Vellum deterministic engine — argparse dispatch (spec 5.2).
# Original code (base design credited in ATTRIBUTION.md).
"""CLI over the frozen spec-5.2 subcommand table. Exit codes:
0 clean · 1 findings · 2 schema/usage error."""
import argparse
import os
import sys

from . import util
from .util import EXIT_OK, EXIT_ERROR, FmError, LockError


def _root(_args):
    return util.find_project_root()


def build_parser():
    from . import __version__
    p = argparse.ArgumentParser(
        prog="vellum",
        description="Vellum deterministic engine (stdlib Python >= 3.8). "
                    "Run from the project root; exit codes: 0 clean, "
                    "1 findings, 2 schema/usage error.")
    p.add_argument("--version", action="version",
                   version="vellum engine %s" % __version__)
    sub = p.add_subparsers(dest="group")

    # state rebuild | state check
    state = sub.add_parser("state", help="state rebuild / state check")
    ssub = state.add_subparsers(dest="action")
    ssub.add_parser("rebuild", help="regenerate _tracking-state.json + "
                                    "state-card.md + derived hashes")
    ssub.add_parser("check", help="transactional invariants (gate-1 "
                                  "precondition)")
    ssub_check = ssub.choices["check"]
    ssub_check.add_argument("target", nargs="?", default=None,
                            help="optional path of the chapter file the "
                                 "calling guard is writing; edits to an "
                                 "existing chapter are that chapter's own "
                                 "transaction, not a new-chapter start")

    # ledger check
    ledger = sub.add_parser("ledger", help="deterministic continuity checks")
    lsub = ledger.add_subparsers(dest="action")
    lsub.add_parser("check", help="run the ledger check catalog")

    # bible validate | reindex | links
    bible = sub.add_parser("bible", help="kb schema + registry tools")
    bsub = bible.add_subparsers(dest="action")
    bsub.add_parser("validate", help="frontmatter schema validation + "
                                     "cross-reference integrity")
    bsub.add_parser("reindex", help="rebuild _index.md registries; repair "
                                    "derived files")
    bsub.add_parser("links", help="cross-reference integrity only")

    # wordcount [--write] [chapters...]
    wc = sub.add_parser("wordcount", help="words per chapter; band check")
    wc.add_argument("--write", action="store_true",
                    help="update the word-count frontmatter field")
    wc.add_argument("chapters", nargs="*",
                    help="chapter file paths or names (default: all)")

    # knowledge <character> --as-of N [--audience]
    kn = sub.add_parser("knowledge", help="query who knows what, as of a chapter")
    kn.add_argument("character", help="character id")
    kn.add_argument("--as-of", dest="as_of", type=int, required=True,
                    metavar="N", help="chapter number")
    kn.add_argument("--audience", action="store_true",
                    help="audience-knowledge view (dramatic irony)")

    # style stats <file|glob> [--baseline]
    st = sub.add_parser("style", help="style metrics")
    sts = st.add_subparsers(dest="action")
    stats = sts.add_parser("stats", help="sentence stats + per-1k voice profile")
    stats.add_argument("pattern", help="file or glob (e.g. "
                                       "'manuscript/chapters/chapter-*.md')")
    stats.add_argument("--baseline", action="store_true",
                       help="diff against kb/styles/baseline.md")

    # pack chapter-NN
    pack = sub.add_parser("pack", help="deterministic writer context pack")
    pack.add_argument("chapter", help="chapter id (chapter-NN)")

    # dismiss <key> --reason "..." [--chapter chapter-NN]
    dis = sub.add_parser("dismiss", help="record an author dismissal")
    dis.add_argument("key", help="<category>:<entity_id>")
    dis.add_argument("--reason", required=True,
                     help="the author's words, verbatim")
    dis.add_argument("--chapter", default=None,
                     help="optional chapter context of the dismissal "
                          "(recorded as metadata; never part of the key)")

    # debt list | debt clear <id|all>
    debt = sub.add_parser("debt", help="voice-debt accounting")
    dsub = debt.add_subparsers(dest="action")
    dsub.add_parser("list", help="list open voice-debt items")
    dclear = dsub.add_parser("clear", help="clear a voice-debt item")
    dclear.add_argument("target", help="item id or 'all'")

    # readiness
    sub.add_parser("readiness", help="evaluate the section-10 preconditions")

    # export build --out DIR [--epub]
    exp = sub.add_parser("export", help="export tools")
    esub = exp.add_subparsers(dest="action")
    build = esub.add_parser("build", help="assemble the export bundle")
    build.add_argument("--out", required=True, help="output directory")
    build.add_argument("--epub", action="store_true",
                       help="also build a stdlib-zipfile EPUB")

    return p


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    if not getattr(args, "group", None):
        parser.print_help()
        return EXIT_ERROR

    root = util.find_project_root()
    try:
        if args.group == "state":
            from . import state as mod
            if args.action == "rebuild":
                return mod.rebuild(root)
            if args.action == "check":
                return mod.check(root, target=getattr(args, "target", None))
        elif args.group == "ledger":
            if args.action == "check":
                from . import ledgers as mod
                return mod.check(root)
        elif args.group == "bible":
            from . import bible as mod
            if args.action == "validate":
                return mod.validate(root)
            if args.action == "reindex":
                return mod.reindex(root)
            if args.action == "links":
                return mod.links(root)
        elif args.group == "wordcount":
            from . import wordcount as mod
            return mod.run(root, write=args.write,
                           chapter_paths=list(args.chapters) or None)
        elif args.group == "knowledge":
            from . import knowledge as mod
            return mod.run(root, args.character, args.as_of,
                           audience=args.audience)
        elif args.group == "style":
            if args.action == "stats":
                from . import style_stats as mod
                return mod.run(root, args.pattern, baseline=args.baseline)
        elif args.group == "pack":
            from . import pack as mod
            return mod.run(root, args.chapter)
        elif args.group == "dismiss":
            from . import exemptions as mod
            return mod.dismiss(root, args.key, args.reason,
                               chapter=args.chapter)
        elif args.group == "debt":
            from . import exemptions as mod
            if args.action == "list":
                return mod.debt_list(root)
            if args.action == "clear":
                return mod.debt_clear(root, args.target)
        elif args.group == "readiness":
            from . import export as mod
            return mod.readiness(root)
        elif args.group == "export":
            if args.action == "build":
                from . import export as mod
                return mod.build(root, args.out, epub=args.epub)
    except FmError as e:
        sys.stderr.write("vellum: %s\n" % e)
        return EXIT_ERROR
    except LockError as e:
        sys.stderr.write("vellum: %s\n" % e)
        return EXIT_ERROR

    parser.print_help()
    return EXIT_ERROR
