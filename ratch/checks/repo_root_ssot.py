"""tests-repo-root-ssot check."""
import re

from ratch.check import Plant
from ratch.checks import is_test_py
from ratch.result import Finding, Result, State
from ratch.testing import FakeWorkspace

_RX = re.compile(
    r"__file__.*(?:parent\.parent|\.parents\s*\[)"
    r"|(?:parent\.parent|\.parents\s*\[).*__file__"
)


class RepoRootSSot:
    """Require tests to import one repository-root helper.

    Rule:
        Tracked tests/*.py other than the configured ssot module must
        not compute the repo root from __file__ via parent.parent or
        .parents[N].

    Why:
        Seven copies of Path(__file__).parent.parent drift independently;
        one helper is the SSOT.

    Proven in:
        A regex over test modules; the ssot file is the one allowed to
        walk parents.

    Not this:
        Not a full pathlib SSOT. Not a ban on Path(__file__) for a
        fixture next to the test. Importing the helper PASSes.
    """

    id = "tests-repo-root-ssot"
    tier = "A"
    kind = "gate"
    scope = "global"
    proven_in = ()
    confidence = "inferred"
    tolerates_unparseable = False

    def __init__(self, min_surface=1, ssot="tests/repo_root.py"):
        if min_surface < 1:
            raise ValueError("min_surface must be >= 1")
        self.min_surface = min_surface
        self.ssot = ssot

    def _state(self, findings, examined_n):
        if findings:
            return State.FAIL
        if examined_n < self.min_surface:
            return State.VACUOUS
        return State.PASS

    def check(self, ws):
        findings = []
        examined_n = 0
        for path in ws.tracked_files():
            if not is_test_py(path):
                continue
            if path == self.ssot:
                continue
            examined_n += 1
            text = ws.read(path)
            if _RX.search(text):
                findings.append(
                    Finding(self.id, path, "parent.parent",
                            message="repo root walked from __file__")
                )
        return Result(
            self.id, self._state(findings, examined_n),
            examined_n=examined_n, skipped_n=ws.skipped_n, findings=findings,
        )

    def plants(self, ws):
        src = "root = pathlib.Path(__file__).resolve().parent.parent\n"
        yield Plant(
            label="walk",
            planted_ws=FakeWorkspace(files={"tests/t.py": src}),
            expected=(self.id, "tests/t.py", "parent.parent"),
        )

    def fixture(self, kit):
        return FakeWorkspace(files={
            "tests/repo_root.py": "ROOT = 1\n",
            "tests/t.py": "from tests.repo_root import ROOT\n",
        })
