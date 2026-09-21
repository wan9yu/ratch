"""BDD test-naming check."""
from __future__ import annotations

import ast

from ratch.check import Plant
from ratch.checks import is_test_py
from ratch.result import Finding, Result, State
from ratch.testing import FakeWorkspace


def _is_bdd_name(name, prefix):
    if prefix and not name.startswith(prefix):
        return None
    if not prefix and name.startswith("test_"):
        return False
    if "_should_" not in name or "_when_" not in name:
        return False
    return "or" not in name.split("_")


def _paragraph_n(node, lines):
    start = node.lineno
    end = node.end_lineno or node.lineno
    body = lines[start:end]
    groups = 0
    in_group = False
    for line in body:
        if line.strip():
            if not in_group:
                groups += 1
                in_group = True
        else:
            in_group = False
    return groups


class BddTestConventions:
    """Require BDD test names in tracked test modules.

    Rule:
        In tracked tests/*.py, selected top-level defs must contain
        _should_ and _when_ and must not use or as a snake_case segment.
        prefix="" (this repo) inspects every public def and forbids a
        test_ prefix. prefix="test_" inspects only that prefix (helpers
        are ignored). blank_blocks=3 requires two blank-line gaps;
        blank_blocks=0 skips body shape. Labels are ignored.

    Why:
        A test name that reads as a sentence is the readable spec; a
        machine can prove the shape so pytest collection and review
        share one convention.

    Proven in:
        A test name reads as subject_should_outcome_when_condition,
        with no test_ prefix and no or segment. Two blank lines in the
        body mark three blocks; no given/when/then labels.

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

    def __init__(self, min_surface=1, prefix="", blank_blocks=3):
        if min_surface < 1:
            raise ValueError("min_surface must be >= 1")
        self.min_surface = min_surface
        self.prefix = prefix
        self.blank_blocks = blank_blocks

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
            lines = ws.read(path).splitlines()
            for node in tree.body:
                if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    continue
                name = node.name
                if name.startswith("_"):
                    continue
                verdict = _is_bdd_name(name, self.prefix)
                if verdict is None:
                    continue
                if not verdict:
                    findings.append(
                        Finding(self.id, path, name,
                                message=f"bdd name: {name}")
                    )
                    continue
                if self.blank_blocks and _paragraph_n(node, lines) < self.blank_blocks:
                    findings.append(
                        Finding(self.id, path, name,
                                message=f"bdd blank: {name}")
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
        body = "\n".join(f"    a{i} = {i}" for i in range(6))
        yield Plant(
            label="dense-body",
            planted_ws=FakeWorkspace(
                files={"tests/t.py": f"def foo_should_bar_when_baz():\n{body}\n"}
            ),
            expected=(self.id, "tests/t.py", "foo_should_bar_when_baz"),
        )

    def fixture(self, kit):
        return FakeWorkspace(
            files={"tests/t.py": (
                "def foo_should_bar_when_baz():\n"
                "    x = 1\n\n"
                "    y = 2\n\n"
                "    assert x\n"
            )}
        )
