# FAQ

## How to enter new credentials ?

Reference: [*Credentials & data cache*](usage.html#credentials-data-cache).

```sh
$ zotero-cli --id <my-id> --key <my-key> [...]
$ zotero-cli -i <my-id> -k <my-key> [...]
```

This will save the new credentials to `~/.zotero/creds.txt`. If you want to immediately re-download library items, use the `reset` command.

```sh
$ zotero-cli --id <my-id> --key <my-key> reset
$ zotero-cli -i <my-id> -k <my-key> reset
```

## How to reset the cache ?

Reference: [*Credentials & data cache*](usage.html#credentials-data-cache).

```sh
$ zotero-cli reset
```

In order to only reset cached items (and therefore attachments and notes), use:

```sh
$ zotero-cli reset --reset-items
$ zotero-cli reset -r
```

If you want to reset everything while using another command, use `-r` or `--reset`:

```sh
$ zotero-cli --reset list title
$ zotero-cli -r count
$ zotero-cli -r show [...]
```

## How to list values ?

Reference: [*List field values*](usage.html#list-field-values).

```sh
$ zotero-cli list title
$ zotero-cli list authors
$ zotero-cli list collections
$ zotero-cli list attachments
```

## How to show items with filters ?

Reference: [*Filter, sort and limit*](usage.html#filter-sort-limit).

```sh
$ zotero-cli show title -f "collections:bibliography"
$ zotero-cli show year title -f "collections:biblio" -f "date:2020"
$ zotero-cli show year title numPages -f "collections:biblio" -f "date:2020" -f "tags:python"
```

!!! note "Filter characteristics"
    
    Filters are **case-insensitive** and only **AND**-based. The `tags` field is an exception to regex-based filtering as it uses exact matching with regard to the list of valid tags encountered in the whole library of items.

## How to sort items ?

Reference: [*Filter, sort and limit*](usage.html#filter-sort-limit).

```sh
$ zotero-cli show title -f "collections:biblio" -s date
$ zotero-cli show year title -f "collections:biblio" -s "<date"
$ zotero-cli show year title -f "collections:biblio" -s ">date"
```

## How to limit the number of items ?

Reference: [*Filter, sort and limit*](usage.html#filter-sort-limit).

```sh
$ zotero-cli show year title -f "collections:biblio" -l "date:10"
$ zotero-cli show year title -f "collections:biblio" -l ">date:10"
$ zotero-cli show year title -f "collections:biblio" -s date -l "numPages:10"
$ zotero-cli show year title -f "collections:biblio" -s date -l ">numPages:10"
```

!!! note "Sorting before applying the limit"
    
    Beware that, if `--sort` and `--limit` are used together, a first sorting is applied based on the field name mentioned in `--limit` and items are then sorted with the field from `--sort`.

## How to filter all items for a given author ?

References: [*Filter, sort and limit*](usage.html#filter-sort-limit), [*Count/Show/Export items*](usage.html#count-show-export-items).

```sh
$ zotero-cli show year title -f "collections:biblio" -f "authors:smith"
$ zotero-cli show year title -f "collections:biblio" -f "authors:smith" -f "authors:anderson"
```

## How to show titles for which the date is not filled in ?

References: [*Filter, sort and limit*](usage.html#filter-sort-limit), [*Count/Show/Export items*](usage.html#count-show-export-items).

```sh
$ zotero-cli show title -f "date:<empty>"
$ zotero-cli show title -f "collections:biblio" -f "date:-"
```

## How to mark items as read/unread ?

Reference: [*Mark items as read/unread*](usage.html#mark-items-as-read-unread)

```sh
$ zotero-cli mark --filter "key:QZR5QAIW"
$ zotero-cli mark --query "top-10-most-relevants"
```

