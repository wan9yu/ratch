from ratch.checks.forbidden_literal import NoForbiddenLiteral
from ratch.result import State
from ratch.testing import FakeWorkspace, assert_bites


def no_forbidden_literal_should_fail_when_the_literal_is_in_tracked_content():
    banned = "cl" + "aude"
    ws = FakeWorkspace(files={"pkg/mod.py": banned + "\n"})

    result = NoForbiddenLiteral().check(ws)

    assert result.state is State.FAIL
    assert any(
        f.identity == ("no-forbidden-literal", "pkg/mod.py", banned)
        for f in result.findings
    )


def no_forbidden_literal_should_fail_when_the_literal_is_in_a_tracked_filename():
    banned = "cl" + "aude"
    path = f"pkg/{banned}_helper.py"
    ws = FakeWorkspace(files={path: "x = 1\n"})

    result = NoForbiddenLiteral().check(ws)

    assert result.state is State.FAIL
    assert any(
        f.identity == ("no-forbidden-literal", path, path)
        for f in result.findings
    )


def no_forbidden_literal_should_fail_when_the_literal_is_in_the_committer_email():
    banned = "cl" + "aude"
    email = banned + "@example.test"
    ws = FakeWorkspace(
        files={"ok.py": "x = 1\n"},
        identity={"name": "Dev", "email": email, "subject": "init", "body": ""},
    )

    result = NoForbiddenLiteral().check(ws)

    assert result.state is State.FAIL
    assert any(
        f.identity == ("no-forbidden-literal", "<commit>", f"email:{email}")
        for f in result.findings
    )


def no_forbidden_literal_should_pass_when_the_tree_is_clean():
    ws = FakeWorkspace(
        files={"pkg/mod.py": "x = 1\n"},
        identity={"name": "Dev", "email": "dev@example.test",
                  "subject": "init", "body": ""},
    )

    result = NoForbiddenLiteral().check(ws)

    assert result.state is State.PASS
    assert result.findings == []


def no_forbidden_literal_should_bite_on_every_plant_when_checked_against_its_own_fixture(tmp_path):
    check = NoForbiddenLiteral()

    assert_bites(check, tmp_path)

    assert check.id
