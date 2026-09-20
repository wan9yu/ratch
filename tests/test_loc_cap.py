import importlib

from ratch.registry import discover
from ratch.result import State
from ratch.testing import FakeWorkspace, assert_bites

LocCap = importlib.import_module("ratch.checks.loc_cap").LocCap


def loc_cap_should_fail_when_a_python_file_exceeds_the_ceiling():
    ws = FakeWorkspace(files={"a.py": "x = 1\n" * 1001})

    result = LocCap().check(ws)

    assert result.state is State.FAIL


def loc_cap_should_pass_when_files_are_under_the_ceiling():
    found = LocCap().check(FakeWorkspace(files={'a.py': 'x = 1\n'})).state

    expected = State.PASS

    assert found is expected


def loc_cap_should_bite_its_plants_when_checked_against_its_own_fixture(tmp_path):
    check = LocCap()

    assert_bites(check, tmp_path)

    assert check.id


def loc_cap_should_be_discoverable_when_registered_as_an_entry_point():
    catalog = discover()

    loaded = catalog.get("loc-cap")

    assert loaded is LocCap
