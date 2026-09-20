import importlib

from ratch.registry import discover
from ratch.result import State
from ratch.testing import FakeWorkspace, assert_bites

NoReassuranceWords = importlib.import_module(
    "ratch.checks.reassurance"
).NoReassuranceWords


def no_reassurance_words_should_fail_when_markdown_soothes_the_reader():
    phrase = "".join(["放", "心"])

    ws = FakeWorkspace(files={"note.md": phrase + "\n"})

    result = NoReassuranceWords().check(ws)
    assert result.state is State.FAIL


def no_reassurance_words_should_pass_when_markdown_is_plain():
    ws = FakeWorkspace(files={'note.md': 'a machine can prove it.\n'})

    found = NoReassuranceWords().check(ws).state

    expected = State.PASS

    assert found is expected


def no_reassurance_words_should_bite_its_plants_when_checked_against_its_own_fixture(tmp_path):
    check = NoReassuranceWords()

    assert_bites(check, tmp_path)

    assert check.id


def no_reassurance_words_should_be_discoverable_when_registered_as_an_entry_point():
    catalog = discover()

    loaded = catalog.get("no-reassurance-words")

    assert loaded is NoReassuranceWords
