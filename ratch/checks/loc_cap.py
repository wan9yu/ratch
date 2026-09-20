"""loc-cap check."""
from ratch.check import Plant
from ratch.result import Finding, Result, State
from ratch.testing import FakeWorkspace


class LocCap:
    """Cap tracked Python modules at a line budget.

    Rule:
        No tracked *.py file may exceed max_lines physical lines.

    Why:
        A module that grows without bound hides complexity; a flat cap
        is a fact, not a smell score.

    Proven in:
        Line count of tracked Python files against a constructor
        ceiling (default 1000).

    Not this:
        Not cyclomatic complexity. Not a growth heatmap.
    """

    id = "loc-cap"
    tier = "A"
    kind = "gate"
    scope = "global"
    proven_in = ()
    confidence = "inferred"
    tolerates_unparseable = False

    def __init__(self, min_surface=1, max_lines=1000):
        if min_surface < 1:
            raise ValueError("min_surface must be >= 1")
        self.min_surface = min_surface
        self.max_lines = max_lines

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
            if not path.endswith(".py"):
                continue
            examined_n += 1
            n = ws.read(path).count("\n")
            if not ws.read(path).endswith("\n") and ws.read(path):
                n += 1
            if n > self.max_lines:
                findings.append(
                    Finding(self.id, path, str(n),
                            message=f"loc {n} > {self.max_lines}")
                )
        return Result(
            self.id, self._state(findings, examined_n),
            examined_n=examined_n, skipped_n=ws.skipped_n, findings=findings,
        )

    def plants(self, ws):
        blob = "x = 1\n" * (self.max_lines + 1)
        yield Plant(
            label="over-cap",
            planted_ws=FakeWorkspace(files={"a.py": blob}),
            expected=(self.id, "a.py", str(self.max_lines + 1)),
        )

    def fixture(self, kit):
        return FakeWorkspace(files={"a.py": "x = 1\n"})
