"""commit-heatmap eye, lifted from argus-gateway commit_heatmap hour buckets."""
from datetime import datetime

from ratch.check import Plant
from ratch.result import MeasuredValue, MState, Result, State
from ratch.testing import FakeWorkspace

_MAX_COMMITS = 500


class CommitHeatmap:
    """Report the busiest hour-of-day in recent git history.

    Rule:
        Recent commit timestamps are bucketed by local hour of day and
        the peak bucket is reported as a measured value.

    Why:
        A commit heatmap is a lens on when the repo actually moves;
        failing the run because Tuesday was quiet would turn a dashboard
        into a gate. argus-gateway's commit_heatmap is the structure x
        time tool; this eye keeps only the hour histogram.

    Proven in:
        this repository

    Not this:
        Not the ASCII directory heatmap. Not role filters, --exclude, or
        depth. Not a gate.
    """

    id = "commit-heatmap"
    tier = "A"
    kind = "eye"
    scope = "global"
    proven_in = ("this repository",)
    confidence = "depth-once"
    tolerates_unparseable = False

    def __init__(self, min_surface=1):
        if min_surface < 1:
            raise ValueError("min_surface must be >= 1")
        self.min_surface = min_surface

    def check(self, ws):
        hours = [0] * 24
        n = 0
        for line in ws.git_log(fmt="%at").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                ts = int(line)
            except ValueError:
                continue
            hours[datetime.fromtimestamp(ts).hour] += 1
            n += 1
            if n >= _MAX_COMMITS:
                break
        if n < self.min_surface:
            return Result(self.id, State.VACUOUS, examined_n=n, findings=[])
        peak_hour = max(range(24), key=lambda h: hours[h])
        measured = MeasuredValue(
            value=f"{peak_hour}h:{hours[peak_hour]}/{n}",
            state=MState.MEASURED,
            source="git_log:%at",
            measured_at=ws.now(),
        )
        return Result(
            self.id, State.PASS, examined_n=n, findings=[], measured=measured,
        )

    def plants(self, ws):
        yield Plant(
            label="empty-log",
            planted_ws=FakeWorkspace(files={"a.py": "x = 1\n"}, git_log_text=""),
            expected=(self.id, "git_log", "0"),
        )

    def fixture(self, kit):
        return FakeWorkspace(
            files={"a.py": "x = 1\n"},
            git_log_text="1700000000\n1700003600\n",
        )
