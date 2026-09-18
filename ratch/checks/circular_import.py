"""No-circular-import check."""
from __future__ import annotations

import sys

from ratch.result import Finding, Result, State

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
        this repository

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
    proven_in = ("this repository",)
    confidence = "portable-with-config"
    tolerates_unparseable = False

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
