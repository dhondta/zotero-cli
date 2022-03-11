#!/usr/bin/env python
# -*- coding: UTF-8 -*-
from os.path import abspath, dirname, join
from setuptools import setup

currdir = abspath(dirname(__file__))
with open(join(currdir, 'README.md')) as f:
    long_descr = f.read()

setup(
  name = "zotero-cli-tool",
  author = "Alexandre D\'Hondt",
  author_email = "alexandre.dhondt@gmail.com",
  url = "https://github.com/dhondta/zotero-cli",
  version = "1.3.0",
  license = "GPLv3",
  description = "Tinyscript tool for sorting and exporting Zotero references based on pyzotero",
  long_description=long_descr,
  long_description_content_type='text/markdown',
  keywords = ["zotero", "citations", "cli-app", "tinyscript"],
  scripts = ["zotero-cli"],
  classifiers = [
    'Development Status :: 4 - Beta',
    'Environment :: Console',
    'Intended Audience :: Science/Research',
    'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
    'Programming Language :: Python :: 2',
    'Programming Language :: Python :: 2.7',
    'Programming Language :: Python :: 3',
    'Programming Language :: Python :: 3.5',
    'Programming Language :: Python :: 3.6',
    'Programming Language :: Python :: 3.7',
    'Programming Language :: Python :: 3.8',
    'Programming Language :: Python :: 3.9',
  ],
  install_requires=["matplotlib", "pyzotero", "tinyscript>=1.25.0", "xlsxwriter"],
  python_requires = '>=2.7,!=3.0.*,!=3.1.*,!=3.2.*,!=3.3.*,!=3.4.*,<4',
)
