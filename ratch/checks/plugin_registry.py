"""Plugin-registry meta-check."""
from __future__ import annotations

import inspect

from ratch.check import Plant
from ratch.result import Finding, Result, State
from ratch.testing import FakeWorkspace, assert_bites

_HEADINGS = ("Rule:", "Why:", "Proven in:", "Not this:")


def _headings_present(doc):
    if not doc:
        return []
    return [heading for heading in _HEADINGS if heading in doc]


def _min_surface_of(cls):
    value = getattr(cls, "min_surface", None)
    if isinstance(value, int):
        return value
    try:
        param = inspect.signature(cls.__init__).parameters.get("min_surface")
    except (TypeError, ValueError):
        return None
    if param is None or param.default is inspect.Parameter.empty:
        return None
    if isinstance(param.default, int):
        return param.default
    return None


def _instantiate(cls):
    try:
        params = inspect.signature(cls.__init__).parameters
    except (TypeError, ValueError):
        return None
    required = [
        param.name for param in params.values()
        if param.name != "self"
        and param.default is inspect.Parameter.empty
        and param.kind not in (param.VAR_POSITIONAL, param.VAR_KEYWORD)
    ]
    if required == ["package"]:
        return cls(package="_ratch_registry_probe")
    if required:
        return None
    return cls()


def _idle_constructor(inst):
    clean = inst.fixture(None)
    return (
        not list(inst.plants(clean))
        and inst.check(clean).state is State.VACUOUS
    )


def _ban_check(owner, ws):
    findings = []
    examined_n = 0
    for path in ws.tracked_files():
        examined_n += 1
        if "BAN" in ws.read(path):
            findings.append(
                Finding(owner.id, path, "BAN", message="banned token")
            )
    if findings:
        state = State.FAIL
    elif examined_n < getattr(owner, "min_surface", 1):
        state = State.VACUOUS
    else:
        state = State.PASS
    return Result(owner.id, state, examined_n=examined_n, findings=findings)


def _ban_plants(owner, ws):
    yield Plant(
        label="content:BAN",
        planted_ws=FakeWorkspace(files={"planted.py": "BAN\n"}),  # type: ignore[arg-type]
        expected=(owner.id, "planted.py", "BAN"),
    )


def _ban_fixture(owner, kit):
    return FakeWorkspace(files={"clean.py": "x = 1\n"})


class _CleanTooth:
    """A minimal contract-satisfying tooth for the registry fixture.

    Rule:
        Tracked files may not contain the token BAN.
    Why:
        The registry meta-check needs a clean plugin to prove PASS.
    Proven in:
        this repository's plugin-registry plants
    Not this:
        Not a project rule; a fixture double only.
    """

    id = "clean-tooth"
    tier = "A"
    kind = "gate"
    scope = "global"
    proven_in = ()
    confidence = "breadth"
    tolerates_unparseable = False
    min_surface = 1

    def check(self, ws):
        return _ban_check(self, ws)

    def plants(self, ws):
        yield from _ban_plants(self, ws)

    def fixture(self, kit):
        return _ban_fixture(self, kit)


class _MissingWhy:
    """A tooth whose docstring omits the Why heading.

    Rule:
        Tracked files may not contain the token BAN.
    Proven in:
        this repository's plugin-registry plants
    Not this:
        Not a project rule; a plant double only.
    """

    id = "missing-why"
    tier = "A"
    kind = "gate"
    scope = "global"
    proven_in = ()
    confidence = "breadth"
    tolerates_unparseable = False
    min_surface = 1

    def check(self, ws):
        return _ban_check(self, ws)

    def plants(self, ws):
        yield from _ban_plants(self, ws)

    def fixture(self, kit):
        return _ban_fixture(self, kit)


class _NoMinSurface:
    """A tooth that never declares min_surface.

    Rule:
        Tracked files may not contain the token BAN.
    Why:
        The registry meta-check must refuse a plugin with no floor.
    Proven in:
        this repository's plugin-registry plants
    Not this:
        Not a project rule; a plant double only.
    """

    id = "no-min-surface"
    tier = "A"
    kind = "gate"
    scope = "global"
    proven_in = ()
    confidence = "breadth"
    tolerates_unparseable = False

    def check(self, ws):
        return _ban_check(self, ws)

    def plants(self, ws):
        yield from _ban_plants(self, ws)

    def fixture(self, kit):
        return _ban_fixture(self, kit)


class _Toothless:
    """A tooth that exposes no plants.

    Rule:
        Tracked files may not contain the token BAN.
    Why:
        The registry meta-check must refuse a plugin that cannot bite.
    Proven in:
        this repository's plugin-registry plants
    Not this:
        Not a project rule; a plant double only.
    """

    id = "toothless"
    tier = "A"
    kind = "gate"
    scope = "global"
    proven_in = ()
    confidence = "breadth"
    tolerates_unparseable = False
    min_surface = 1

    def check(self, ws):
        return Result(self.id, State.PASS, examined_n=1)

    def fixture(self, kit):
        return FakeWorkspace(files={"clean.py": "x = 1\n"})


class _NoFixture:
    """A tooth that exposes no fixture method.

    Rule:
        Tracked files may not contain the token BAN.
    Why:
        The registry meta-check must refuse a plugin with no fixture.
    Proven in:
        this repository's plugin-registry plants
    Not this:
        Not a project rule; a plant double only.
    """

    id = "no-fixture"
    tier = "A"
    kind = "gate"
    scope = "global"
    proven_in = ()
    confidence = "breadth"
    tolerates_unparseable = False
    min_surface = 1

    def check(self, ws):
        return _ban_check(self, ws)

    def plants(self, ws):
        yield from _ban_plants(self, ws)


class _BrokenBite:
    """A tooth that never FAILs its plants.

    Rule:
        Tracked files may not contain the token BAN.
    Why:
        The registry meta-check must refuse a plugin whose plants do not bite.
    Proven in:
        this repository's plugin-registry plants
    Not this:
        Not a project rule; a plant double only.
    """

    id = "broken-bite"
    tier = "A"
    kind = "gate"
    scope = "global"
    proven_in = ()
    confidence = "breadth"
    tolerates_unparseable = False
    min_surface = 1

    def check(self, ws):
        return Result(self.id, State.PASS, examined_n=1)

    def plants(self, ws):
        yield from _ban_plants(self, ws)

    def fixture(self, kit):
        return _ban_fixture(self, kit)


class PluginRegistry:
    """Refuse a registered plugin that does not carry the check contract.

    Rule:
        Every plugin in the workspace catalog must carry a four-heading
        docstring, a min_surface of at least 1, and plants and fixture
        methods. Gate plugins must also pass assert_bites; eyes do not.

    Why:
        A registered plugin with no plants, no floor, or no headings is a
        dark gate: it looks enabled while proving nothing. The registry
        meta-check makes the authoring contract a blocking tooth.

    Proven in:
        A registry meta-check: four-heading docstring, min_surface,
        plants, fixture, and assert_bites on gate plugins.

    Not this:
        Not a judgment of Why: prose quality. Not the manifest-purity
        check (side-effect-free import, identical repr). Not the rule
        that only listed plugins RUN — discovery makes plugins available;
        the manifest still chooses what executes.
    """

    id = "plugin-registry"
    tier = "A"
    kind = "meta"
    scope = "ratch"
    proven_in = ()
    confidence = "breadth"
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

    def _inspect(self, name, cls):
        findings = []
        if _headings_present(cls.__doc__) != list(_HEADINGS):
            findings.append(
                Finding(self.id, name, "four-heading docstring",
                        message=f"{name}: four-heading docstring")
            )
        floor = _min_surface_of(cls)
        if not isinstance(floor, int) or floor < 1:
            findings.append(
                Finding(self.id, name, "min_surface",
                        message=f"{name}: min_surface")
            )
        if not callable(getattr(cls, "plants", None)):
            findings.append(
                Finding(self.id, name, "plants",
                        message=f"{name}: plants")
            )
        if not callable(getattr(cls, "fixture", None)):
            findings.append(
                Finding(self.id, name, "fixture",
                        message=f"{name}: fixture")
            )
        if findings:
            return findings
        try:
            inst = _instantiate(cls)
        except Exception:
            findings.append(
                Finding(self.id, name, "construct",
                        message=f"{name}: construct")
            )
            return findings
        if inst is None:
            findings.append(
                Finding(self.id, name, "construct",
                        message=f"{name}: unconstructable")
            )
            return findings
        if getattr(cls, "kind", "gate") != "eye":
            try:
                assert_bites(inst, None)
            except Exception:
                if not _idle_constructor(inst):
                    findings.append(
                        Finding(self.id, name, "assert_bites",
                                message=f"{name}: assert_bites")
                    )
        return findings

    def check(self, ws):
        catalog = ws.plugin_classes()
        findings = []
        examined_n = 0
        for name in sorted(catalog):
            examined_n += 1
            findings.extend(self._inspect(name, catalog[name]))
        return Result(
            self.id, self._state(findings, examined_n),
            examined_n=examined_n, skipped_n=ws.skipped_n,
            unparseable_n=0, findings=findings,
        )

    def plants(self, ws):
        missing_why = FakeWorkspace(
            files={"ok.py": "x = 1\n"},
            plugin_classes={"missing-why": _MissingWhy},
        )
        yield Plant(
            label="heading:Why:",
            planted_ws=missing_why,  # type: ignore[arg-type]
            expected=(self.id, "missing-why", "four-heading docstring"),
        )
        no_floor = FakeWorkspace(
            files={"ok.py": "x = 1\n"},
            plugin_classes={"no-min-surface": _NoMinSurface},
        )
        yield Plant(
            label="min_surface",
            planted_ws=no_floor,  # type: ignore[arg-type]
            expected=(self.id, "no-min-surface", "min_surface"),
        )
        toothless = FakeWorkspace(
            files={"ok.py": "x = 1\n"},
            plugin_classes={"toothless": _Toothless},
        )
        yield Plant(
            label="plants",
            planted_ws=toothless,  # type: ignore[arg-type]
            expected=(self.id, "toothless", "plants"),
        )
        no_fixture = FakeWorkspace(
            files={"ok.py": "x = 1\n"},
            plugin_classes={"no-fixture": _NoFixture},
        )
        yield Plant(
            label="fixture",
            planted_ws=no_fixture,  # type: ignore[arg-type]
            expected=(self.id, "no-fixture", "fixture"),
        )
        broken_bite = FakeWorkspace(
            files={"ok.py": "x = 1\n"},
            plugin_classes={"broken-bite": _BrokenBite},
        )
        yield Plant(
            label="assert_bites",
            planted_ws=broken_bite,  # type: ignore[arg-type]
            expected=(self.id, "broken-bite", "assert_bites"),
        )

    def fixture(self, kit):
        return FakeWorkspace(
            files={"ok.py": "x = 1\n"},
            plugin_classes={"clean-tooth": _CleanTooth},
        )
