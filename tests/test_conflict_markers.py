import importlib

from ratch.result import State
from ratch.testing import FakeWorkspace, assert_bites

NoConflictMarkers = importlib.import_module(
    "ratch.checks.conflict_markers"
).NoConflictMarkers

_START = "<" * 7


def no_conflict_markers_should_fail_when_a_file_has_a_git_start_marker():
    ws = FakeWorkspace(files={"a.py": _START + " HEAD\nx = 1\n"})

    result = NoConflictMarkers().check(ws)

    assert result.state is State.FAIL
    assert any(
        f.identity == ("no-conflict-markers", "a.py", _START + " HEAD")
        for f in result.findings
    )


def no_conflict_markers_should_pass_when_markdown_has_a_setext_underline():
    ws = FakeWorkspace(files={"doc.md": "Title\n=======\n"})

    result = NoConflictMarkers().check(ws)

    assert result.state is State.PASS


def no_conflict_markers_should_bite_its_plants_when_checked_against_its_own_fixture(tmp_path):
    check = NoConflictMarkers()

    assert_bites(check, tmp_path)

    assert check.id


def no_conflict_markers_should_be_discoverable_when_registered_as_an_entry_point():
    from ratch.registry import discover

    found = discover().get('no-conflict-markers')

    expected = NoConflictMarkers

    assert found is expected
