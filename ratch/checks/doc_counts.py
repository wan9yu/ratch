"""doc-counts-match-ssot check."""
import re

from ratch.check import Plant
from ratch.registry import discover
from ratch.result import Finding, Result, State
from ratch.testing import FakeWorkspace


def render_checks_region():
    return f"catalog_n={len(discover())}\n"


class Pin:
    def __init__(self, path, pattern, ssot_key):
        self.path = path
        self.pattern = re.compile(pattern)
        self.ssot_key = ssot_key


_DEFAULT_PINS = (
    Pin("README.md", r"^catalog_n=(\d+)$", "discover_n"),
)


class DocCountsMatchSSot:
    """Pin a README capture to a runtime catalog count.

    Rule:
        README.md must contain a catalog_n=N line whose N equals
        len(discover()).

    Why:
        A hand-typed catalog size in prose rots the moment a plugin is
        added; the entry-point catalog is the SSOT.

    Proven in:
        this repository

    Not this:
        Not a full README renderer. Not an enabled-set count (that
        needs a Workspace-aware manifest reader). Not a match scoped
        only to the generated HTML region.
    """

    id = "doc-counts-match-ssot"
    tier = "A"
    kind = "gate"
    scope = "global"
    proven_in = ("this repository",)
    confidence = "inferred"
    tolerates_unparseable = False

    def __init__(self, min_surface=1, pins=None):
        if min_surface < 1:
            raise ValueError("min_surface must be >= 1")
        self.min_surface = min_surface
        self.pins = _DEFAULT_PINS if pins is None else pins

    def _state(self, findings, examined_n):
        if findings:
            return State.FAIL
        if examined_n < self.min_surface:
            return State.VACUOUS
        return State.PASS

    def _ssot(self, key):
        if key == "discover_n":
            return str(len(discover()))
        raise ValueError(f"unknown ssot_key {key}")

    def check(self, ws):
        tracked = set(ws.tracked_files())
        findings = []
        texts = {}
        for pin in self.pins:
            if pin.path not in tracked:
                continue
            if pin.path not in texts:
                texts[pin.path] = ws.read(pin.path)
            matched = False
            for line in texts[pin.path].splitlines():
                hit = pin.pattern.search(line)
                if hit is None:
                    continue
                matched = True
                if hit.group(1) != self._ssot(pin.ssot_key):
                    findings.append(
                        Finding(self.id, pin.path, "catalog_n",
                                message="catalog_n disagrees with discover()")
                    )
            if not matched:
                findings.append(
                    Finding(self.id, pin.path, "catalog_n",
                            message="catalog_n line missing")
                )
        return Result(
            self.id, self._state(findings, len(texts)),
            examined_n=len(texts), skipped_n=ws.skipped_n, findings=findings,
        )

    def plants(self, ws):
        wrong = f"catalog_n={len(discover()) + 1}\n"
        yield Plant(
            label="wrong-catalog-n",
            planted_ws=FakeWorkspace(files={"README.md": wrong}),
            expected=(self.id, "README.md", "catalog_n"),
        )

    def fixture(self, kit):
        return FakeWorkspace(files={"README.md": render_checks_region()})
