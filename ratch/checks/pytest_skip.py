"""No-pytest-skip check."""
from __future__ import annotations

import ast

from ratch.check import Plant
from ratch.checks import is_test_py, match_globs
from ratch.result import Finding, Result, State
from ratch.testing import FakeWorkspace


def _is_pytest_skip(node):
    if not isinstance(node, ast.Call):
        return False
    func = node.func
    return (
        isinstance(func, ast.Attribute)
        and func.attr == "skip"
        and isinstance(func.value, ast.Name)
        and func.value.id == "pytest"
    )


class NoPytestSkip:
    """Forbid pytest.skip in invariant tests.

    Rule:
        Selected tests must not call pytest.skip. paths=None uses
        tests/*.py (this repo's default). Consumers with e2e hardware
        skips should pass paths= for the invariant glob.

    Why:
        skip turns a gate into a silent pass; invariants must fail
        out loud with pytest.fail instead.

    Proven in:
        Invariant tests must fail out loud, never pytest.skip into a
        silent green.

    Not this:
        Not a ban on pytest.fail. Not a ban on e2e environment skips;
        narrow with paths=.
    """

    id = "no-pytest-skip"
    tier = "A"
    kind = "gate"
    scope = "global"
    proven_in = ()
    confidence = "inferred"
    tolerates_unparseable = False

    def __init__(self, min_surface=1, paths=None):
        if min_surface < 1:
            raise ValueError("min_surface must be >= 1")
        self.min_surface = min_surface
        self.paths = None if paths is None else tuple(paths)

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
            if self.paths is None and not is_test_py(path):
                continue
            if not match_globs(path, self.paths):
                continue
            examined_n += 1
            tree = ws.ast(path)
            if tree is None:
                continue
            for node in ast.walk(tree):
                if _is_pytest_skip(node):
                    findings.append(
                        Finding(self.id, path, "pytest.skip",
                                message="pytest.skip in tests")
                    )
        return Result(
            self.id, self._state(findings, examined_n),
            examined_n=examined_n, skipped_n=ws.skipped_n,
            unparseable_n=ws.unparseable_n, findings=findings,
        )

    def plants(self, ws):
        src = "import pytest\npytest.skip('x')\n"
        yield Plant(
            label="pytest-skip",
            planted_ws=FakeWorkspace(files={"tests/t.py": src}),
            expected=(self.id, "tests/t.py", "pytest.skip"),
        )

    def fixture(self, kit):
        return FakeWorkspace(files={"tests/t.py": "assert True is False, 'x'\n"})
