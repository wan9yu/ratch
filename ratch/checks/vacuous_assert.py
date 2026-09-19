"""No-vacuous-assert check."""
from __future__ import annotations

import re

from ratch.check import Plant
from ratch.result import Finding, Result, State
from ratch.testing import FakeWorkspace

_RX = re.compile(r"^\s*assert (?:True|False)\s*(?:#.*)?$")


def _is_test_py(path):
    return path.endswith(".py") and (
        path.startswith("tests/") or "/tests/" in path
    )


class NoVacuousAssert:
    """Forbid placeholder assert True/False in tests.

    Rule:
        No tracked tests/*.py line may be a message-less assert True or
        assert False.

    Why:
        A placeholder assert proves nothing and can hide a missing
        check; the fail-path form with a message and assert x is True
        remain allowed.

    Proven in:
        this repository

    Not this:
        Not a ban on assert False with a reason, nor on assert x is True.
    """

    id = "no-vacuous-assert"
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
            for line in ws.read(path).splitlines():
                if _RX.search(line):
                    anchor = " ".join(line.split())
                    findings.append(
                        Finding(self.id, path, anchor,
                                message=f"vacuous assert: {anchor}")
                    )
        return Result(
            self.id, self._state(findings, examined_n),
            examined_n=examined_n, skipped_n=ws.skipped_n, findings=findings,
        )

    def plants(self, ws):
        line = "assert True"
        yield Plant(
            label="assert-true",
            planted_ws=FakeWorkspace(files={"tests/t.py": line + "\n"}),
            expected=(self.id, "tests/t.py", line),
        )

    def fixture(self, kit):
        return FakeWorkspace(files={"tests/t.py": "assert value is True\n"})
