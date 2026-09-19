"""No-circular-import check."""
from __future__ import annotations

import pathlib
import sys
import tempfile

from ratch.check import Plant
from ratch.result import Finding, Result, State
from ratch.workspace import Workspace

_CYCLE_SIGNATURES = ("partially initialized module", "circular import")


def _strip_trailing_path(line):
    """Drop CPython's trailing ``(/abs/path/mod.py)`` from an ImportError line.

    That path varies by machine and tmp dir; removing it makes the anchor
    deterministic so a planted cycle yields a stable finding identity.
    """
    if line.endswith(")"):
        open_at = line.rfind(" (")
        if open_at != -1 and "/" in line[open_at:]:
            return line[:open_at].rstrip()
    return line


def _cycle_line(stderr):
    lines = [ln.strip() for ln in stderr.splitlines() if ln.strip()]
    for line in reversed(lines):
        if any(sig in line for sig in _CYCLE_SIGNATURES):
            return _strip_trailing_path(line)
    return lines[-1] if lines else ""


def _write_package(root, name, modules):
    pkg = pathlib.Path(root) / name
    pkg.mkdir(parents=True, exist_ok=True)
    for mod_name, text in modules.items():
        (pkg / mod_name).write_text(text)
    return pkg


class NoCircularImport:
    """Forbid a package that cannot be imported because of an import cycle.

    Rule:
        Importing the configured top-level package in a fresh interpreter
        must not raise a CPython circular-import error.

    Why:
        A cycle imports clean in one entry order and explodes in another, so
        it hides until a production import path hits the bad order; a
        subprocess import proves the package loads on every commit, where an
        in-process import would be masked by an already-populated sys.modules.

    Proven in:
        A fresh-interpreter import of the package: CPython cycle
        strings FAIL; any other import error is ERROR, never FAIL.

    Not this:
        Not a static import-graph analysis and not a style rule. Only an
        actual interpreter cycle FAILs; a missing dependency or any other
        import error is reported as ERROR (could-not-measure), never FAIL.
        The subprocess import runs against the checked-out worktree, not
        the index, because Workspace.run always uses repo_root as cwd.
    """

    id = "no-circular-import"
    tier = "A"
    kind = "gate"
    scope = "global"
    proven_in = ()
    confidence = "portable-with-config"
    tolerates_unparseable = False
    min_surface = 1

    def __init__(self, package, interpreter=None):
        self.package = package
        self.interpreter = interpreter

    def check(self, ws):
        interp = self.interpreter or sys.executable
        proc = ws.run([interp, "-c", f"import {self.package}"])
        if proc.returncode == 0:
            return Result(self.id, State.PASS, examined_n=1)
        stderr = proc.stderr or ""
        if any(sig in stderr for sig in _CYCLE_SIGNATURES):
            anchor = _cycle_line(stderr)
            return Result(
                self.id, State.FAIL, examined_n=1,
                findings=[Finding(self.id, self.package, anchor,
                                  message=f"circular import: {anchor}")],
            )
        return Result(self.id, State.ERROR, examined_n=0)

    def plants(self, ws):
        root = pathlib.Path(tempfile.mkdtemp(prefix="ratch-circ-"))
        _write_package(root, self.package, {
            "__init__.py": f"from {self.package} import a\n",
            "a.py": f"from {self.package}.b import beta\n\nalpha = 1\n",
            "b.py": f"from {self.package}.a import alpha\n\nbeta = 2\n",
        })
        planted = Workspace(root)
        probe = NoCircularImport(self.package, interpreter=self.interpreter)
        probed = probe.check(planted)
        if probed.state is not State.FAIL or not probed.findings:
            raise AssertionError(
                f"{self.id}: probe could not reproduce the planted cycle "
                f"(got {probed.state})")
        finding = probed.findings[0]
        yield Plant(
            label=f"circular:{self.package}",
            planted_ws=planted,
            expected=(self.id, self.package, finding.anchor),
        )

    def fixture(self, kit):
        root = pathlib.Path(tempfile.mkdtemp(prefix="ratch-circ-clean-"))
        _write_package(root, self.package, {"__init__.py": "value = 42\n"})
        return Workspace(root)
