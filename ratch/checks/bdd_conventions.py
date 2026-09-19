"""BDD test-naming check."""
from __future__ import annotations

import ast

from ratch.check import Plant
from ratch.checks import is_test_py
from ratch.result import Finding, Result, State
from ratch.testing import FakeWorkspace


def _is_bdd_name(name):
    if name.startswith("test_"):
        return False
    if "_should_" not in name or "_when_" not in name:
        return False
    return "or" not in name.split("_")


class BddTestConventions:
    """Require BDD test names in tracked test modules.

    Rule:
        In tracked tests/*.py, every top-level def whose name does not
        start with underscore must contain _should_ and _when_, must not
        start with test_, and must not use or as a snake_case segment.

    Why:
        A test name that reads as a sentence is the readable spec; a
        machine can prove the shape so pytest collection and review
        share one convention.

    Proven in:
        A test name reads as subject_should_outcome_when_condition,
        with no test_ prefix and no or segment.

    Not this:
        Not a requirement on private helpers. Not a ban on tokens that
        merely contain the letters o-r (error, format). Not a change to
        pytest python_functions.
    """

    id = "bdd-test-conventions"
    tier = "A"
    kind = "gate"
    scope = "global"
    proven_in = ()
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
            if not is_test_py(path):
                continue
            examined_n += 1
            tree = ws.ast(path)
            if tree is None:
                continue
            for node in tree.body:
                if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    continue
                name = node.name
                if name.startswith("_"):
                    continue
                if not _is_bdd_name(name):
                    findings.append(
                        Finding(self.id, path, name,
                                message=f"bdd name: {name}")
                    )
        return Result(
            self.id, self._state(findings, examined_n),
            examined_n=examined_n, skipped_n=ws.skipped_n,
            unparseable_n=ws.unparseable_n, findings=findings,
        )

    def plants(self, ws):
        yield Plant(
            label="test-prefix",
            planted_ws=FakeWorkspace(
                files={"tests/t.py": "def test_foo():\n    pass\n"}
            ),
            expected=(self.id, "tests/t.py", "test_foo"),
        )
        yield Plant(
            label="or-segment",
            planted_ws=FakeWorkspace(
                files={"tests/t.py": "def foo_should_pass_or_fail_when_x():\n    pass\n"}
            ),
            expected=(self.id, "tests/t.py", "foo_should_pass_or_fail_when_x"),
        )

    def fixture(self, kit):
        return FakeWorkspace(
            files={"tests/t.py": "def foo_should_bar_when_baz():\n    pass\n"}
        )
