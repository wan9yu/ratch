"""BDD test-naming check."""
from __future__ import annotations

import re

from ratch.check import Plant
from ratch.result import Finding, Result, State
from ratch.testing import FakeWorkspace

_DEF = re.compile(r"^def (\w+)\(", re.M)


def _is_test_py(path):
    return path.endswith(".py") and (
        path.startswith("tests/") or "/tests/" in path
    )


class BddTestConventions:
    """Require BDD test names in tracked test modules.

    Rule:
        In tracked tests/*.py, every top-level def whose name does not
        start with underscore must contain _should_ and _when_, and must
        not start with test_.

    Why:
        A test name that reads as a sentence is the readable spec; a
        machine can prove the shape so pytest collection and review
        share one convention.

    Proven in:
        this repository

    Not this:
        Not a requirement on private helpers. Not a change to pytest
        python_functions.
    """

    id = "bdd-test-conventions"
    tier = "A"
    kind = "gate"
    scope = "global"
    proven_in = ("this repository",)
    confidence = "inferred"
    tolerates_unparseable = False

    def __init__(self, min_surface=1):
        if min_surface < 1:
            raise ValueError("min_surface must be >= 1")
        self.min_surface = min_surface

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
            if not _is_test_py(path):
                continue
            examined_n += 1
            for name in _DEF.findall(ws.read(path)):
                if name.startswith("_"):
                    continue
                if name.startswith("test_") or "_should_" not in name or "_when_" not in name:
                    findings.append(
                        Finding(self.id, path, name,
                                message=f"bdd name: {name}")
                    )
        return Result(
            self.id, self._state(findings, examined_n),
            examined_n=examined_n, skipped_n=ws.skipped_n, findings=findings,
        )

    def plants(self, ws):
        yield Plant(
            label="test-prefix",
            planted_ws=FakeWorkspace(
                files={"tests/t.py": "def test_foo():\n    pass\n"}
            ),
            expected=(self.id, "tests/t.py", "test_foo"),
        )

    def fixture(self, kit):
        return FakeWorkspace(
            files={"tests/t.py": "def foo_should_bar_when_baz():\n    pass\n"}
        )
