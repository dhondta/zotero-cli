<p align="center"><img src="https://github.com/dhondta/zotero-cli/raw/main/doc/logo.png"></p>
<h1 align="center">Zotero CLI <a href="https://twitter.com/intent/tweet?text=Zotero%20CLI%20-%20A%20Tinyscript%20tool%20for%20sorting,%20ranking%20and%20exporting%20Zotero%20references%20based%20on%20pyzotero.%0D%0Ahttps%3a%2f%2fgithub%2ecom%2fdhondta%2fzotero-cli%0D%0A&hashtags=python,zotero,cli,pyzotero,pagerank"><img src="https://img.shields.io/badge/Tweet--lightgrey?logo=twitter&style=social" alt="Tweet" height="20"/></a></h1>
<h3 align="center">Sort and rank your Zotero references easy from your CLI.</h3>

[![PyPi](https://img.shields.io/pypi/v/zotero-cli-tool.svg)](https://pypi.python.org/pypi/zotero-cli-tool/)
![Platform](https://img.shields.io/badge/platform-linux-yellow.svg)
[![Read The Docs](https://readthedocs.org/projects/zotero-cli/badge/?version=latest)](http://zotero-cli.readthedocs.io/en/latest/?badge=latest)
[![Requirements Status](https://requires.io/github/dhondta/zotero-cli/requirements.svg?branch=main)](https://requires.io/github/dhondta/zotero-cli/requirements/?branch=main)
[![Known Vulnerabilities](https://snyk.io/test/github/dhondta/zotero-cli/badge.svg?targetFile=requirements.txt)](https://snyk.io/test/github/dhondta/zotero-cli?targetFile=requirements.txt)
[![DOI](https://zenodo.org/badge/321932121.svg)](https://zenodo.org/badge/latestdoi/321932121)
[![License](https://img.shields.io/pypi/l/zotero-cli-tool.svg)](https://pypi.python.org/pypi/zotero-cli-tool/)

This [Tinyscript](https://github.com/dhondta/zotero-cli) tool relies on [`pyzotero`](https://github.com/urschrei/pyzotero) for communicating with [Zotero's Web API](https://www.zotero.org/support/dev/web_api/v3/start). It allows to list field values, show items in tables in the CLI or also export sorted items to an Excel file.


```session
$ pip install zotero-cli-tool
```

## :fast_forward: Quick Start

The first time you start it, the tool will ask for your API identifier and key. It will cache it to `~/.zotero/creds.txt` with permissions set to `rw` for your user only. Data is cached to `~/.zotero/cache/`. If you are using a shared group library, you can either pass the "`-g`" ("`--group`") option in your `zotero-cli` command or, for setting it permanently, touch an empty file `~/.zotero/group`.

- Manually update cached data

```sh
$ zotero-cli reset
```

Note that it could take a while. That's why caching is interesting for further use.

- Count items in a collection

```sh
$ zotero-cli count --filter "collections:biblio"
123
```

- List values for a given field

```sh
$ zotero-cli list itemType

    Type             
    ----             
    computer program 
    conference paper 
    document         
    journal article  
    manuscript       
    thesis           
    webpage          

```

- Show entries with the given set of fields, filtered based on multiple critera and limited to a given number of items

```sh
$ zotero-cli show year title itemType numPages --filter "collections:biblio" --filter "title:detect" --limit ">date:10"

    Year  Title                                                                                                                             Type              #Pages 
    ----  -----                                                                                                                             ----              ------ 
    2016  Classifying Packed Programs as Malicious Software Detected                                                                        conference paper  3      
    2016  Detecting Packed Executable File: Supervised or Anomaly Detection Method?                                                         conference paper  5      
    2016  Entropy analysis to classify unknown packing algorithms for malware detection                                                     conference paper  21     
    2017  Packer Detection for Multi-Layer Executables Using Entropy Analysis                                                               journal article   18     
    2018  Sensitive system calls based packed malware variants detection using principal component initialized MultiLayers neural networks  journal article   13     
    2018  Effective, efficient, and robust packing detection and classification                                                             journal article   15     
    2019  Efficient automatic original entry point detection                                                                                journal article   14     
    2019  All-in-One Framework for Detection, Unpacking, and Verification for Malware Analysis                                              journal article   16     
    2020  Experimental Comparison of Machine Learning Models in Malware Packing Detection                                                   conference paper  3      
    2020  Building a smart and automated tool for packed malware detections using machine learning                                          thesis            99     

```

- Export entries

```sh
$ zotero-cli export year title itemType numPages --filter "collections:biblio" --filter "title:detect" --limit ">date:10"
$ file export.xlsx 
export.xlsx: Microsoft Excel 2007+

```

- Use a predefined query

```sh
$ zotero-cli show - --query "top-50-most-relevants"
```

> **Note**: "`-`" is used for the `field` positional argument to tell the tool to select the predefined list of fields included in the query.

This is equivalent to:

```sh
$ zotero-cli show year title numPages itemType --limit ">rank:50"
```

Available queries:
- `no-attachment`: list of all items with no attachment ; displayed fields: `title`
- `no-url`: list of all items with no URL ; displayed fields: `year`, `title`
- `top-10-most-relevants`: top-10 best ranked items ; displayed fields: `year`, `title`, `numPages`, `itemType`
- `top-50-most-relevants`: same as top-10 but with the top-50

- Mark items

```sh
$ zotero-cli mark read --filter "title:a nice paper"
$ zotero-cli mark unread --filter "title:a nice paper"
```

> **Markers**:
> 
> - `read` / `unread`: by default, items are displayed in bold ; marking an item as read will make it display as normal
> - `irrelevant` / `relevant`: this allows to exclude a result from the output list of items
> - `ignore` / `unignore`: this allows to completely ignore an item, including in the ranking algorithm


## :bulb: Special Features

Some additional fields can be used for listing/filtering/showing/exporting data.

- Computed fields

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

- Extracted fields (from the `extra` field)

  - `comments`: custom field for adding comments
  - `results`: custom field for mentioning results related to the item
  - `what`: custom field for a short description of what the item is about
  - `zscc`: number of Scholar citations, computed with the [Zotero Google Scholar Citations](https://github.com/beloglazov/zotero-scholar-citations) plugin

- PageRank-based reference ranking algorithm

  - `rank`: computed field aimed to rank references in order of relevance ; this uses an algorithm similar to Google's PageRank while weighting references in function of their year of publication (giving more importance to recent references, which cannot have as much citations as older references anyway)


## :clap:  Supporters

[![Stargazers repo roster for @dhondta/zotero-cli](https://reporoster.com/stars/dark/dhondta/zotero-cli)](https://github.com/dhondta/zotero-cli/stargazers)

[![Forkers repo roster for @dhondta/zotero-cli](https://reporoster.com/forks/dark/dhondta/zotero-cli)](https://github.com/dhondta/zotero-cli/network/members)

<p align="center"><a href="#"><img src="https://img.shields.io/badge/Back%20to%20top--lightgrey?style=social" alt="Back to top" height="20"/></a></p>
