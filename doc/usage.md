## Credentials & data cache

The first time you start the tool, there is a chance (unless you used something before that created it) you don't have the cached credentials located at `~/.zotero/cache/`. You can either enter you API identifier and key through the `--id` and `--key` options or wait for the tool to ask for these. In both cases the values will be cached to `~/.zotero/cache/`. This way, you won't have to re-enter them next time. From a security perspective, the only protection is that, once created, the credentials file immediately gets the read-write permissions only for your own user. So, the API key is NOT encrypted or hashed and thus resides in cleartext, only protected from reading by other users by the applied permissions.

Also, if the cache files do not exist, they will be downloaded from `zotero.org` using [`pyzotero`](https://github.com/urschrei/pyzotero) and saved in `~/.zotero/cache/`. Four JSON files are cached:

- `collections.json`: library's collections, downloaded using `pyzotero`'s `Zotero.collections` method. 
- `items.json`: library's items, downloaded using `pyzotero`'s `Zotero.items` method with parameter `Zotero.everything()` in order to get everything at once.
- `attachments.json` and `notes.json`: computed from the downloaded items.

Note that option `--reset-items` (with command `reset`) allows to only re-download items, and therefore also resets `attachments.json` and `notes.json`.

There are two different ways to reset cached files:

1. Use `-r` (`--reset`) general option (can be used with any command except `reset`)

        :::sh
        $ zotero-cli -r list [...]
        $ zotero-cli -r show [...]

2. Use the `reset` command (this allows to use `--reset-items`)

        :::sh
        $ zotero-cli reset -r
        $ zotero-cli reset --reset-items

## Computed fields

In order to refine the returned data, multiple fields are computed by the tool:

  - `authors`: the list of `creators` with `creatorType` equal to `author`
  - `citations`: the number of relations the item has to other items with a later date
  - `editors`: the list of `creators` with `creatorType` equal to `editor`
  - `numAttachments`: the number of child items with `itemType` equal to `attachment`
  - `numAuthors`: the number of `creators` with `creatorType` equal to `author`
  - `numCreators`: the number of `creators`
  - `numEditors`: the number of `creators` with `creatorType` equal to `editor`
  - `numNotes`: the number of child items with `itemType` equal to `note`
  - `numPages`: the (corrected) number of pages, either got from the original or `pages` field
  - `references`: the number of relations the item has to other items with an earlier date
  - `year`: the year coming from the `datetime` parsing of the `date` field

Additionaly, some fields are extracted from the (native) `extra` field:

  - `comments`: custom field for adding comments
  - `results`: custom field for mentioning results related to the item
  - `what`: custom field for a short description of what the item is about
  - `zscc`: number of Scholar citations, computed with the [Zotero Google Scholar Citations](https://github.com/beloglazov/zotero-scholar-citations) plugin

A PageRank-based reference ranking algorithm is used to refine the data further for allowing to manipulate records by relevance.

  - `rank`: computed field aimed to rank references in order of relevance ; this uses an algorithm similar to Google's PageRank while weighting references in function of their year of publication (giving more importance to recent references, which cannot have as much citations as older references anyway given their recent nature)

!!! note "Filtering and computed fields"
    
    Beware that filters (see next subsection) are applied **BEFORE** computing fields. Therefore, using the `rank` field involves that only the filtered items were considered, which can drastically change results regarding their relevance.

## Filter, sort and limit

For multiple commands, it is possible to filter fields, sort them and/or limit the number of records returned.

- Filtering is done by using the `-f` or `--filter` option with the following format: `[field]:[regex]` ; it is **case-insensitive** and applies to all commands but `reset`.

    For instance, let us assume a collection named "*Bibliography*", the following `regex` value will filter items from this collection (given that no other collection starts with "`biblio`", of course):
    
        :::sh
        $ zotero-cli list title -f "collections:biblio"
    
    Filters are **AND-based**. So, using multiple times the `-f`/`--filter` will of course narrow the results. For instance, this will filter items from a collection named "*Bibliography*" published in 2020:
    
        :::sh
        $ zotero-cli export title -f "collections:biblio" -f "year:2020"
    
    There exists an exception to this regex-based filtering ; the `tags` field. It relies on exact matches among the set of existing tags, which are collected at startup while parsing the items. Consequently, an error will be thrown if a bad tag is entered.
    
        :::sh
        $ zotero-cli show title -f "tags:application" -f "tags:python"

- Sorting is done by using the `-s` or `--sort` option with the following format: `[field]`

    Any valid field can be used to sort records, including computed ones.

## Comparison operators

While filtering some particular fields, it is desirable to use operators to cover multiple values (e.g. with integers as for the `year` field). For this purpose, the common comparison operators (`<`, `>`, `<=`, `>=` and `==`) are available for use with the `-f`/`--filter`, `-s`/`--sort` and `-l`/`--limit` options for the following fields:

- Integers: `citations`, `numAttachments`, `numAuthors`, `numNotes`, `numPages`, `references`, `year`, `zscc`

        :::sh
        $ zotero-cli show title -f "year:<=2015" -f "numPages:>5"

- Floats: `rank`

        :::sh
        $ zotero-cli show title -f "rank:>=1.5" -f "rank:<2.5"

- Dates: `date`, `dateAdded`, `dateModified`

        :::sh
        $ zotero-cli show title -f "date:>Sep 2018"

!!! note "Supported datetime formats"
    
    In order to filter datetimes, the following formats are supported: 
    
    - `%Y`: e.g. `2020`
    - `%b %Y`: e.g. `Oct 2019`
    - `%B %Y`: e.g. `September 2018`
    - `%Y-%m-%dT%H:%M:%SZ`: e.g. `2019-10-01T12:00:00Z`
    - `%b %d %Y at %I:%M%p`: e.g. `Jul 01 2015 at 02:01PM`
    - `%B %d, %Y, %H:%M:%S`: e.g. `April 03, 2016, 13:15:00`

## List field values

It can be useful to inspect the values for a particular field, e.g. for correcting or normalizing some values. The `list` command allows to list all the existing values from the library. It is also possible to list the available fields by simply using `fields`:

```sh
$ zotero-cli list fields

    Fields              
    ------              
    abstractNote        
    accessDate          
    archive             
    archiveLocation     
    [...]

```

Besides valid fields, attached files can also be listed by using `attachments`.

Any of the field names can then be used to list available values.

```sh
$ zotero-cli list publisher

    Publisher                 
    ---------                 
    -                         
    ACM          
    [...]
    IEEE
    [...]
    Springer
    [...]
             
```

When the empty value also exists for the given field, it is listed as "`-`". Beware that it can be filtered by using `-f "[field]:<empty>"`.

```sh
$ zotero-cli show title -f "publisher:<empty>"

    Title                                                                                                     
    -----
    [...]

```

This can be very helpful to identify entries that have missing information.

!!! note "List of values"
    
    Unless handled in the tool, fields that have lists of values (e.g. `tags` with a list of semicolon-separted values) will be displayed as is. The following fields have this special handling for collecting distinct values: `authors`, `creators`, `editors` and `tags`.

## Count/Show/Export items

Library items can be manipulated in different ways, as shown hereafter.

- Counting items (filter only):

        :::sh
        $ zotero-cli count -f "collections:biblio" -f "date:>Sep 2018"
        123

- Showing or exporting items (filter + sort + limit):

        :::sh
        $ zotero-cli show year title numPages -f "collections:biblio" -f "date:>Sep 2018" -s date -l ">rank:2"

