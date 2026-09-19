"""No-conflict-markers check."""
from __future__ import annotations

from ratch.check import Plant
from ratch.result import Finding, Result, State
from ratch.testing import FakeWorkspace

_START = "<" * 7
_END = ">" * 7


class NoConflictMarkers:
    """Forbid leftover git conflict markers in tracked files.

    Rule:
        No tracked file may contain a line whose stripped prefix is the
        seven-character git conflict start or end marker.

    Why:
        A leftover conflict marker is an unfinished merge that no
        reviewer reliably catches by eye; a machine can prove absence
        on every commit.

    Proven in:
        this repository

    Not this:
        Not a Markdown rule. A setext underline of equals signs is
        allowed; only the git start and end markers are rejected.
    """

    id = "no-conflict-markers"
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
            examined_n += 1
            for line in ws.read(path).splitlines():
                stripped = line.lstrip()
                if stripped.startswith((_START, _END)):
                    anchor = " ".join(line.split())
                    findings.append(
                        Finding(self.id, path, anchor,
                                message=f"conflict marker: {anchor}")
                    )
        return Result(
            self.id, self._state(findings, examined_n),
            examined_n=examined_n, skipped_n=ws.skipped_n, findings=findings,
        )

    def plants(self, ws):
        line = _START + " HEAD"
        yield Plant(
            label="start-marker",
            planted_ws=FakeWorkspace(files={"a.py": line + "\nx = 1\n"}),
            expected=(self.id, "a.py", line),
        )

    def fixture(self, kit):
        return FakeWorkspace(files={"a.py": "x = 1\n"})
