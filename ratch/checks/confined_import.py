"""confined-import check."""
import ast

from ratch.check import Plant
from ratch.checks import match_globs
from ratch.result import Finding, Result, State
from ratch.testing import FakeWorkspace


def _attr_pair(spec):
    mod, attr = spec.rsplit(".", 1)
    return (mod, attr)


def _confine_hits(tree, names, attr_pairs):
    hits = []
    binds = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                mod = alias.name
                binds[alias.asname or alias.name] = mod
                if mod in names or mod.split(".")[0] in names:
                    hits.append(mod)
        elif isinstance(node, ast.ImportFrom):
            if not node.module:
                continue
            mod = node.module
            if mod in names or mod.split(".")[0] in names:
                hits.append(mod)
            for alias in node.names:
                binds[alias.asname or alias.name] = (mod, alias.name)
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        if isinstance(func, ast.Name):
            bind = binds.get(func.id)
            if isinstance(bind, tuple) and bind in attr_pairs:
                hits.append(bind[1])
        elif (
            isinstance(func, ast.Attribute)
            and isinstance(func.value, ast.Name)
        ):
            bind = binds.get(func.value.id)
            if isinstance(bind, str) and (bind, func.attr) in attr_pairs:
                hits.append(func.attr)
    return hits


class ConfinedImport:
    """Confine listed imports to allow_paths.

    Rule:
        names=() and attrs=() is idle: VACUOUS, no scan. When set,
        tracked *.py outside allow_paths must not import those modules
        (aliases count, unused imports count) or call attrs such as
        os.pidfd_open. allow_paths= uses match_globs; empty means no
        reviewed seam.

    Why:
        A wait primitive copied into a second module reopens a
        single-owner bug; one reviewed file is the seam.

    Proven in:
        Bind-then-blame import scan with negative plants.

    Not this:
        Not injected-clock (Call-only, Clock-armed). Not a ban on
        asyncio everywhere. Not a default names list from a CPython bug.
    """

    id = "confined-import"
    tier = "A"
    kind = "gate"
    scope = "global"
    proven_in = ()
    confidence = "inferred"
    tolerates_unparseable = False

    def __init__(self, min_surface=1, names=(), attrs=(), allow_paths=()):
        if min_surface < 1:
            raise ValueError("min_surface must be >= 1")
        self.min_surface = min_surface
        self.names = tuple(names)
        self.attrs = tuple(attrs)
        self.allow_paths = tuple(allow_paths)

    def _state(self, findings, examined_n):
        if findings:
            return State.FAIL
        if examined_n < self.min_surface:
            return State.VACUOUS
        return State.PASS

    def check(self, ws):
        if not self.names and not self.attrs:
            return Result(
                self.id, State.VACUOUS, examined_n=0,
                skipped_n=ws.skipped_n, findings=[],
            )
        names = set(self.names)
        attr_pairs = {_attr_pair(spec) for spec in self.attrs}
        findings = []
        examined_n = 0
        for path in ws.tracked_files():
            if not path.endswith(".py"):
                continue
            if match_globs(path, self.allow_paths):
                continue
            examined_n += 1
            tree = ws.ast(path)
            if tree is None:
                continue
            hits = _confine_hits(tree, names, attr_pairs)
            if hits:
                findings.append(
                    Finding(self.id, path, hits[0],
                            message=f"confined import: {hits[0]}")
                )
        return Result(
            self.id, self._state(findings, examined_n),
            examined_n=examined_n, skipped_n=ws.skipped_n,
            unparseable_n=ws.unparseable_n, findings=findings,
        )

    def plants(self, ws):
        if not self.names:
            return
        name = self.names[0]
        yield Plant(
            label="leak",
            planted_ws=FakeWorkspace(files={"app.py": f"import {name}\n"}),
            expected=(self.id, "app.py", name),
        )

    def fixture(self, kit):
        return FakeWorkspace(files={"app.py": "x = 1\n"})
