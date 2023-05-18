# -*- coding: UTF-8 -*-
"""Zotero-CLI package information.

"""
import os


__author__ = "Alexandre D'Hondt"
__email__  = "alexandre.dhondt@gmail.com"
__source__ = "https://github.com/dhondta/zotero-cli"

with open(os.path.join(os.path.dirname(__file__), "VERSION.txt")) as f:
    __version__ = f.read().strip()

