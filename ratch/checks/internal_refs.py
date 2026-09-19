"""no-internal-refs check."""
from ratch.check import Plant
from ratch.result import Finding, Result, State
from ratch.testing import FakeWorkspace

# Assembled so this module does not contain the forbidden path prefix.
_NEEDLE = "inter" + "nal/"
_SKIP = {".gitignore"}


class NoInternalRefs:
    """Forbid pointers into the gitignored working-notes tree.

    Rule:
        Tracked files other than .gitignore must not contain the
        working-notes directory prefix, in content or in the path.

    Why:
        That tree is never shipped. A proven_in or comment that names
        it is a map to files GitHub does not have, and a leak of
        process notes that were meant to stay local.

    Proven in:
        This repository, after a shipped proven_in tuple named a
        gitignored working-notes tree that GitHub does not carry.

    Not this:
        Not a ban on the word in identifiers without the trailing
        slash. Not a scan of .gitignore, which must name the skip.
    """

    id = "no-internal-refs"
    tier = "A"
    kind = "gate"
    scope = "global"
    proven_in = ()
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
            if path in _SKIP:
                continue
            examined_n += 1
            if _NEEDLE in path:
                findings.append(
                    Finding(self.id, path, path,
                            message="working-notes prefix in path")
                )
                continue
            text = ws.read(path)
            if _NEEDLE in text:
                findings.append(
                    Finding(self.id, path, _NEEDLE,
                            message="working-notes prefix in content")
                )
        return Result(
            self.id, self._state(findings, examined_n),
            examined_n=examined_n, skipped_n=ws.skipped_n, findings=findings,
        )

    def plants(self, ws):
        leak = _NEEDLE + "notes.md"
        yield Plant(
            label="notes-prefix",
            planted_ws=FakeWorkspace(files={"a.py": leak + "\n"}),
            expected=(self.id, "a.py", _NEEDLE),
        )

    def fixture(self, kit):
        return FakeWorkspace(files={"a.py": "x = 1\n", ".gitignore": _NEEDLE + "\n"})
