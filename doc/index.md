## Introduction

This Tinyscript tool aims to manipulate Zotero references, relying on [`pyzotero`](https://github.com/urschrei/pyzotero), applying simple filtering if needed, in order to:

- Count items
- List field values (e.g. for spotting bad values)
- Show items in the terminal, given a set of fields
- Export items to an Excel file, given a set of fields

Quick example:

``` sh
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

-----

## System Requirements

- **Platform**: Linux
- **Python**: 2 or 3

-----

## Installation

This tool is available on [PyPi](https://pypi.python.org/pypi/zotero-cli-tool/) (DO NOT confuse with this [package](https://pypi.python.org/pypi/zotero-cli/), this another related tool) and can be simply installed using Pip via `pip install zotero-cli-tool`.

