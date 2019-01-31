#!/usr/bin/env python3

"""
Record repository status after asserting it's clean.

This script records the status of one or more repositories in a JSON
file (``recrepo.json`` by default).  It also asserts that those
repositories are clean (unless ``--ignore-dirty`` option is given) and
exit with an error code if files that are not tracked by git or not
committed are found.

Examples
--------
::
    recrepo PATH/TO/GIT/REPOSITORY
    recrepo --output=- PATH/TO/GIT/REPOSITORY
    recrepo REPOSITORY_1 REPOSITORY_2
"""

# Copyright 2019, Takafumi Arakaki

# Permission is hereby granted, free  of charge, to any person obtaining
# a  copy  of this  software  and  associated documentation  files  (the
# "Software"), to  deal in  the Software without  restriction, including
# without limitation  the rights to  use, copy, modify,  merge, publish,
# distribute, sublicense,  and/or sell  copies of  the Software,  and to
# permit persons to whom the Software  is furnished to do so, subject to
# the following conditions:

# The  above  copyright  notice  and this  permission  notice  shall  be
# included in all copies or substantial portions of the Software.

# THE  SOFTWARE IS  PROVIDED  "AS  IS", WITHOUT  WARRANTY  OF ANY  KIND,
# EXPRESS OR  IMPLIED, INCLUDING  BUT NOT LIMITED  TO THE  WARRANTIES OF
# MERCHANTABILITY,    FITNESS    FOR    A   PARTICULAR    PURPOSE    AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE
# LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
# OF CONTRACT, TORT OR OTHERWISE, ARISING  FROM, OUT OF OR IN CONNECTION
# WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

__version__ = "0.0.0"
__author__ = "Takafumi Arakaki"
__license__ = "MIT"

from collections import namedtuple
from contextlib import contextmanager
from io import StringIO
from pathlib import Path
import json
import subprocess
import sys


RepoState = namedtuple("RepoState", ["is_clean", "status", "revision", "toplevel"])


def to_record(state):
    r = state._asdict()
    del r["status"]
    return r


def repostate(pointer):
    path = Path(pointer).resolve()
    if not path.is_dir():
        path = path.parent

    def git(*args):
        return subprocess.check_output(
            ["git"] + list(args), universal_newlines=True, cwd=str(path)
        )

    status = git("status", "--short")
    return RepoState(
        is_clean=not status.strip(),
        status=status,
        revision=git("rev-parse", "HEAD").strip(),
        toplevel=git("rev-parse", "--show-toplevel").rstrip(),
    )


class DirtyRepositories(Exception):

    CODE = 113
    """ Exit status when there is an un-clean repository. """
    # Using 113 and below as it seems that's for "users". See:
    # https://www.tldp.org/LDP/abs/html/exitcodes.html

    def __init__(self, repos):
        self.repos = repos

    def __str__(self):
        repos = [r for r in self.repos if not r.is_clean]
        io = StringIO()

        def _print(*args, **kwargs):
            print(*args, file=io, **kwargs)

        _print(
            len(repos),
            "dirty",
            "repositories" if len(repos) > 1 else "repository",
            "found:",
        )
        for r in repos:
            _print()
            _print("*", r.toplevel, "@", r.revision)
            for l in r.status.splitlines():
                _print("|  ", l)

        _print()
        _print("Aborting...", end="")
        return io.getvalue()


def recrepo(pointers, ignore_dirty):
    repos = list(map(repostate, pointers))
    if not ignore_dirty and not all(r.is_clean for r in repos):
        raise DirtyRepositories(repos)
    return list(map(to_record, repos))


@contextmanager
def _openw(path):
    if path == "-":
        yield sys.stdout
    else:
        with open(path, "w") as file:
            yield file


def cli(output, **kwargs):
    try:
        records = recrepo(**kwargs)
        with _openw(output) as file:
            json.dump(records, file, sort_keys=True)
    except DirtyRepositories as err:
        print(err, file=sys.stderr)
        sys.exit(err.CODE)


def main(args=None):
    import argparse

    class CustomFormatter(
        argparse.RawDescriptionHelpFormatter, argparse.ArgumentDefaultsHelpFormatter
    ):
        pass

    parser = argparse.ArgumentParser(
        formatter_class=CustomFormatter, description=__doc__
    )

    parser.add_argument(
        "--ignore-dirty",
        default=False,
        action="store_true",
        help="""
        Ignore repositories with un-committed files.  By default,
        un-committed files result in exit with return code {code}.
        """.format(
            code=DirtyRepositories.CODE
        ),
    )

    parser.add_argument(
        "--output",
        default="recrepo.json",
        help="""
        Path to output JSON file.  "-" means stdout.
        """,
    )
    # Not using `type=argparse.FileType("w")` to avoid creating a file
    # in abort case.

    parser.add_argument(
        "pointers",
        metavar="pointer",
        nargs="+",
        help="""
        Path to a file or directory inside a project.  Multiple paths
        can be given.
        """,
    )

    ns = parser.parse_args(args)
    cli(**vars(ns))


if __name__ == "__main__":
    main()
