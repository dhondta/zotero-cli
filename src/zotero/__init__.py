# -*- coding: UTF-8 -*-
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import operator
import requests
import xlsxwriter
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pyzotero import zotero, zotero_errors
from tinyscript import *
from tinyscript.helpers.text import _indent
from tinyscript.report import *
from warnings import filterwarnings

filterwarnings("ignore", "The input looks more like a filename than markup")


__all__ = ["ZoteroCLI",
           "CACHE_FILES", "CACHE_PATH", "CHARTS", "CREDS_FILE", "GROUP_FILE", "MARKERS", "OBJECTS", "QUERIES"]

OBJECTS = ["attachments", "notes", "annotations"]
CACHE_FILES = ["collections", "items", "marks"] + OBJECTS
CACHE_PATH = ts.Path("~/.zotero/cache", create=True, expand=True)
CREDS_FILE = ts.CredentialsPath("~/.zotero")
GROUP_FILE = ts.Path("~/.zotero/group", expand=True)

OPERATORS = {
    '==': operator.eq,
    '<':  operator.lt,
    '<=': operator.le,
    '>':  operator.gt,
    '>=': operator.ge,
}

FIELD_ALIASES = {
    'itemType': "Type",
    'what': "What ?",
    'zscc': "#Cited",
}
FLOAT_FIELDS = []
INTEGER_FIELDS = ["callNumber", "citations", "numAttachments", "numAuthors", "numCreators", "numEditors", "numNotes",
                  "numAnnotations", "numPages", "rank", "references", "year", "zscc"]
NOTE_FIELDS = ["comments", "results", "what"]

CHARTS  = ["software-in-time"]
MARKERS = [("read", "unread", "this will display the entry as normal instead of bold"),
           ("irrelevant", "relevant", "this will exclude the entry from the shown results"),
           ("ignore", "unignore", "this will totally ignore the entry while getting the filtered items")]
QUERIES = {
    'no-attachment':         {'filter': ["numAttachments:0"], 'fields': ["title"]},
    'no-url':                {'filter': ["url:<empty>"], 'sort': "year", 'fields': ["year", "title"]},
    'top-10-most-relevants': {'limit': ">rank:10", 'sort': ">date",
                              'fields': ["year", "title", "numPages", "itemType"]},
    'top-50-most-relevants': {'limit': ">rank:50", 'sort': ">date",
                              'fields': ["year", "title", "numPages", "itemType"]},
}
STATIC_WORDS = ["Android", "Bochs", "Linux", "Markov", "NsPack", "Windows"]
TYPE_EMOJIS = {
    'artwork':              ":art:",
    'audio recording':      ":microphone:",
    'blog post':            ":pushpin:",
    'book':                 ":green_book:",
    'book section':         ":closed_book:",
    'computer program':     ":floppy_disk:",
    'conference paper':     ":notebook:",
    'default':              ":question:",
    'document':             ":page_facing_up:",
    'email':                ":email:",
    'encyclopedia article': ":book:",
    'forum post':           ":pushpin:",
    'journal article':      ":newspaper:",
    'magazine article':     ":page_with_curl:",
    'manuscript':           ":scroll:",
    'newspaper article':    ":newspaper:",
    'podcast':              ":video_camera:",
    'preprint':             ":bookmark:",
    'presentation':         ":bar_chart:",
    'report':               ":clipboard:",
    'thesis':               ":mortar_board:",
    'tv broadcast':         ":tv:",
    'video recording':      ":movie_camera:",
    'webpage':              ":earth_americas:",
}
URL_CHECK_HEADERS = {
    'Accept': "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    'Accept-Language': "en-US,en;q=0.9",
    'Accept-Encoding': "gzip, deflate, br",
    'Connection': "close",
    'Range': "bytes=0-0",
    'Upgrade-Insecure-Requests': "1",
    'User-Agent': "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:138.0) Gecko/20100101 Firefox/138.0",
}
URL_NO_CHECK = (
    "arxiv.org",
    "dial.uclouvain.be",
    "dl.acm.org",
    "hal.inria.fr",
    "ieeexplore.ieee.org",
    "inria.hal.science",
    "iopscience.iop.org",
    "link.springer.com",
    "onlinelibrary.wiley.com",
    "researchportal.rma.ac.be",
    "scholar.dsu.edu",
    "web.archive.org",
    "www.ijofcs.org",
    "www.jstage.jst.go.jp",
    "www.ndss-symposium.org",
    "www.researchgate.net",
    "www.researchsquare.com",
    "www.sciencedirect.com",
    "www.scopus.com",
    "www.semanticscholar.org",
    "www.softpedia.com",
    "www.usenix.org",
)


def _check_url(url, nocheck=URL_NO_CHECK):
    try:
        scheme, domain = url.split(":", 1)
    except ValueError:
        scheme, domain = "http", url
    domain = domain.lstrip("/").split("/")[0].split("@")[-1].split(":")[0]
    if scheme not in ["http", "https"] or ts.is_iterable(nocheck) and domain in nocheck:
        return
    response = requests.get(url, headers=URL_CHECK_HEADERS, allow_redirects=True, stream=True)
    code = response.status_code
    response.close()
    if code >= 400:
        return url


def _lower_title(title):
    g = lambda p, n=1: p.group(n)
    for i in range(2):
        # this regex allows to preserve cased subtitles such as: "First Part: Second Part" => "First part: Second part"
        title = re.sub(r"([^-:!?]\s+(?:[A-Z][a-z]+(?:[-_]?[A-Z]?[a-z]+)*|[A-Z]{2}[a-z]{3,}))", \
                       lambda p: g(p) if g(p)[1:].strip() in STATIC_WORDS else g(p)[0] + g(p)[1:].lower(), title)
        # it requires applying twice the transformation as the first one only catches 1 instance out of 2 ;
        #  "An Example Title: With a Subtitle"
        #    ^^^^^^^^^      ^^^^^^ ^^^^^^^^^^
        #                ^
        #        this one is not matched the first time as the last "e" of "Example" was already consumed !
    # this one corrects bad case for substrings after a punctuation among -:!?
    title = re.sub(r"([-:!?]\s+)([a-z]+(?:[-_][A-Z]?[a-z]+)*)", lambda p: g(p) + g(p,2)[0].upper() + g(p,2)[1:], title)
    # the last one ensures that the very first word has its first letter uppercased
    return re.sub(r"^([A-Z][a-z]+(?:[-_][A-Z]?[a-z]+)*)", lambda p: g(p)[0] + g(p)[1:].lower(), title)


class ZoteroCLI:
    def __init__(self, api_id=None, api_id_type="user", api_key=None, creds_file=None, group=False, logger=None,
                 reset=False, stop=False, **kw):
        self.logger = logger
        api_id_type = ["user", "group"][group or GROUP_FILE.exists()]
        # create the default credentials file the first time that the API identifier and secret are input
        if api_id is not None and api_key is not None:
            if not creds_file.exists():
                creds_file.id = api_id
                creds_file.secret = api_key
                creds_file.save()
            else:
                logger.debug(f"Credentials file '{creds_file}' already exists")
        if creds_file.id == "" and creds_file.secret == "":
            creds_file.load()
        if creds_file.id == "" and creds_file.secret == "":
            creds_file.ask("API ID: ", "API key: ")
            creds_file.save()
        self.__zot = None
        cache_dir = self.__cdir = CACHE_PATH.joinpath(creds_file.id)
        cache_dir.mkdir(exist_ok=True)
        if reset:
            self.reset()
        if stop:
            return
        # load data into attributes of this instance
        for k in CACHE_FILES:
            if k == "marks":
                continue
            cached_file = cache_dir.joinpath(k + ".json")
            if cached_file.exists():
                if k == "creds":
                    continue  # marks is not saved as self.marks but well self._marks_file ; process it separately
                with cached_file.open() as f:
                    logger.debug(f"Getting {k} from cache '{cached_file}'...")
                    try:
                        setattr(self, k, json.load(f))
                    except json.decoder.JSONDecodeError:
                        setattr(self, k, [])
            else:
                # setup a zotero.Zotero instance once
                self.__zot = self.__zot or zotero.Zotero(creds_file.id, api_id_type, creds_file.secret)
                # now get the data from zotero.org
                logger.debug(f"Getting {k} from zotero.org...")
                if k == "collections":
                    try:
                        self.collections = list(self.__zot.collections())
                    except zotero_errors.ResourceNotFound:
                        logger.error(f"Nothing found for ID {creds_file.id}")
                        logger.warning("Beware to use the --group option if this is the ID of a group")
                        return
                elif k == "items":
                    self.items = list(self.__zot.everything(self.__zot.top()))
                elif k in OBJECTS:
                    for attr in OBJECTS:
                        if not hasattr(self, attr):
                            setattr(self, attr, [])
                    for i in self.items[:]:
                        if i['meta'].get('numChildren', 0) > 0:
                            for c in self.__zot.children(i['key']):
                                t = c['data']['itemType']
                                tpl = f"{t}s"
                                if tpl in OBJECTS:
                                    getattr(self, tpl).append(c)
                                else:
                                    raise ValueError(f"Unknown item type '{t}'")
                with cached_file.open('w') as f:
                    logger.debug(f"Saving {k} to cache '{cached_file}'...")
                    json.dump(getattr(self, k), f)
        # handle marks.json separately
        self._marks_file = cache_dir.joinpath("marks.json")
        # on the contrary of other JSON files (which are lists of dictionaries), marks.json is a dictionary
        if not self._marks_file.exists():
            self._marks_file.write_text("{}")
        with self._marks_file.open() as f:
            logger.debug(f"Opening marks from cache '{self._marks_file}'...")
            self.marks = json.load(f)
        self.__objects = {}
        for a in CACHE_FILES:
            d = getattr(self, a)
            if isinstance(d, list):
                for x in d:
                    try:
                        self.__objects[x['key']] = x
                    except:
                        print(x)
                        raise
        self._valid_fields = []
        self._valid_tags = []
        # parse items, collecting valid fields and tags
        for i in self.items:
            tags = i['data'].get('tags')
            if tags:
                if ts.is_str(tags):
                    tags = tags.split(";")
                elif ts.is_list(tags):
                    tags = [t['tag'] for t in tags]
                for t in tags:
                    if t not in self._valid_tags:
                        self._valid_tags.append(t)
            for f in i['data'].keys():
                if f not in self._valid_fields:
                    self._valid_fields.append(f)
        # also append computed fields to the list of valid fields
        for f in ["abstractShortNote", "attachments", "authors", "editors", "firstAuthor", "selected"] + \
                 INTEGER_FIELDS + NOTE_FIELDS:
            if f not in self._valid_fields:
                self._valid_fields.append(f)
    
    def _expand_limit(self, limit, sort=None, desc=False, age=True):
        """ Expand the 'limit' parameter according to the following format: (([order])[field]:)[limit]
             - order: "<" for increasing, ">" for decreasing
             - field: target field
             - limit: numerical value for limiting records """
        lfield, lfdesc = sort, desc
        if limit is not None:
            try:
                lfield, limit = limit.split(":")
                lfield = lfield.strip()
                # handle [<>] as sort orders
                if lfield[0] in "<>":
                    lfdesc = lfield[0] == ">"
                    lfield = lfield[1:]
                # handle "rank*" as using the strict rank, that is, with no damping factor relatd to the item's age
                if lfield == "rank*":
                    age = False
                    lfield = "rank"
            except ValueError:
                pass
            if not str(limit).isdigit() or int(limit) <= 0:
                raise ValueError("Bad limit number ; sould be a positive integer")
            limit = int(limit)
        return limit, lfield, lfdesc, age

    
    def _filter(self, fields=None, filters=None, force=False):
        """ Apply one or more filters to the items. """
        # validate and make filters
        _filters, raised = {}, False
        for f in filters or []:
            try:
                field, regex = list(map(lambda x: x.strip(), f.split(":", 1)))
            except ValueError as e:
                raise ValueError(f"Bad filter '{f}' ; format: [field]:[regex]")
            if regex == "":
                raise ValueError(f"Regex for filter on field '{field}' is empty")
            not_ = field[0] == "~"
            if not_:
                field = field[1:]
            # filter format: (negate, comparison operator, first comparison value's lambda, second comparison value)
            if field in set(INTEGER_FIELDS) - set(["rank"]) and re.match(r"^(|<|>|<=|>=|==)\d+$", regex):
                m = re.match(r"^(|<|>|<=|>=|==)(\d+)$", regex)
                op, v = m.group(1), m.group(2).strip()
                if op == "":
                    op = "=="
                filt = (not_, OPERATORS[op], lambda i, f: i['data'][f], int(v))
            elif field.startswith("date"):
                if regex in ["-", "<empty>"]:
                    op, v = "==", ""
                else:
                    m = re.match(r"^(<|>|<=|>=|==)([^=]*)$", regex)
                    op, v = m.group(1), m.group(2).strip()
                filt = (not_, OPERATORS[op], lambda i, f: ZoteroCLI.date(i['data'][f], i), ZoteroCLI.date(v))
            elif field == "rank":
                m = re.match(r"^(<|>|<=|>=|==)(\d+|\d*\.\d+)$", regex)
                op, v = m.group(1), m.group(2).strip()
                filt = (not_, OPERATORS[op], lambda i, f: self.ranks.get(i['key'], 0), float(v))
            # filter format: (negate, lambda, lambda's second arg)
            elif field == "tags":
                if regex not in self._valid_tags and regex not in ["-", "<empty>"]:
                    self.logger.warning(f"Got tag '{regex}' ; should be one of:\n- " + \
                                         "\n- ".join(sorted(self._valid_tags, key=ZoteroCLI.sort)))
                    raise ValueError(f"Tag '{regex}' does not exist")
                filt = (not_, lambda i, r: r in ["-", "<empty>"] and i['data']['tags'] in ["", []] or \
                                        r in (i['data']['tags'].split(";") if ts.is_str(i['data']['tags']) else \
                                              [x['tag'] for x in i['data']['tags']]), regex)
            # filter format: (negate, lambda) ; lambda's second arg is the field name 
            elif regex in ["-", "<empty>"]:
                filt = (not_, lambda i, f: i['data'].get(f) == 1900) if field == "year" else \
                       (not_, lambda i, f: i['data'].get(f) == "")
            else:
                filt = (not_, re.compile(regex, re.I), lambda i, f: i['data'].get(f) or "")
            _filters.setdefault(field, [])
            _filters[field].append(filt)
        # validate fields
        afields = (fields or []) + list(_filters.keys())
        for f in afields:
            if f not in self._valid_fields and regex != "-":
                self.logger.warning(f"Got field name '{f}' ; should be one of:\n- " + \
                                     "\n- ".join(sorted(self._valid_fields, key=ZoteroCLI.sort)))
                raise ValueError(f"Bad field name '{f}'")
        # now yield items, applying the filters and only selecting the given fields
        for i in self.items:
            # create a temporary item with computed fields (e.g. citations)
            tmp_i = {k: v for k, v in i.items() if k != 'data'}
            tmp_i['data'] = d = {k: self._format_value(v, k) for k, v in i['data'].items() if k in afields}
            d['zscc'] = -1
            # set custom fields defined in the special field named "Extra"
            for l in i['data'].get('extra', "").splitlines():
                try:
                    field, value = list(map(lambda x: x.strip(), l.split(": ", 1)))
                except:
                    continue
                field = field.lower()
                if field not in i['data'].keys():
                    if field == "zscc":
                        try:
                            d[field] = int(value)
                        except:
                            pass
                    else:
                        d[field] = self._format_value(value, field)
            # compute non-existing fields if required
            if "abstractShortNote" in afields:
                asn = re.split(r"\.(\s|$)", i['data']['abstractNote'])[0]
                d['abstractShortNote'] = re.sub(r"\r?\n", "", asn.strip()) + "."
            if "attachments" in afields:
                d['attachments'] = [x['data']['title'] for x in self.attachments if x['data']['parentItem'] == i['key']]
            if "authors" in afields:
                d['authors'] = [c for c in i['data']['creators'] if c['creatorType'] in ["author", "presenter"]]
            if "citations" in afields or "references" in afields:
                c, r = 0, 0
                try:
                    links = i['data']['relations']['dc:relation']
                    if not ts.is_list(links):
                        links = [links]
                    for link in links:
                        k = self.__objects[link.split("/")[-1]]
                        if "collections" in _filters.keys():
                            gb = True
                            for n, regex, _ in _filters['collections']:
                                b = regex.search(", ".join(self.__objects[x]['data']['name'] for x in \
                                                           k['data']['collections']))
                                gb = gb and [b, not b][n]
                            if not gb:
                                continue
                        if ZoteroCLI.date(k['data']['date'], k) > ZoteroCLI.date(i['data']['date'], i):
                            c += 1
                        if ZoteroCLI.date(k['data']['date'], k) <= ZoteroCLI.date(i['data']['date'], i):
                            r += 1
                except KeyError:
                    pass
                d['citations'] = c
                d['references'] = r
            if "collections" in afields:
                d['collections'] = [self.__objects[k]['data']['name'] for k in i['data']['collections']]
            if "editors" in afields:
                d['editors'] = [c for c in i['data']['creators'] if c['creatorType'] == "editor"]
            if "firstAuthor" in afields:
                a = [c for c in i['data']['creators'] if c['creatorType'] in ["author", "presenter"]]
                d['firstAuthor'] = a[0] if len(a) > 0 else ""
            if "numAttachments" in afields:
                d['numAttachments'] = len([x for x in self.attachments if x['data']['parentItem'] == i['key']])
            if "numAuthors" in afields:
                d['numAuthors'] = len([x for x in i['data']['creators'] if x['creatorType'] in ["author", "presenter"]])
            if "numCreators" in afields:
                d['numCreators'] = len([x for x in i['data']['creators']])
            if "numEditors" in afields:
                d['numEditors'] = len([x for x in i['data']['creators'] if x['creatorType'] == "editor"])
            if "numNotes" in afields:
                d['numNotes'] = len([x for x in self.notes if x['data']['parentItem'] == i['key']])
            if "numAnnotations" in afields:
                d['numAnnotations'] = len([x for x in self.annotations if x['data']['parentItem'] == i['key']])
            if "numPages" in afields:
                p = i['data'].get('numPages', i['data'].get('pages')) or "0"
                m = re.match(r"(\d+)(?:\s*[\-–]+\s*(\d+))?$", p)
                if m:
                    s, e = m.groups()
                    d['numPages'] = abs(int(s) - int(e or 0)) or -1
                else:
                    self.logger.warning(f"Bad pages value '{p}'")
                    d['numPages'] = -1
            if any(x in NOTE_FIELDS for x in afields):
                for f in NOTE_FIELDS:
                    d[f] = ""
                for n in self.notes:
                    if n['data']['parentItem'] == i['key']:
                        t = bs4.BeautifulSoup(n['data']['note'], "html.parser").text
                        try:
                            f, c = t.split(":", 1)
                        except:
                            continue
                        f = f.lower()
                        if f in NOTE_FIELDS:
                            d[f] = c.strip()
            if "year" in afields:
                dt = i.get('data', {}).get('date')
                d['year'] = ZoteroCLI.date(dt, i).year if dt else 1900
            # now apply filters
            pass_item = False
            for field, tfilters in _filters.items():
                for tfilter in tfilters:
                    if isinstance(tfilter[1], re.Pattern):
                        b = tfilter[1].search(self._format_value(tfilter[2](tmp_i, field), field))
                    elif ts.is_lambda(tfilter[1]) and len(tfilter) == 2:
                        b = tfilter[1](tmp_i, field)
                    elif ts.is_lambda(tfilter[1]) and len(tfilter) == 3:
                        b = tfilter[1](tmp_i, tfilter[2])
                    elif len(tfilter) == 4:
                        b = tfilter[1](tfilter[2](tmp_i, field), tfilter[3])
                    else:
                        raise ValueError("Unsupported filter")
                    if [not b, b][tfilter[0]]:
                        pass_item = True
                        break
                if pass_item:
                    break
            if not pass_item and (not tmp_i['key'] in self.marks.get('ignore', []) or force):
                yield tmp_i
    
    def _format_value(self, value, field=""):
        """ Ensure the given value is a string. """
        v = value
        if field == "tags":
            return v if ts.is_str(v) else ";".join(x['tag'] for x in v)
        elif field == "itemType":
            return re.sub(r'([a-z0-9])([A-Z])', r'\1 \2', re.sub(r'(.)([A-Z][a-z]+)', r'\1 \2', v)).lower()
        elif field == "rank":
            return f"{float(v or '0'):.3f}"
        elif field == "year":
            return [str(v), "-"][v == 1900]
        elif ts.is_int(v):
            return [str(v), "-"][v < 0]
        elif ts.is_list(v):
            return [", ", ";"][field == "attachments"].join(self._format_value(x, field) for x in v)
        elif ts.is_dict(v):
            if field in ["authors", "creators", "editors", "firstAuthor"]:
                v = v.get('name') or "{} {}".format(v.get('lastName', ""), v.get('firstName', "")).strip()
        return str(v)
    
    def _items(self, fields=None, filters=None, sort=None, desc=False, limit=None, force=False):
        """ Get items, computing special fields and applying filters. """
        filters = filters or []
        sort = sort or fields[0]
        data = []
        age, order = True, 3
        # define the order of the damping factor function to be applied to the rank field
        for f in fields:
            m = re.match(r"rank(\*|\^[1-9])$", f)
            if m:
                break
        if m:
            f = m.group()
            if m.group(1) == "*":
                age = False
            else:
                order = int(m.group(1).lstrip("^"))
            fields.insert(fields.index(f), "rank")
            fields.remove(f)
        # extract the limit field
        limit, lfield, lfdesc, age = self._expand_limit(limit, sort, desc, age)
        # select relevant items, including all the fields required for further computations
        ffields = fields[:]
        if sort not in ffields:
            ffields.append(sort)
        if "rank" in fields or lfield == "rank" or sort == "rank" or \
           "rank" in [f.split(":")[0].lstrip("~") for f in filters or []]:
            for f in ["rank", "title", "citations", "references", "year", "zscc"]:
                if f not in ffields:
                    ffields.append(f)
        if lfield not in ffields:
            ffields.append(lfield)
        self.logger.debug(f"Selected fields: {'|'.join(ffields)}")
        if len(filters):
            self.logger.debug(f"Filtering entries ({filters})...")
        items = {i['key']: i for i in \
                 self._filter(ffields, [f for f in filters if not re.match(r"\~?rank\:", f)], force)}
        if len(items) == 0:
            self.logger.info("No data")
            return [], []
        # compute ranks similarly to the Page Rank algorithm, if relevant
        if "rank" in ffields:
            self.logger.debug("Computing ranks...")
            # principle: items with a valid date get a weight, others (with year==1900) do not
            self.ranks = {k: 1./len(items) if i['data']['year'] > 1900 else 0. for k, i in items.items()}
            # now we can iterate
            prev = tuple(self.ranks.values())
            for n in range(len(self.ranks)):  # at most N iterations are required (N being the number of keys)
                for k1 in self.ranks.keys():
                    k1_d = self.__objects[k1]['data']
                    links = k1_d['relations'].get('dc:relation', [])
                    if not ts.is_list(links):
                        links = [links]
                    if items[k1]['data']['year'] == 1900:
                        continue
                    # now compute the iterated rank
                    self.ranks[k1] = float(len([None for l in links if l.split("/")[-1] in items.keys()]) > 0)
                    for link in links:
                        k2 = link.split("/")[-1]
                        if k2 not in items.keys():
                            continue
                        k2_d = self.__objects[k2]['data']
                        if ZoteroCLI.date(k1_d['date'], k1_d) <= ZoteroCLI.date(k2_d['date'], k2_d):
                            k2_d = items.get(k2, {}).get('data')
                            if k2_d:
                                r = k2_d['references']
                                if r > 0:
                                    # consider a damping factor on a per-item basis, taking age into account
                                    self.ranks[k1] += self.ranks.get(k2, 0.) / r
                # check for convergence
                if tuple(self.ranks.values()) == prev:
                    self.logger.debug(f"Ranking algorithm converged after {n} iterations")
                    break
                prev = tuple(self.ranks.values())
            # apply the damping factor at the very end
            if age:
                dt_zero = ZoteroCLI.date("").timestamp()
                dt = set(ZoteroCLI.date(i['data']['date']).timestamp() for i in items.values()) - {dt_zero}
                # min/max years are computed to take item's age into account
                dt_min, dt_max = min(dt), max(dt)
                # in order not to get a null damping factor for items with minimum year, we shift y_min by 10% to the left
                dt_min -= max(1, (dt_max - dt_min) // 10)
                ddt = float(dt_max - dt_min)
                # set the damping factor formula relying on the previously defined order (default is order 3)
                df_func = lambda dt: (float(ZoteroCLI.date(dt).timestamp()-dt_min)/ddt)**order
                self.ranks = {k: df_func(items[k]['data']['date']) * v for k, v in self.ranks.items()}
            # finally, we normalize ranks
            max_rank = max(self.ranks.values())
            self.ranks = {k: v / max_rank if max_rank else 0. for k, v in self.ranks.items()}
            for k, r in sorted(self.ranks.items(), key=lambda x: -x[1]):
                k_d = items[k]['data']
                self.logger.debug(f"{r:.05f} - {k_d['title']} ({k_d['date']})")
            # reapply filters, including for fields that were just computed
            items = {i['key']: i for i in self._filter(ffields, filters, force)}
            for k, i in items.items():
                i['data']['rank'] = self.ranks.get(k)
            if len(items) == 0:
                self.logger.info("No data")
                return
        # exclude irrelevant items from the list of items
        if not force:
            for k, i in {k: v for k, v in items.items()}.items():
                if k in self.marks.get('irrelevant', []):
                    del items[k]
        # apply the limit on the selected items
        if limit is not None:
            if lfield is not None:
                select_items = sorted(items.values(), key=lambda i: ZoteroCLI.sort(i['data'][lfield], lfield))
            else:
                select_items = list(items.values())
            if lfdesc:
                select_items = select_items[::-1]
            self.logger.debug(f"Limiting to {limit} items (sorted based on {lfield or sort} in "
                              f"{['ascending', 'descending'][lfdesc]} order)...")
            items = {i['key']: i for i in select_items[:limit]}
        # ensure that the rank field is set for every item
        if "rank" in ffields:
            for i in items.values():
                i['data']['rank'] = self.ranks.get(i['key'], .0)
        # format the selected items as table data
        self.logger.debug(f"Sorting items based on {sort}...")
        for i in sorted(items.values(), key=lambda i: ZoteroCLI.sort(i['data'].get(sort, "-"), sort)):
            row = [self._format_value(i['data'].get(f), f) if i['data'].get(f) else "-" for f in fields]
            if len(row) > 1 and all(x in ".-" for x in row[1:]):  # row[0] is the item's key ; shall never be "." or "-"
                continue
            data.append(row)
        if desc:
            data = data[::-1]
        return [ZoteroCLI.header(f) for f in fields], data
    
    def _marks(self, marker, filters=None, sort=None, desc=False, limit=None):
        """ Mark the selected items with a specified marker.
        
        NB: by convetion, a marker can be submitted as its negation with the "un" prefix ; e.g. read <> unread
        """
        m1, m2, negate = None, None, False
        for m1, m2, _ in MARKERS:
            if marker in [m1, m2]:
                negate = marker == m2
                marker = m1
                break
        if m1 is None:
            raise ValueError("Bad marker (should be one of: {})".format("|".join(x for p in MARKERS for x in p[:2])))
        self.marks.setdefault(marker, [])
        _, data = self._items(["key"], filters, sort, desc, limit, True)
        for row in data:
            k = row[0]
            if negate:
                try:
                    self.marks[marker].remove(k)
                    self.logger.debug(f"Unmarked {k} from {marker}")
                except ValueError:
                    pass
            elif k not in self.marks[marker]:
                self.logger.debug(f"Marked {k} as {marker}")
                self.marks[marker].append(k)
        self.marks = {k: l for k, l in self.marks.items() if len(l) > 0}
        with self._marks_file.open('w') as f:
            self.logger.debug(f"Saving marks to cache '{self._marks_file}'...")
            json.dump(self.marks, f)
    
    @ts.try_or_die(exc=ValueError, trace=False)
    def count(self, filters=None, **kw):
        """ Count items while applying filters. """
        _, data = self._items(["title"], filters or [])
        print(len(data))
    
    @ts.try_or_die(exc=ValueError, trace=False)
    def export(self, fields=None, filters=None, sort=None, desc=False, limit=None, line_format=None,
               output_format="xlsx", check_url=False, url_no_check=None, **kw):
        """ Export the selected fields of items while applying filters to an Excel file. """
        if "{stars}" in (line_format or "") and "rank" not in fields:
            fields.append("rank")
        headers, data = self._items(fields, filters, sort, desc, limit)
        if output_format == "xlsx":
            c, r = string.ascii_uppercase[len(headers)-1], len(data) + 1
            self.logger.debug("Creating Excel file...")
            wb = xlsxwriter.Workbook("export.xlsx")
            ws = wb.add_worksheet()
            ws.add_table(f"A1:{c}{r}", {
                'autofilter': 1,
                'columns': [{'header': h} for h in headers],
                'data': data,
            })
            # center header cells
            cc = wb.add_format()
            cc.set_align("center")
            for i, h in enumerate(headers):
                ws.write(f"{string.ascii_uppercase[i]}1", h, cc)
            # fix widths
            max_w = []
            wtxt = [False] * len(headers)
            for i in range(len(headers)):
                m = max(len(str(row[i])) for row in [headers] + data)
                w = min(m, 80)
                wtxt[i] = wtxt[i] or m > 80
                max_w.append(w)
                ws.set_column("{0}:{0}".format(string.ascii_uppercase[i]), w)
            # wrap text where needed and fix heights
            tw = wb.add_format()
            tw.set_text_wrap()
            for j, row in enumerate(data):
                for i, v in enumerate(row):
                    if wtxt[i]:
                        ws.write(string.ascii_uppercase[i] + str(j+2), v, tw)
            wb.close()
            return
        elif output_format in ["csv", "json", "xml", "yaml"] or line_format is None:
            r = Report(Table(data, column_headers=headers))
        else:
            if "{stars}" in line_format:
                # determine highest rank
                mr, i_rank = 0., [h.lower() for h in headers].index("rank")
                for row in data:
                    r = row[i_rank]
                    mr = max(mr, float(r if r != "-" else 0))
            lines = []
            if check_url:
                url_check_executor, results = ThreadPoolExecutor(max_workers=10), {}
            for row in data:
                d = {k.lower(): v for k, v in zip(headers, row)}
                if check_url and d['url'] not in ["", "-"]:
                    results[url_check_executor.submit(_check_url, d['url'], url_no_check or URL_NO_CHECK)] = d['url']
                if "Title" in headers and "Url" in headers:
                    d['lower_title'] = t = _lower_title(d['title'])
                    d['link'] = d['title'] if d['url'] in ["", "-"] else f"[{d['title']}]({d['url']})"
                    d['link_lower'] = t if d['url'] in ["", "-"] else f"[{t}]({d['url']})"
                if "link" in d.keys() and "link_with_abstract" in line_format:
                    if "AbstractNote" in headers:
                        d['link_with_abstract'] = d['link'] if d['abstractnote'] == "-" else \
                                                  f"{d['link']}\n\n{_indent(d['abstractnote'], 2)}\n\n"
                    elif "AbstractShortNote" in headers:
                        d['link_with_abstract'] = d['link'] if d['abstractshortnote'] == "." else \
                                                  f"{d['link']} - {d['abstractshortnote']}"
                if "{emoji}" in line_format:
                    d['emoji'] = TYPE_EMOJIS.get(d['type'], TYPE_EMOJIS['default'])
                if "{stars}" in line_format:
                    r = float(d['rank']) if d['rank'] != "-" else 0.
                    s = " :star2:" if r == mr else " :star:"
                    d['stars'] = "" if r < .35 else s if .35 <= r < .65 else 2*s if .65 <= r < .85 else 3*s
                lines.append(line_format.format(**d))
            if check_url:
                for r in as_completed(results):
                    try:
                        url = results[r]
                        if r.result() is None:
                            continue
                        self.logger.warning(f"Broken link: {url}")
                    except requests.exceptions.ConnectionError:
                        continue
                    except requests.exceptions.SSLError:
                        self.logger.error(f"Broken link: {url} (SSL certificate check failure))")
                url_check_executor.shutdown()
            r = Report(List(*lines))
        r.filename = "export"
        self.logger.debug(f"Creating {output_format.upper()} file...")
        getattr(r, output_format)(save_to_file=True)
    
    @ts.try_or_die(exc=ValueError, trace=False)
    def list(self, field, filters=None, desc=False, limit=None, **kw):
        """ List field's values while applying filters. """
        if field == "collections":
            l = [c['data']['name'] for c in self.collections]
            self.logger.warning("Filters are not applicable to field: collections")
        elif field == "fields":
            l = self._valid_fields
            self.logger.warning("Filters are not applicable to field: fields")
        else:
            l = [row[0] for row in self._items([field], filters)[1]]
        if len(l) == 0:
            return
        if field in ["attachments", "tags"]:
            tmp, l = l[:], []
            for x in tmp:
                l.extend(x.split(";"))
        elif field in ["authors", "creators", "editors"]:
            tmp, l = l[:], []
            for x in tmp:
                l.extend(x.split(", "))
        data = [[x] for x in sorted(set(l), key=lambda x: ZoteroCLI.sort(x, field)) if x != "-"]
        if desc:
            data = data[::-1]
        if limit is not None:
            data = data[:limit]
        print(ts.BorderlessTable([[ZoteroCLI.header(field)]] + data))
    
    @ts.try_or_die(exc=ValueError, trace=False)
    def mark(self, marker, filters=None, sort=None, desc=False, limit=None, **kw):
        """ Mark the selected items as read/unread. """
        self._marks(marker, filters, sort, desc, limit)
    
    @ts.try_or_die(exc=ValueError, trace=False)
    def plot(self, name, filters=None, **kw):
        """ Plot a chart given its slug. """
        if name == "software-in-time":
            data = {}
            for i in self._filter(["title", "date"], ["itemType:computerProgram"] + filters):
                y = ZoteroCLI.date(i['data']['date'], i).year
                data.setdefault(y, [])
                data[y].append(i['data']['title'])
            for y, t in sorted(data.items(), key=lambda x: x[0]):
                print([f"{y}:", "####:"][y == 1900], ", ".join(t))
        else:
            self.logger.debug(f"Got chart name '{name}' ; should be one of:\n- " + "\n- ".join(sorted(CHARTS)))
            self.logger.error("Bad chart")
            raise ValueError
    
    @ts.try_or_die(exc=ValueError, trace=False)
    def show(self, fields=None, filters=None, sort=None, desc=False, limit=None, **kw):
        """ Show the selected fields of items while applying filters. """
        # ensure the 'key' field is included for filtering the items ; then do not keep it if not selected
        output_key = "key" in fields
        if not output_key:
            fields = ["key"] + fields
        headers, data = self._items(fields, filters, sort, desc, limit)
        keys, data = [row[fields.index("key")] for row in data], [row[int(not output_key):] for row in data]
        if not output_key:
            headers = headers[1:]
        if len(headers) > 0:
            table = ts.BorderlessTable([headers] + data)
            t_idx = headers.index("Title")
            for key, row in zip(keys, table.table_data[2:]):
                if t_idx > 0:
                    row[t_idx] = "\n".join(ts.txt2italic(l) if len(l) > 0 else "" for l in row[t_idx].split("\n"))
                if key not in self.marks.get('read', []):
                    for i, v in enumerate(row):
                        row[i] = "\n".join(ts.txt2bold(l) if len(l) > 0 else "" for l in v.split("\n"))
            print(table)
    
    def reset(self, reset_items=False, **kw):
        for k in CACHE_FILES:
            if reset_items and k not in ["items"] + OBJECTS or k == "marks":
                continue
            self.__cdir.joinpath(k + ".json").remove(False)
    
    @ts.try_or_die(exc=ValueError, trace=False)
    def view(self, name, value, fields=None, **kw):
        """ View a single item given a field and its value. """
        headers, data = self._items(fields, [f"{name}:{value}"])
        for h, d in zip(headers, data[0]):
            hb = ts.txt2bold(h)
            if h == "Title":
                d = ts.txt2italic(d)
            try:
                d = ast.literal_eval(d)
            except:
                pass
            if not isinstance(d, dict):
                print("{: <24}: {}".format(hb, d))
            else:
                if len(d) == 0:
                    print("{: <24}: -".format(hb))
                elif h == "Relations":
                    print("{: <24}:".format(hb))
                    rel = d['dc:relation']
                    if isinstance(rel, str):
                        rel = [rel]
                    for k in rel:
                        print(f"- {ts.txt2italic(self.__objects[k.split('/')[-1]]['data']['title'])}")
                else:
                    print("{: <24}:\n".format(hb))
                    for i in d:
                        print(f"- {i}")

    @staticmethod
    def date(date_str, data=None):
        if date_str == "":
            return datetime.strptime("1900-01-01", "%Y-%m-%d")
        dt = ts.dateparse(date_str)
        if dt:
            return dt
        msg = f"Bad datetime format: {date_str}"
        if data:
            msg += f" for item titled '{ZoteroCLI.title(data)}'"
        msg += ". Using default date 1900-01-01."
        self.logger.warning(msg)
        return datetime.strptime("1900-01-01", "%Y-%m-%d")
    
    @staticmethod
    def header(field):
        h = FIELD_ALIASES.get(field, re.sub(r"^num([A-Z].*)$", r"#\1", field))
        return h[0].upper() + h[1:]
    
    @staticmethod
    def sort(value, field=None):
        field = field or ""
        if field.startswith("date") or field.endswith("Date"):
            return ZoteroCLI.date(value.lstrip("-"), f"sort per {field}").timestamp()
        elif field in FLOAT_FIELDS or field in INTEGER_FIELDS:
            try:
                return float(-1 if value in ["", "-", None] else value)
            except:
                self.logger.warning(f"Bad value '{value}' for field {field}")
                return -1
        elif field == "title":
            s = str(value).lower()
            if len(s) > 0 and s.split(maxsplit=1)[0] in ["a", "an", "the"]:
                s = s.split(maxsplit=1)[-1]
            s = re.sub(r"^\$", "s", re.sub(r"^\@", "a", s.lstrip())).lstrip(string.punctuation)
            return s
        else:
            return str(value).lower()
    
    @staticmethod
    def title(data=None):
        return(data or {}).get('data', data).get('title', "undefined")

