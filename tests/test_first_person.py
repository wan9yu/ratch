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


def no_first_person_should_pass_when_a_prose_line_says_i_slash_o():
    ws = FakeWorkspace(files={"doc.md": "The I/O boundary is the sole seam.\n"})

    result = NoFirstPerson().check(ws)

    assert result.state is State.PASS
    assert result.findings == []


def no_first_person_should_pass_when_prose_uses_a_lowercase_i_as_a_variable():
    ws = FakeWorkspace(files={"doc.md": "The loop uses i as its counter.\n"})

    result = NoFirstPerson().check(ws)

    assert result.state is State.PASS


def no_first_person_should_pass_when_prose_says_i_e():
    ws = FakeWorkspace(files={"doc.md": "Use the gate, i.e. the blocking check.\n"})

    result = NoFirstPerson().check(ws)

    assert result.state is State.PASS


def no_first_person_should_pass_when_prose_says_us_as_an_uppercase_acronym():
    ws = FakeWorkspace(files={"doc.md": "The US-ASCII encoding is fine.\n"})

    result = NoFirstPerson().check(ws)

    assert result.state is State.PASS


def no_first_person_should_fail_when_a_prose_line_contains_cjk_self():
    ws = FakeWorkspace(files={"doc.md": "这是我的计划。\n"})

    result = NoFirstPerson().check(ws)

    assert result.state is State.FAIL
    assert any(
        f.identity == ("no-first-person", "doc.md", "这是我的计划。")
        for f in result.findings
    )


def no_first_person_should_pass_on_team_we_cjk_when_polarity_allows_it():
    ws = FakeWorkspace(files={"doc.md": "这是我们的计划。\n"})

    result = NoFirstPerson(polarity="allow-team-we").check(ws)

    assert result.state is State.PASS
    assert result.findings == []


def no_first_person_should_still_fail_when_bare_cjk_self_appears_under_allow_team_we():
    ws = FakeWorkspace(files={"doc.md": "我做的。\n"})

    result = NoFirstPerson(polarity="allow-team-we").check(ws)

    assert result.state is State.FAIL


def no_first_person_should_pass_when_english_we_appears_under_allow_team_we():
    ws = FakeWorkspace(files={"doc.md": "Here we shipped it.\n"})

    result = NoFirstPerson(polarity="allow-team-we").check(ws)

    assert result.state is State.PASS


def no_first_person_should_bite_every_plant_when_checked_against_its_own_fixture(tmp_path):
    check = NoFirstPerson()

    assert_bites(check, tmp_path)

    assert check.id


def no_first_person_should_be_discoverable_when_registered_as_an_entry_point():
    from ratch.registry import discover

    found = discover().get('no-first-person')

    expected = NoFirstPerson

    assert found is expected
