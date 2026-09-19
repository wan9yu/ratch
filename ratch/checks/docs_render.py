"""docs-equal-fresh-render check."""
from ratch.check import Plant
from ratch.checks.doc_counts import render_checks_region
from ratch.result import Finding, Result, State
from ratch.testing import FakeWorkspace

_START = "<!-- ratch:generated:checks -->"
_END = "<!-- ratch:generated:checks:end -->"
_README = "README.md"


def _region(text):
    if _START not in text or _END not in text:
        return None
    return text.split(_START, 1)[1].split(_END, 1)[0]


class DocsEqualFreshRender:
    """Require the README generated region to match a fresh render.

    Rule:
        README.md must contain the generated-checks markers whose inner
        body equals render_checks_region().

    Why:
        A catalog_n line that a human typed can still be the wrong
        shape (extra lines, missing newline). Byte-equal to the live
        renderer is the SSOT.

    Proven in:
        This repository: the generated checks region is byte-equal to
        a fresh render_checks_region().

    Not this:
        Not a rewrite of the authored fence. Not a full README
        generator. Not an enabled-set count.
    """

    id = "docs-equal-fresh-render"
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
        if _README not in ws.tracked_files():
            return Result(
                self.id, self._state([], 0),
                examined_n=0, skipped_n=ws.skipped_n, findings=[],
            )
        body = _region(ws.read(_README))
        expected = "\n" + render_checks_region()
        findings = []
        if body is None or body != expected:
            findings.append(
                Finding(self.id, _README, "generated:checks",
                        message="generated region stale")
            )
        return Result(
            self.id, self._state(findings, 1),
            examined_n=1, skipped_n=ws.skipped_n, findings=findings,
        )

    def plants(self, ws):
        stale = f"{_START}\ncatalog_n=0\n{_END}\n"
        yield Plant(
            label="stale-region",
            planted_ws=FakeWorkspace(files={_README: stale}),
            expected=(self.id, _README, "generated:checks"),
        )

    def fixture(self, kit):
        text = f"{_START}\n{render_checks_region()}{_END}\n"
        return FakeWorkspace(files={_README: text})
