import importlib

from ratch.result import State
from ratch.testing import FakeWorkspace, assert_bites

TodoHasIssueRef = importlib.import_module("ratch.checks.todo_issue").TodoHasIssueRef
_DEBT = "TO" + "DO"


def todo_has_issue_ref_should_fail_when_a_debt_marker_lacks_a_ticket():
    line = _DEBT + " fix this"
    ws = FakeWorkspace(files={"a.py": line + "\n"})
    result = TodoHasIssueRef().check(ws)
    assert result.state is State.FAIL
    assert any(
        f.identity == ("todo-has-issue-ref", "a.py", line)
        for f in result.findings
    )


def todo_has_issue_ref_should_pass_when_a_debt_marker_cites_a_ticket():
    ws = FakeWorkspace(files={"a.py": _DEBT + " fix this (#12)\n"})
    result = TodoHasIssueRef().check(ws)
    assert result.state is State.PASS


def todo_has_issue_ref_should_bite_its_plants_when_checked_against_its_own_fixture(tmp_path):
    assert_bites(TodoHasIssueRef(), tmp_path)


def todo_has_issue_ref_should_be_discoverable_when_registered_as_an_entry_point():
    from ratch.registry import discover
    assert discover().get("todo-has-issue-ref") is TodoHasIssueRef
