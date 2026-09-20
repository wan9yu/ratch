"""injected-clock check."""
import ast

from ratch.check import Plant
from ratch.result import Finding, Result, State
from ratch.testing import FakeWorkspace

_TIME_ATTRS = frozenset({"time", "sleep", "monotonic", "perf_counter"})
_DT_ATTRS = frozenset({"now", "utcnow", "today"})


def _has_clock_class(tree):
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef) and node.name == "Clock":
            return True
    return False


def _time_hits(tree):
    hits = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Attribute):
            continue
        if node.attr in _TIME_ATTRS or node.attr in _DT_ATTRS:
            hits.append(node.attr)
    return hits


class InjectedClock:
    """Confine raw time reads when a Clock type exists.

    Rule:
        If any tracked *.py defines class Clock, other modules must not
        call time.time / sleep or datetime.now / today except the
        configured clock module.

    Why:
        Tests and production must share one clock; a raw now() call
        makes time uninjectable.

    Proven in:
        AST attribute scan. No Clock type → VACUOUS (nothing to confine).

    Not this:
        Not a ban on datetime.timedelta. Not a requirement to invent a
        Clock where none exists.
    """

    id = "injected-clock"
    tier = "A"
    kind = "gate"
    scope = "global"
    proven_in = ()
    confidence = "inferred"
    tolerates_unparseable = False

    def __init__(self, min_surface=1, clock_path="clock.py"):
        if min_surface < 1:
            raise ValueError("min_surface must be >= 1")
        self.min_surface = min_surface
        self.clock_path = clock_path

    def _state(self, findings, examined_n):
        if findings:
            return State.FAIL
        if examined_n < self.min_surface:
            return State.VACUOUS
        return State.PASS

    def check(self, ws):
        trees = []
        found_clock = False
        for path in ws.tracked_files():
            if not path.endswith(".py"):
                continue
            tree = ws.ast(path)
            if tree is None:
                continue
            trees.append((path, tree))
            if _has_clock_class(tree):
                found_clock = True
        if not found_clock:
            n = len(trees)
            return Result(
                self.id, self._state([], n),
                examined_n=n, skipped_n=ws.skipped_n, findings=[],
            )
        findings = []
        examined_n = 0
        for path, tree in trees:
            if path == self.clock_path or path.endswith("/" + self.clock_path):
                continue
            examined_n += 1
            hits = _time_hits(tree)
            if hits:
                findings.append(
                    Finding(self.id, path, hits[0],
                            message=f"raw time: {hits[0]}")
                )
        return Result(
            self.id, self._state(findings, examined_n),
            examined_n=examined_n, skipped_n=ws.skipped_n,
            unparseable_n=ws.unparseable_n, findings=findings,
        )

    def plants(self, ws):
        files = {
            "clock.py": "class Clock:\n    pass\n",
            "app.py": "import time\nnow = time.time()\n",
        }
        yield Plant(
            label="raw-time",
            planted_ws=FakeWorkspace(files=files),
            expected=(self.id, "app.py", "time"),
        )

    def fixture(self, kit):
        return FakeWorkspace(files={
            "clock.py": "class Clock:\n    pass\n",
            "app.py": "x = 1\n",
        })
