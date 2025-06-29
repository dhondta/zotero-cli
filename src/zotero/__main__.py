#!/usr/bin/env python
from tinyscript import *

from .__info__ import __author__, __email__, __source__, __version__
from .__init__ import *
try:
    from .gpt import *
    __GPT = True
except ImportError:
    __GPT = False


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
    "export title date url itemType -f \"collections:doc\" -s \"title\" -l \"{emoji} {link_lower}\" -o md --check-url",
    "export year title itemType numAuthors numPages zscc references what results comments -f \"collections:biblio\" " \
        "-s date -l \">rank:50\"",
    "list attachments",
    "list collections",
    "list citations --desc -f \"citations:>10\"",
    "show title DOI",
    "show title date zscc -s date -l '>zscc:10'",
]


def _domains(url_no_check):
    r = []
    for url in (url_no_check or []):
        if ts.is_file(url):
            with open(url) as f:
                for l in f:
                    r.append(l.strip())
        else:
            r.append(url.strip())
    return r


def _set_arg(subparser, arg, msg=None):
    """ Shortcut function to set arguments repeated for multiple subparsers. """
    if arg == "filter":
        subparser.add_argument("-f", "--filter", action="extend", dest="filters", nargs="*", default=[],
                               note="format: [field]:[regex]", help=msg or "filter to be applied on field's value")
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
    parser.add_argument("--creds-file", default=CREDS_FILE, type=ts.CredentialsPath, help="credentials file to load")
    parser.add_argument("-g", "--group", action="store_true", help="set the API identifier as a group",
                        note="the default API identifier type is 'user' ; use this option if you modified your library "
                            f"to be shared with a group of users, this can be set permanently by touching {GROUP_FILE}")
    parser.add_argument("-i", "--id", help="API identifier",
                        note="if 'id' and 'key' not specified, credentials are obtained from a file (by default: "
                            f"{CREDS_FILE})")
    parser.add_argument("-k", "--key", help="API key",
                        note="if not specified while 'id' is, 'key' is asked as a password")
    parser.add_argument("-r", "--reset", action="store_true", help="remove cached collections and items")
    # commands: count | export | list | plot | reset | show | view
    sparsers = parser.add_subparsers(dest="command", help="command to be executed")
    kw1, kw2 = {}, {}
    if __GPT:
        kw1, kw2 = {'category': "main"}, {'category': "GPT"}
        cask = sparsers.add_parser("ask", help="ask questions to your Zotero documents", category="GPT")
        cask.add_argument("name", default=MODEL_DEFAULT_NAME, choices=MODELS, nargs="?", help="model name")
        cask.add_argument("-c", "--show-content", action="store_true", help="show content from source documents")
        cask.add_argument("-m", "--mute-stream", action="store_true", help="disable streaming StdOut callback for LLMs")
        cask.add_argument("-s", "--show-source", action="store_true", help="show source documents")
    ccount = sparsers.add_parser("count", help="count items", category="read")
    _set_arg(ccount, "filter", "filter to be applied while counting")
    _set_arg(ccount, "query")
    cexpt = sparsers.add_parser("export", help="export items to a file", category="read")
    cexpt.add_argument("fields", nargs="+", help="field to be shown")
    cexpt.add_argument("-l", "--line-format", help="line's format string for outputting as a list")
    cexpt.add_argument("-o", "--output-format", default="xlsx", help="output format",
                       choices=["csv", "html", "json", "md", "pdf", "rst", "xml", "xlsx", "yaml"])
    cexpt.add_argument("-u", "--check-url", action="store_true", help="check for broken URL's")
    cexpt.add_argument("--url-no-check", nargs="*", help="either a domain or a file with one domain per line for "
                                                         "skipping URL check")
    _set_args(cexpt, "filter", "limit", "query", "sort")
    if __GPT:
        cingest = sparsers.add_parser("ingest", help="ingest Zotero documents", category="GPT")
        cinst = sparsers.add_parser("install", help="install a GPT model", category="GPT")
        cinst.add_argument("name", default=MODEL_DEFAULT_NAME, choices=MODEL_NAMES, nargs="?", help="model name")
        cinst.add_argument("-d", "--download", action="store_true", help="download the input model")
    clist = sparsers.add_parser("list", help="list distinct values for the given field", category="read")
    clist.add_argument("field", help="field whose distinct values are to be listed")
    _set_args(clist, "filter")
    clist.add_argument("-l", "--limit", type=ts.pos_int, help="limit the number of displayed records")
    clist.add_argument("--desc", action="store_true", help="sort results in descending order")
    cmark = sparsers.add_parser("mark", help="mark items with a marker", category="manage")
    cmark.add_argument("marker", choices=[x for p in MARKERS for x in p[:2]], help="marker to be set",
                       note="possible values:\n - {}".format("\n - ".join(f"{p[0]}: {p[2]}" for p in MARKERS)))
    _set_args(cmark, "filter", "limit", "query", "sort")
    cplot = sparsers.add_parser("plot", help="plot various information using Matplotlib", category="read")
    cplot.add_argument("chart", choices=CHARTS, help="chart to be plotted")
    _set_args(cplot, "filter", "query")
    creset = sparsers.add_parser("reset", help="reset cached collections and items", category="manage")
    creset.add_argument("-r", "--reset-items", action="store_true", help="reset items only")
    if __GPT:
        cselect = sparsers.add_parser("select", help="select a GPT model", category="GPT")
        cselect.add_argument("name", default=MODEL_DEFAULT_NAME, choices=MODELS, nargs="?", help="model name")
    cshow = sparsers.add_parser("show", help="show a list of items", category="read")
    cshow.add_argument("fields", nargs="*", help="field to be shown")
    _set_args(cshow, "filter", "limit", "query", "sort")
    sparsers.add_parser("update", help="reset the cache and redownload collections and items", category="manage")
    cview = sparsers.add_parser("view", help="view a single item", category="read")
    cview.add_argument("name", help="field name for selection")
    cview.add_argument("value", help="field value to be selected")
    cview.add_argument("fields", nargs="+", help="field to be shown")
    initialize()
    args.logger = logger
    if getattr(args, "query", None):
        if hasattr(args, "fields") and args.fields == ["-"]:
            args.fields = QUERIES[args.query].get('fields', ["title"])
        args.filter.extend(QUERIES[args.query].get('filter', []))
        if getattr(args, "limit", None) is None:
            args.limit = QUERIES[args.query].get('limit')
        if getattr(args, "sort", None) is None:
            args.sort = QUERIES[args.query].get('sort')
    if hasattr(args, "sort"):
        args.desc = False
        if args.sort is not None:
            args.desc = args.sort[0] == ">"
            if args.sort[0] in "<>":
                args.sort = args.sort[1:]
    if args.command == "reset":
        args.reset, args.stop = True, True
        ZoteroCLI(**vars(args))
    elif args.command == "update":
        args.reset = True
        ZoteroCLI(**vars(args))
    else:
        if args.command == "export":
            args.url_no_check = l = _domains(args.url_no_check)
            args.check_url |= len(l) > 0
        getattr(ZoteroCLI(**vars(args)), args.command, globals().get(args.command))(**vars(args))

