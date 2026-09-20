import importlib

from ratch.registry import discover
from ratch.result import State
from ratch.testing import FakeWorkspace, assert_bites

InjectedClock = importlib.import_module(
    "ratch.checks.injected_clock"
).InjectedClock


def injected_clock_should_pass_when_no_clock_type_exists():
    ws = FakeWorkspace(files={'app.py': 'import time\nnow = time.time()\n'})

    found = InjectedClock().check(ws).state

    expected = State.PASS

    assert found is expected


def injected_clock_should_fail_when_a_clock_exists_and_time_is_raw():
    ws = FakeWorkspace(files={'clock.py': 'class Clock:\n    pass\n', 'app.py': 'import time\nnow = time.time()\n'})

    found = InjectedClock().check(ws).state

    expected = State.FAIL

    assert found is expected


def injected_clock_should_bite_its_plants_when_checked_against_its_own_fixture(tmp_path):
    check = InjectedClock()

    assert_bites(check, tmp_path)

    assert check.id


def injected_clock_should_be_discoverable_when_registered_as_an_entry_point():
    catalog = discover()

    loaded = catalog.get("injected-clock")

    assert loaded is InjectedClock
