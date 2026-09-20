"""Behavior specs for the ratch command-line adapter."""
import os

from ratch.cli import main
from ratch.registry import discover
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


def main_should_list_discovered_plugins_when_invoked_with_list(
    tmp_path, monkeypatch, capsys,
):
    repo = make_tmp_repo(tmp_path, {"pkg/mod.py": "x = 1\n"})
    monkeypatch.chdir(repo)
    niced = []
    monkeypatch.setattr(os, "nice", lambda n: niced.append(n))

    code = main(["list"])
    out = capsys.readouterr().out
    lines = [line for line in out.splitlines() if line.strip()]
    names = [line.split()[0] for line in lines]

    assert code == 0
    assert niced == []
    assert set(names) == set(discover())
    assert names == sorted(names)
    width = max([24, *(len(name) for name in names)]) + 1
    labels = {}
    for line in lines:
        name, label = line.split()
        assert line == f"{name:<{width}}{label}"
        labels[name] = label
    assert set(labels.values()) <= {"enabled", "catalog"}
    assert labels["no-forbidden-literal"] == "enabled"
    assert labels["no-external-font-cdn"] == "catalog"


def main_should_describe_a_plugin_when_the_id_is_known(monkeypatch, capsys):
    import ratch.cli as cli_mod

    niced = []
    monkeypatch.setattr(os, "nice", lambda n: niced.append(n))

    def boom(*_a, **_k):
        raise AssertionError("Workspace")

    monkeypatch.setattr(cli_mod, "Workspace", boom)

    code = main(["describe", "no-forbidden-literal"])
    out = capsys.readouterr().out

    assert code == 0
    assert niced == []
    assert "Rule:" in out
    assert "Not this:" in out
    sig_lines = [line for line in out.splitlines() if line.startswith("(")]
    assert sig_lines and "self" not in sig_lines[0]


def main_should_return_one_when_the_describe_id_is_unknown(capsys):
    code = main(["describe", "no-such-check"])

    err = capsys.readouterr().err

    assert code == 1
    assert "no-such-check" in err
