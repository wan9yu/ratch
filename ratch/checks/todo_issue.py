"""todo-has-issue-ref check."""
from __future__ import annotations

import re

from ratch.check import Plant
from ratch.result import Finding, Result, State
from ratch.testing import FakeWorkspace

_MARKERS = ("TO" + "DO", "FIX" + "ME", "XX" + "X", "HA" + "CK")
_MARK = re.compile(r"\b(?:" + "|".join(_MARKERS) + r")\b")
_REF = re.compile(r"\(#\d+\)")


class TodoHasIssueRef:
    """Require an issue citation on debt markers.

    Rule:
        A tracked line that contains a debt-marker word must also
        carry an issue ref of the form (#N).

    Why:
        An unmarked debt item has no owner and no ticket; a machine
        can prove each marker points at a numbered issue.

    Proven in:
        this repository

    Not this:
        Not a requirement to file the issue. Not a style rule on
        comment wording beyond the marker and the (#N) shape.
    """

    id = "todo-has-issue-ref"
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
                if _MARK.search(line) and not _REF.search(line):
                    anchor = " ".join(line.split())
                    findings.append(
                        Finding(self.id, path, anchor,
                                message=f"debt marker: {anchor}")
                    )
        return Result(
            self.id, self._state(findings, examined_n),
            examined_n=examined_n, skipped_n=ws.skipped_n, findings=findings,
        )

    def plants(self, ws):
        line = _MARKERS[0] + " fix this"
        yield Plant(
            label="debt-unreferenced",
            planted_ws=FakeWorkspace(files={"a.py": line + "\n"}),
            expected=(self.id, "a.py", line),
        )

    def fixture(self, kit):
        return FakeWorkspace(files={"a.py": _MARKERS[0] + " fix this (#12)\n"})
