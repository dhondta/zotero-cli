[![PyPi](https://img.shields.io/pypi/v/zotero-cli-tool.svg)](https://pypi.python.org/pypi/zotero-cli-tool/)
![Platform](https://img.shields.io/badge/platform-linux-yellow.svg)
[![Read The Docs](https://readthedocs.org/projects/zotero-cli/badge/?version=latest)](http://zotero-cli.readthedocs.io/en/latest/?badge=latest)
[![Known Vulnerabilities](https://snyk.io/test/github/dhondta/zotero-cli/badge.svg?targetFile=requirements.txt)](https://snyk.io/test/github/dhondta/zotero-cli?targetFile=requirements.txt)
[![Requirements Status](https://requires.io/github/dhondta/zotero-cli/requirements.svg?branch=main)](https://requires.io/github/dhondta/zotero-cli/requirements/?branch=main)
[![License](https://img.shields.io/pypi/l/zotero-cli-tool.svg)](https://pypi.python.org/pypi/zotero-cli-tool/)

## Table of Contents

- [Introduction](#introduction)
- [Setup](#setup)
- [Quick Start](#quick-start)
- [Special Features](#special-features)


## Introduction

This Tinyscript tool relies on [`pyzotero`](https://github.com/urschrei/pyzotero) for communicating with [Zotero's Web API](https://www.zotero.org/support/dev/web_api/v3/start). It allows to list field values, show items in tables in the CLI or also export sorted items to an Excel file.


## Setup

```session
$ pip install zotero-cli-tool
```

> **Behind a proxy ?**
> 
> Do not forget to add option `--proxy=http://[user]:[pwd]@[host]:[port]` to your pip command.


## Quick Start

The first time you start it, the tool will ask for your API identifier and key. It will cache it to `~/.zotero/creds.txt` this persmissions set to `rw` for your user only. Data is cached to `~/.zotero/cache/`.

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


## Special Features

Some additional fields can be used for listing/filtering/showing/exporting data.

- Computed fields

  - `citations`: the number of relations the item has to other items with a later date
  - `numAttachments`: the number of child items with `itemType` equal to `attachment`
  - `numAuthors`: the number of `creators` with `creatorType` equal to `author`
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

