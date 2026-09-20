from subprocess import CompletedProcess

from ratch.checks.ai_signatures import NoAiSignatures
from ratch.result import State
from ratch.testing import FakeWorkspace, assert_bites

# git renders `--format="...%B%x00"` as `sha\0an\0ae\0cn\0ce\0body\0`
# per commit, joining records with "\n"; this mirrors those exact bytes so
# the same parser runs against the fake and the real Workspace.
def _log(*commits):
    recs = ["\x00".join(c) + "\x00" for c in commits]
    return "\n".join(recs) + "\n"


def _not_shallow():
    return {("git", "rev-parse", "--is-shallow-repository"):
            CompletedProcess([], 0, stdout="false\n")}


def no_ai_signatures_should_fail_when_a_co_author_trailer_is_in_history():
    sha = "1a2b3c4d5e6f7a8b"
    body = "feat: thing\n\nCo-Authored-By: Bot <bot@example.test>\n"
    ws = FakeWorkspace(
        files={"ok.py": "x = 1\n"},
        run_table=_not_shallow(),
        git_log_text=_log((sha, "Dev", "dev@example.test", "Dev", "dev@example.test", body)),
    )

    result = NoAiSignatures().check(ws)

    assert result.state is State.FAIL
    assert any(
        f.identity == ("no-ai-signatures", "<commit>", f"{sha[:9]}:Co-Authored-By:")
        for f in result.findings
    )


def no_ai_signatures_should_fail_when_a_robot_emoji_appears_in_an_author_name():
    sha = "9f8e7d6c5b4a3210"
    robot = "\N{ROBOT FACE}"
    ws = FakeWorkspace(
        files={"ok.py": "x = 1\n"},
        run_table=_not_shallow(),
        git_log_text=_log((sha, f"{robot} agent", "a@example.test",
                           "Dev", "d@example.test", "chore: tick\n")),
    )

    result = NoAiSignatures().check(ws)

    assert result.state is State.FAIL
    assert any(
        f.identity == ("no-ai-signatures", "<commit>", f"{sha[:9]}:{robot}")
        for f in result.findings
    )


def no_ai_signatures_should_pass_when_history_carries_no_attribution_shape():
    ws = FakeWorkspace(
        files={"ok.py": "x = 1\n"},
        run_table=_not_shallow(),
        git_log_text=_log(("abc123abc123", "Dev", "dev@example.test",
                           "Dev", "dev@example.test", "feat: initial\n")),
    )

    result = NoAiSignatures().check(ws)

    assert result.state is State.PASS
    assert result.findings == []


def no_ai_signatures_should_be_vacuous_when_the_repo_is_shallow():
    sha = "deadbeef0badf00d"
    trailer = "feat: x\n\nCo-Authored-By: Bot <bot@example.test>\n"
    ws = FakeWorkspace(
        files={"ok.py": "x = 1\n"},
        run_table={("git", "rev-parse", "--is-shallow-repository"):
                   CompletedProcess([], 0, stdout="true\n")},
        git_log_text=_log((sha, "Dev", "dev@example.test", "Dev", "dev@example.test", trailer)),
    )

    result = NoAiSignatures().check(ws)

    assert result.state is State.VACUOUS
    assert result.examined_n == 0
    assert result.findings == []


def no_ai_signatures_should_fail_when_trailer_uses_github_lowercase_casing():
    sha = "0badc0de0badc0de"
    body = "feat: thing\n\nCo-authored-by: Bot <bot@example.test>\n"
    ws = FakeWorkspace(
        files={"ok.py": "x = 1\n"},
        run_table=_not_shallow(),
        git_log_text=_log((sha, "Dev", "dev@example.test", "Dev", "dev@example.test", body)),
    )

    result = NoAiSignatures().check(ws)

    assert result.state is State.FAIL


def no_ai_signatures_should_bite_on_every_plant_when_checked_against_its_own_fixture(tmp_path):
    check = NoAiSignatures()

    assert_bites(check, tmp_path)

    assert check.id
