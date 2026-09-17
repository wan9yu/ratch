"""Behavior specs for the 'ratch check' command-line adapter."""
import os

from ratch.cli import main
from ratch.testing import make_tmp_repo


def main_should_return_one_when_the_repo_has_a_violation(tmp_path, monkeypatch):
    banned = "cl" + "aude"
    repo = make_tmp_repo(tmp_path, {"pkg/mod.py": f'MARK = "{banned}"\n'})
    monkeypatch.chdir(repo)
    monkeypatch.setattr(os, "nice", lambda n: None)

    code = main(["check"])

    assert code == 1


def main_should_return_zero_when_the_repo_is_clean(tmp_path, monkeypatch):
    repo = make_tmp_repo(tmp_path, {"pkg/mod.py": "MARK = 'clean'\n"})
    monkeypatch.chdir(repo)
    monkeypatch.setattr(os, "nice", lambda n: None)

    code = main(["check"])

    assert code == 0
