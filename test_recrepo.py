# Resources:
# * https://docs.pytest.org/en/latest/fixture.html
# * https://py.readthedocs.io/en/latest/path.html

from subprocess import run
import os
import sys
import json

import pytest

import recrepo


def call_cli(*args, **kwargs):
    kw = dict(capture_output=True, input="", text=True, check=True)
    kw.update(kwargs)
    return run([sys.executable, recrepo.__file__] + list(args), **kw)


def git(*args, **kwargs):
    kw = dict(check=True)
    kw.update(kwargs)
    return run(
        ["git", "-c", "user.email=test@recrepo", "-c", "user.name=recrepo tester"]
        + list(args),
        **kw
    )
    # See: git-config


def make_gitrepo(path):
    kwargs = dict(cwd=str(path))
    git("init", **kwargs)
    git("commit", "--message", "Initial commit", "--allow-empty", **kwargs)
    return path


@pytest.fixture
def gitrepo(tmpdir):
    cwd_orig = os.getcwd()
    tmpdir.chdir()
    make_gitrepo(tmpdir)
    yield tmpdir
    os.chdir(cwd_orig)


def test_clean_one_repo(gitrepo):
    proc = call_cli(".")
    states = json.loads(proc.stdout)
    assert set(states[0]) == {"is_clean", "revision", "toplevel"}
    assert len(states) == 1
    assert states[0]["toplevel"] == str(gitrepo)
    assert not proc.stderr


def test_clean_two_repos(tmpdir):
    repo1 = make_gitrepo(tmpdir.mkdir("repo1"))
    repo2 = make_gitrepo(tmpdir.mkdir("repo2"))
    proc = call_cli(str(repo1), str(repo2))
    states = json.loads(proc.stdout)
    assert set(states[0]) == {"is_clean", "revision", "toplevel"}
    assert set(states[1]) == {"is_clean", "revision", "toplevel"}
    assert len(states) == 2
    assert states[0]["toplevel"] == str(repo1)
    assert states[1]["toplevel"] == str(repo2)
    assert not proc.stderr


def test_dirty_one_repo(gitrepo):
    gitrepo.join("spam").ensure(file=True)
    proc = call_cli(".", check=False)
    assert proc.returncode == 113
    assert "1 dirty repository found:" in proc.stderr


def test_dirty_two_repos(tmpdir):
    repo1 = make_gitrepo(tmpdir.mkdir("repo1"))
    repo2 = make_gitrepo(tmpdir.mkdir("repo2"))
    repo1.join("spam").ensure(file=True)
    repo2.join("spam").ensure(file=True)
    proc = call_cli(str(repo1), str(repo2), check=False)
    assert proc.returncode == 113
    assert "2 dirty repositories found:" in proc.stderr


def test_one_clean_one_dirty_repos(tmpdir):
    repo1 = make_gitrepo(tmpdir.mkdir("repo1"))
    repo2 = make_gitrepo(tmpdir.mkdir("repo2"))
    repo1.join("spam").ensure(file=True)
    proc = call_cli(str(repo1), str(repo2), check=False)
    assert proc.returncode == 113
    assert "1 dirty repository found:" in proc.stderr
