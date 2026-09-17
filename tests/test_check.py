from ratch.check import Check
from ratch.result import Result, State


class _StubCheck:
    """Rule: a conforming check exposes the full Check shape.

    Why: the Protocol is the contract every tier-A rule is held to.

    Proven in: tests/test_check.py

    Not this: a class that omits a required method or attribute.
    """

    id = "stub"
    tier = "A"
    kind = "gate"
    scope = "global"
    proven_in = ("tests/test_check.py",)
    confidence = "breadth"
    tolerates_unparseable = False

    def check(self, ws):
        return Result(check_id=self.id, state=State.PASS)

    def plants(self, ws):
        return []

    def fixture(self, kit):
        return object()


def stub_check_should_satisfy_the_protocol_when_it_exposes_the_full_shape():
    stub = _StubCheck()

    conforms = isinstance(stub, Check)

    assert conforms


def stub_check_docstring_should_carry_four_headings_in_order_when_documented():
    doc = _StubCheck.__doc__

    seen = [h for h in ("Rule:", "Why:", "Proven in:", "Not this:") if h in doc]

    assert seen == ["Rule:", "Why:", "Proven in:", "Not this:"]


import dataclasses

import pytest

from ratch.check import Plant


def plant_should_hold_label_workspace_and_expected_identity_when_constructed():
    ws = object()

    plant = Plant(label="content", planted_ws=ws, expected=("no-forbidden-literal", "a.py", "x"))

    assert plant.label == "content"
    assert plant.planted_ws is ws
    assert plant.expected == ("no-forbidden-literal", "a.py", "x")


def plant_should_be_frozen_when_a_field_is_reassigned():
    plant = Plant(label="content", planted_ws=object(), expected=("r", "p", "x"))

    with pytest.raises(dataclasses.FrozenInstanceError):
        plant.label = "other"


import typing

from ratch import check as _check_module
from ratch.workspace import Workspace


def plant_type_hints_should_resolve_workspace_when_module_globals_include_it():
    # `Workspace` is only imported under TYPE_CHECKING (see ratch/check.py),
    # so a caller resolving hints must supply it via globalns; this is the
    # tool-facing seam that keeps typing.get_type_hints from raising
    # NameError on the deferred forward reference.
    globalns = dict(vars(_check_module))
    globalns["Workspace"] = Workspace

    hints = typing.get_type_hints(Plant, globalns=globalns)

    assert hints["planted_ws"] is Workspace
