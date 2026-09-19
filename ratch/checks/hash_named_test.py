"""No-hash-named-test check."""
from __future__ import annotations

import re

from ratch.check import Plant
from ratch.checks import is_test_py
from ratch.result import Finding, Result, State
from ratch.testing import FakeWorkspace

_HEX_STEM = re.compile(r"_[a-f0-9]{6,8}$")


def _stem(path):
    name = path.rsplit("/", 1)[-1]
    if name.endswith(".py"):
        name = name[:-3]
    return name


class NoHashNamedTest:
    """Forbid opaque hex suffixes on test filenames.

    Rule:
        No tracked tests/*.py stem may end in underscore plus 6 to 8
        hex digits.

    Why:
        A truncated hash in a filename is opaque once the commit is
        forgotten; a readable stem stays reviewable.

    Proven in:
        this repository

    Not this:
        Not a ban on hex elsewhere in the path. Not a check on non-test
        modules.
    """

    id = "no-hash-named-test"
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
            if not is_test_py(path):
                continue
            examined_n += 1
            if _HEX_STEM.search(_stem(path)):
                findings.append(
                    Finding(self.id, path, path,
                            message=f"hash-named test: {path}")
                )
        return Result(
            self.id, self._state(findings, examined_n),
            examined_n=examined_n, skipped_n=ws.skipped_n, findings=findings,
        )

    def plants(self, ws):
        path = "tests/test_foo_a1b2c3d4.py"
        yield Plant(
            label="hex-stem",
            planted_ws=FakeWorkspace(files={path: "x = 1\n"}),
            expected=(self.id, path, path),
        )

    def fixture(self, kit):
        return FakeWorkspace(files={"tests/test_foo.py": "x = 1\n"})
