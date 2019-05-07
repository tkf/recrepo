# Resources:
# * https://docs.pytest.org/en/latest/fixture.html
# * https://docs.pytest.org/en/latest/tmpdir.html

import json
import os
import sys
from pathlib import Path
from subprocess import PIPE, run

import pytest

import recrepo


def call_cli(*args, cwd=None, **kwargs):
    assert cwd is None  # not supporting changing directory ATM

    kw = dict(stdout=PIPE, stderr=PIPE, universal_newlines=True, input="", check=True)
    kw.update(kwargs)
    proc = run([sys.executable, recrepo.__file__] + list(args), **kw)

    outpath = Path("recrepo.json")
    if outpath.exists():
        with open(str(outpath)) as file:
            states = json.load(file)
    else:
        states = None

    return (proc, states)


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
    path.mkdir()
    kwargs = dict(cwd=str(path))
    git("init", **kwargs)
    git("commit", "--message", "Initial commit", "--allow-empty", **kwargs)
    return path


@pytest.fixture
def gitrepo(tmp_path):
    yield make_gitrepo(tmp_path / "repo0")


@pytest.fixture
def cleancwd(tmp_path):
    cwd_orig = os.getcwd()
    p = tmp_path / "cleancwd"
    p.mkdir()
    os.chdir(str(p))
    yield
    os.chdir(cwd_orig)


def assert_sha1(revision):
    assert isinstance(revision, str)
    assert revision.isalnum()
    assert len(revision) == 40


def assert_repostate(dct):
    assert set(dct) == {"is_clean", "revision", "toplevel"}
    assert dct["is_clean"] in (True, False)
    assert_sha1(dct["revision"])


def assert_repostate_list(dicts, length):
    for d in dicts:
        assert_repostate(d)
    assert len(dicts) == length


def test_clean_one_repo(cleancwd, gitrepo):
    proc, states = call_cli(str(gitrepo))
    assert_repostate_list(states, length=1)
    assert states[0]["toplevel"] == str(gitrepo)
    assert states[0]["is_clean"]
    assert not proc.stderr


def test_clean_two_repos(cleancwd, tmp_path):
    repo1 = make_gitrepo(tmp_path / "repo1")
    repo2 = make_gitrepo(tmp_path / "repo2")
    proc, states = call_cli(str(repo1), str(repo2))
    assert_repostate_list(states, length=2)
    assert states[0]["toplevel"] == str(repo1)
    assert states[1]["toplevel"] == str(repo2)
    assert states[0]["is_clean"]
    assert states[1]["is_clean"]
    assert not proc.stderr


def test_dirty_one_repo_ignore_dirty(cleancwd, gitrepo):
    (gitrepo / "spam").touch()
    proc, states = call_cli("--ignore-dirty", str(gitrepo))
    assert_repostate_list(states, length=1)
    assert states[0]["toplevel"] == str(gitrepo)
    assert not states[0]["is_clean"]
    assert not proc.stderr


def test_dirty_two_repos_ignore_dirty(cleancwd, tmp_path):
    repo1 = make_gitrepo(tmp_path / "repo1")
    repo2 = make_gitrepo(tmp_path / "repo2")
    (repo1 / "spam").touch()
    (repo2 / "spam").touch()
    proc, states = call_cli("--ignore-dirty", str(repo1), str(repo2), check=False)
    assert_repostate_list(states, length=2)
    assert states[0]["toplevel"] == str(repo1)
    assert states[1]["toplevel"] == str(repo2)
    assert not states[0]["is_clean"]
    assert not states[1]["is_clean"]
    assert not proc.stderr


def test_one_clean_one_dirty_repos_ignore_dirty(cleancwd, tmp_path):
    repo1 = make_gitrepo(tmp_path / "repo1")
    repo2 = make_gitrepo(tmp_path / "repo2")
    (repo1 / "spam").touch()
    proc, states = call_cli("--ignore-dirty", str(repo1), str(repo2), check=False)
    assert_repostate_list(states, length=2)
    assert states[0]["toplevel"] == str(repo1)
    assert states[1]["toplevel"] == str(repo2)
    assert not states[0]["is_clean"]
    assert states[1]["is_clean"]
    assert not proc.stderr


def test_dirty_one_repo(cleancwd, gitrepo):
    (gitrepo / "spam").touch()
    proc, _ = call_cli(str(gitrepo), check=False)
    assert proc.returncode == 113
    assert "1 dirty repository found:" in proc.stderr


def test_dirty_two_repos(cleancwd, tmp_path):
    repo1 = make_gitrepo(tmp_path / "repo1")
    repo2 = make_gitrepo(tmp_path / "repo2")
    (repo1 / "spam").touch()
    (repo2 / "spam").touch()
    proc, _ = call_cli(str(repo1), str(repo2), check=False)
    assert proc.returncode == 113
    assert "2 dirty repositories found:" in proc.stderr


def test_one_clean_one_dirty_repos(cleancwd, tmp_path):
    repo1 = make_gitrepo(tmp_path / "repo1")
    repo2 = make_gitrepo(tmp_path / "repo2")
    (repo1 / "spam").touch()
    proc, _ = call_cli(str(repo1), str(repo2), check=False)
    assert proc.returncode == 113
    assert "1 dirty repository found:" in proc.stderr
