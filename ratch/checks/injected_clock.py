"""injected-clock check."""
import ast

from ratch.check import Plant
from ratch.checks import match_globs
from ratch.result import Finding, Result, State
from ratch.testing import FakeWorkspace

_TIME_ATTRS = frozenset({"time", "sleep", "monotonic", "perf_counter"})
_DT_ATTRS = frozenset({"now", "utcnow", "today"})


def _has_clock_class(tree):
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef) and node.name == "Clock":
            return True
    return False


def _bindings(tree):
    out = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name in ("time", "datetime"):
                    out[alias.asname or alias.name] = ("mod", alias.name)
        elif isinstance(node, ast.ImportFrom) and node.module == "time":
            for alias in node.names:
                out[alias.asname or alias.name] = ("func", alias.name)
        elif isinstance(node, ast.ImportFrom) and node.module == "datetime":
            for alias in node.names:
                if alias.name in ("datetime", "date"):
                    out[alias.asname or alias.name] = ("cls", alias.name)
    return out


def _raw_call_attr(func, binds, time_attrs, dt_attrs):
    if isinstance(func, ast.Name):
        bind = binds.get(func.id)
        if bind is not None and bind[0] == "func" and bind[1] in time_attrs:
            return bind[1]
        return None
    if not isinstance(func, ast.Attribute):
        return None
    if isinstance(func.value, ast.Name):
        bind = binds.get(func.value.id)
        if bind is None:
            return None
        kind, origin = bind
        if kind == "mod" and origin == "time" and func.attr in time_attrs:
            return func.attr
        if func.attr in dt_attrs and (
            (kind == "cls" and origin in ("date", "datetime"))
            or (kind == "mod" and origin == "datetime")
        ):
            return func.attr
        return None
    if not isinstance(func.value, ast.Attribute):
        return None
    if not isinstance(func.value.value, ast.Name):
        return None
    if (
        binds.get(func.value.value.id) == ("mod", "datetime")
        and func.value.attr in ("datetime", "date")
        and func.attr in dt_attrs
    ):
        return func.attr
    return None


def _time_hits(tree, time_attrs, dt_attrs):
    binds = _bindings(tree)
    hits = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        hit = _raw_call_attr(node.func, binds, time_attrs, dt_attrs)
        if hit is not None:
            hits.append(hit)
    return hits


class InjectedClock:
    """Confine raw time reads when a Clock type exists.

    Rule:
        Default: if any tracked *.py defines class Clock, other modules
        must not call bound stdlib time.time / sleep or datetime.now /
        today except clock_path. Import aliases and from-imports count.
        clock.sleep / SYSTEM_CLOCK.monotonic are the wait/time seam,
        not a leak. extra_time_attrs= / extra_dt_attrs= extend the Call
        sets (strftime is time-module only). from datetime import date
        is bound, so date.today() is a default leak. clock_paths= arms
        only when those files exist; paths= then limits which modules
        are confined. This repo uses the default (no Clock type → PASS).

    Why:
        Tests and production must share one clock; a raw now() call
        makes time uninjectable.

    Proven in:
        AST Call scan after resolving time/datetime bindings.

    Not this:
        Not a ban on datetime.timedelta. Not a ban on Clock.sleep.
        Not a requirement to invent a Clock where none exists.
    """

    id = "injected-clock"
    tier = "A"
    kind = "gate"
    scope = "global"
    proven_in = ()
    confidence = "inferred"
    tolerates_unparseable = False

    def __init__(self, min_surface=1, clock_path="clock.py",
                 clock_paths=None, paths=None,
                 extra_time_attrs=(), extra_dt_attrs=()):
        if min_surface < 1:
            raise ValueError("min_surface must be >= 1")
        self.min_surface = min_surface
        self.clock_path = clock_path
        self.clock_paths = None if clock_paths is None else tuple(clock_paths)
        self.paths = None if paths is None else tuple(paths)
        self.time_attrs = _TIME_ATTRS | frozenset(extra_time_attrs)
        self.dt_attrs = _DT_ATTRS | frozenset(extra_dt_attrs)

    def _state(self, findings, examined_n):
        if findings:
            return State.FAIL
        if examined_n < self.min_surface:
            return State.VACUOUS
        return State.PASS

    def _clock_ok(self, path):
        if self.clock_paths is not None:
            return path in self.clock_paths
        return path == self.clock_path or path.endswith("/" + self.clock_path)

    def check(self, ws):
        trees = []
        found_clock = False
        tracked = list(ws.tracked_files())
        if self.clock_paths is not None:
            found_clock = any(p in tracked for p in self.clock_paths)
        for path in tracked:
            if not path.endswith(".py"):
                continue
            tree = ws.ast(path)
            if tree is None:
                continue
            trees.append((path, tree))
            if self.clock_paths is None and _has_clock_class(tree):
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
            if self._clock_ok(path) or not match_globs(path, self.paths):
                continue
            examined_n += 1
            hits = _time_hits(tree, self.time_attrs, self.dt_attrs)
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
