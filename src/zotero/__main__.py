#!/usr/bin/env python
from tinyscript import *

from .__info__ import __author__, __email__, __source__, __version__
from .__init__ import *


__copyright__ = ("A. D'Hondt", 2020)
__license__   = "gpl-3.0"
__script__    = "zotero-cli"
__doc__       = """
This tool aims to inspect, filter, sort and export Zotero references.

It works by downloading the whole list of items to perform computations locally. It also uses a modified page rank to
sort references to help selecting the most relevant ones.
"""
__examples__  = [
    "count -f \"collections:biblio\" -f \"rank:>1.0\"",
    "export year title itemType numAuthors numPages zscc references what results comments -f \"collections:biblio\" " \
        "-s date -l \">rank:50\"",
    "list attachments",
    "list collections",
    "list citations --desc -f \"citations:>10\"",
    "show title DOI",
    "show title date zscc -s date -l '>zscc:10'",
]


def _set_arg(subparser, arg, msg=None):
    """ Shortcut function to set arguments repeated for multiple subparsers. """
    if arg == "filter":
        subparser.add_argument("-f", "--filter", action="extend", nargs="*", default=[], note="format: [field]:[regex]",
                               help=msg or "filter to be applied on field's value")
    elif arg == "limit":
        subparser.add_argument("-l", "--limit", help="limit the number of displayed records", note="format: either a "
                               "number or [field]:[number]\n    '<' and '>' respectively indicates ascending or "
                               "descending order (default: ascending)")
    elif arg == "query":
        subparser.add_argument("-q", "--query", choices=list(QUERIES.keys()), help="use a predefined query",
                               note="this can be combined with additional filters")
    elif arg == "sort":
        subparser.add_argument("-s", "--sort", help="field to be sorted on", note="if not defined, the first input "
                               "field is selected\n    '<' and '>' respectively indicates ascending or descending order"
                               " (default: ascending)")
_set_args = lambda sp, *args: [_set_arg(sp, a) for a in args] and None


def main():
    """ Tool's main function """
    # main parser
    parser.add_argument("-g", "--group", action="store_true", help="API identifier is a group",
                        note="the default API identifier type is 'user' ; use this option if you modified your library "
                             "to be shared with a group of users, this can be set permanently by touching %s" % 
                             GROUP_FILE)
    parser.add_argument("-i", "--id", help="API identifier",
                        note="if 'id' and 'key' not specified, credentials are obtained from file %s" % CREDS_FILE)
    parser.add_argument("-k", "--key", help="API key",
                        note="if not specified while 'id' is, 'key' is asked as a password")
    parser.add_argument("-r", "--reset", action="store_true", help="remove cached collections and items")
    # commands: count | export | list | plot | reset | show | view
    sparsers = parser.add_subparsers(dest="command", help="command to be executed")
    ccount = sparsers.add_parser("count", help="count items")
    _set_arg(ccount, "filter", "filter to be applied while counting")
    _set_arg(ccount, "query")
    cexpt = sparsers.add_parser("export", help="export items to a file")
    cexpt.add_argument("field", nargs="+", help="field to be shown")
    cexpt.add_argument("-l", "--line-format", help="line's format string for outputting as a list")
    cexpt.add_argument("-o", "--output-format", default="xlsx", help="output format",
                       choices=["csv", "html", "json", "md", "pdf", "rst", "xml", "xlsx", "yaml"])
    _set_args(cexpt, "filter", "limit", "query", "sort")
    clist = sparsers.add_parser("list", help="list distinct values for the given field")
    clist.add_argument("field", help="field whose distinct values are to be listed")
    _set_args(clist, "filter", "query")
    clist.add_argument("-l", "--limit", type=ts.pos_int, help="limit the number of displayed records")
    clist.add_argument("--desc", action="store_true", help="sort results in descending order")
    cmark = sparsers.add_parser("mark", help="mark items with a marker")
    cmark.add_argument("marker", choices=[x for p in MARKERS for x in p[:2]], help="marker to be set",
                       note="possible values:\n - {}".format("\n - ".join("%s: %s" % (p[0], p[2]) for p in MARKERS)))
    _set_args(cmark, "filter", "limit", "query", "sort")
    cplot = sparsers.add_parser("plot", help="plot various information using Matplotlib")
    cplot.add_argument("chart", choices=CHARTS, help="chart to be plotted")
    _set_args(cplot, "filter", "query")
    creset = sparsers.add_parser("reset", help="reset cached collections and items")
    creset.add_argument("-r", "--reset-items", action="store_true", help="reset items only")
    cshow = sparsers.add_parser("show", help="show a list of items")
    cshow.add_argument("field", nargs="+", help="field to be shown")
    _set_args(cshow, "filter", "limit", "query", "sort")
    cview = sparsers.add_parser("view", help="view a single item")
    cview.add_argument("name", help="field name for selection")
    cview.add_argument("value", help="field value to be selected")
    cview.add_argument("field", nargs="+", help="field to be shown")
    initialize()
    if getattr(args, "query", None):
        if hasattr(args, "field") and args.field == ["-"]:
            args.field = QUERIES[args.query].get('fields', ["title"])
        args.filter.extend(QUERIES[args.query].get('filter', []))
        if args.limit is None:
            args.limit = QUERIES[args.query].get('limit')
        if args.sort is None:
            args.sort = QUERIES[args.query].get('sort')
    if hasattr(args, "sort"):
        args.desc = False
        if args.sort is not None:
            args.desc = args.sort[0] == ">"
            if args.sort[0] in "<>":
                args.sort = args.sort[1:]
    if args.command == "reset" or args.reset:
        for k in CACHE_FILES:
            if getattr(args, "reset_items", False) and k not in ["items"] + OBJECTS or k == "marks":
                continue
            CACHE_PATH.joinpath(k + ".json").remove(False)
    z = ZoteroCLI(args.id, ["user", "group"][args.group or GROUP_FILE.exists()], args.key, logger)
    if args.command == "count":
        z.count(args.filter)
    elif args.command == "export":
        z.export(args.field, args.filter, args.sort, args.desc, args.limit, args.line_format, args.output_format)
    elif args.command == "list":
        z.list(args.field, args.filter, args.desc, args.limit)
    elif args.command == "mark":
        args.filter.append("numPages:>0")
        z.mark(args.marker, args.filter, args.sort, args.desc, args.limit)
    elif args.command == "plot":
        z.plot(args.chart)
    elif args.command == "show":
        z.show(args.field, args.filter, args.sort, args.desc, args.limit)
    elif args.command == "view":
        z.view(args.name, args.value, args.field)

