import importlib

from ratch.registry import discover
from ratch.result import State
from ratch.testing import FakeWorkspace, assert_bites

RepoRootSSot = importlib.import_module(
    "ratch.checks.repo_root_ssot"
).RepoRootSSot


def tests_repo_root_ssot_should_fail_when_a_test_walks_file_parents():
    walk = "parent" + ".parent"
    src = "root = pathlib.Path(__" + "file__).resolve()." + walk + "\n"

    result = RepoRootSSot().check(FakeWorkspace(files={"tests/t.py": src}))

    assert result.state is State.FAIL


def tests_repo_root_ssot_should_fail_when_a_test_indexes_file_parents():
    src = "root = pathlib.Path(__" + "file__).resolve().parents[2]\n"

    result = RepoRootSSot().check(FakeWorkspace(files={"tests/t.py": src}))

    assert result.state is State.FAIL


def tests_repo_root_ssot_should_pass_when_tests_import_the_helper():
    ws = FakeWorkspace(files={'tests/repo_root.py': 'ROOT = 1\n', 'tests/t.py': 'from tests.repo_root import ROOT\n'})

    found = RepoRootSSot().check(ws).state

    expected = State.PASS

    assert found is expected


def tests_repo_root_ssot_should_bite_its_plants_when_checked_against_its_own_fixture(tmp_path):
    check = RepoRootSSot()

    assert_bites(check, tmp_path)

    assert check.id


def tests_repo_root_ssot_should_be_discoverable_when_registered_as_an_entry_point():
    catalog = discover()

    loaded = catalog.get("tests-repo-root-ssot")

    assert loaded is RepoRootSSot
