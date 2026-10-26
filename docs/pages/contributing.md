# Contributing

Contributions are welcome.

## Reporting issues

Open an issue on [GitHub](https://github.com/dhondta/zotero-cli/issues) and include:

- the Zotero CLI version (`zotero-cli --help` prints it) and the Python version;
- the exact command and its output, ideally with `-v`.

## Security

Please do **not** report vulnerabilities in public issues. See the [security policy](https://github.com/dhondta/zotero-cli/blob/main/SECURITY.md): report them privately through the repository's *Security* tab (*Report a vulnerability*).

Dependencies are monitored by Dependabot and audited with [pip-audit](https://github.com/pypa/pip-audit) by the `security` workflow (`.github/workflows/security.yml`), on every push and pull request to `main` and weekly.

## Development setup

```console
$ git clone https://github.com/dhondta/zotero-cli
$ cd zotero-cli
$ pip install -e .
$ pip install flake8
$ flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics
```

CI (`.github/workflows/publish-package.yml`) installs the package on Python 3.9 to 3.13 and runs this flake8 check.

## Releasing

The version is stored in `src/zotero/VERSION.txt`. On every push to `main`, CI checks whether that version is already on PyPI. If not, it builds the package and publishes it.

## Building this documentation

```console
$ pip install -r docs/requirements.txt
$ mkdocs serve -f docs/mkdocs.yml          # live preview at http://127.0.0.1:8000
$ mkdocs build --strict -f docs/mkdocs.yml # what Read the Docs runs
```

Read the Docs builds the site from `.readthedocs.yaml` at the root of the repository.
