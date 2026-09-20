import importlib

from ratch.registry import discover
from ratch.result import State
from ratch.testing import FakeWorkspace, assert_bites

NoAutocloseKeywords = importlib.import_module(
    "ratch.checks.autoclose"
).NoAutocloseKeywords


def no_autoclose_keywords_should_fail_when_a_commit_closes_an_issue():
    ws = FakeWorkspace(files={'a.py': 'x = 1\n'}, git_log_text='Fixes #12\n\x1e')

    found = NoAutocloseKeywords().check(ws).state

    expected = State.FAIL

    assert found is expected


def no_autoclose_keywords_should_pass_when_messages_are_plain():
    ws = FakeWorkspace(files={'a.py': 'x = 1\n'}, git_log_text='tighten the parser\n\x1e')

    found = NoAutocloseKeywords().check(ws).state

    expected = State.PASS

    assert found is expected


def no_autoclose_keywords_should_bite_its_plants_when_checked_against_its_own_fixture(tmp_path):
    check = NoAutocloseKeywords()

    assert_bites(check, tmp_path)

    assert check.id


def no_autoclose_keywords_should_be_discoverable_when_registered_as_an_entry_point():
    catalog = discover()

    loaded = catalog.get("no-autoclose-keywords-in-commits")

    assert loaded is NoAutocloseKeywords
