from ratch.checks.first_person import NoFirstPerson
from ratch.result import State
from ratch.testing import FakeWorkspace, assert_bites


def no_first_person_should_fail_when_a_prose_line_says_we():
    ws = FakeWorkspace(files={"doc.md": "Here we shipped it.\n"})
    result = NoFirstPerson().check(ws)
    assert result.state is State.FAIL
    assert any(
        f.identity == ("no-first-person", "doc.md", "Here we shipped it.")
        for f in result.findings
    )


def no_first_person_should_fail_when_a_prose_line_says_capital_i():
    ws = FakeWorkspace(files={"doc.md": "Then I decided.\n"})
    result = NoFirstPerson().check(ws)
    assert result.state is State.FAIL
    assert result.findings[0].line == 1


def no_first_person_should_fail_when_a_prose_line_says_our():
    ws = FakeWorkspace(files={"doc.md": "This is our plan.\n"})
    result = NoFirstPerson().check(ws)
    assert result.state is State.FAIL
    assert any(
        f.identity == ("no-first-person", "doc.md", "This is our plan.")
        for f in result.findings
    )


def no_first_person_should_fail_when_a_prose_line_says_us():
    ws = FakeWorkspace(files={"doc.md": "It helps us ship.\n"})
    result = NoFirstPerson().check(ws)
    assert result.state is State.FAIL
    assert any(
        f.identity == ("no-first-person", "doc.md", "It helps us ship.")
        for f in result.findings
    )


def no_first_person_should_pass_when_prose_is_impersonal():
    ws = FakeWorkspace(files={"README.md": "The ratchet turns one way.\n"})
    result = NoFirstPerson().check(ws)
    assert result.state is State.PASS
    assert result.findings == []


def no_first_person_should_be_vacuous_when_no_prose_file_is_in_scope():
    ws = FakeWorkspace(files={"src/mod.py": "we = 1  # code, not prose\n"})
    result = NoFirstPerson().check(ws)
    assert result.state is State.VACUOUS
