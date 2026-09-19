"""catalog-size eye."""
from ratch.check import Plant
from ratch.result import MeasuredValue, MState, Result, State
from ratch.testing import FakeWorkspace


class CatalogSize:
    """Report how many checks are installed, without gating.

    Rule:
        The installed ratch.checks catalog size is reported as a
        measured value.

    Why:
        A gate that failed the run because the catalog was empty would
        confuse absence of plugins with a rule break; an eye only
        measures.

    Proven in:
        This repository: an eye that reports how many checks are
        installed, without failing the run.

    Not this:
        Not a gate. VACUOUS on an empty catalog does not fail the run.
    """

    id = "catalog-size"
    tier = "A"
    kind = "eye"
    scope = "global"
    proven_in = ()
    confidence = "inferred"
    tolerates_unparseable = False

    def __init__(self, min_surface=1):
        if min_surface < 1:
            raise ValueError("min_surface must be >= 1")
        self.min_surface = min_surface

    def check(self, ws):
        n = len(ws.plugin_classes())
        measured = MeasuredValue(
            value=n, state=MState.MEASURED,
            source="plugin_classes", measured_at=ws.now(),
        )
        if n < self.min_surface:
            state = State.VACUOUS
        else:
            state = State.PASS
        return Result(
            self.id, state, examined_n=n, findings=[], measured=measured,
        )

    def plants(self, ws):
        yield Plant(
            label="empty-catalog",
            planted_ws=FakeWorkspace(files={"a.py": "x = 1\n"}, plugin_classes={}),
            expected=(self.id, "catalog", "0"),
        )

    def fixture(self, kit):
        return FakeWorkspace(
            files={"a.py": "x = 1\n"},
            plugin_classes={"no-forbidden-literal": object},
        )
