from subprocess import CompletedProcess

from ratch.checks.ai_signatures import NoAiSignatures
from ratch.result import State
from ratch.testing import FakeWorkspace

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
