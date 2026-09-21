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


def _armed(app):
    return FakeWorkspace(files={
        "clock.py": "class Clock:\n    pass\n",
        "app.py": app,
    })


def injected_clock_should_pass_when_injected_clock_sleep_is_called():
    ws = FakeWorkspace(files={
        "clock.py": "class Clock:\n    def sleep(self, n):\n        pass\n",
        "app.py": "def run(clock):\n    clock.sleep(1)\n",
    })

    result = InjectedClock().check(ws)

    assert result.state is State.PASS


def injected_clock_should_fail_when_sleep_is_imported_from_time():
    ws = _armed("from time import sleep\nsleep(1)\n")

    result = InjectedClock().check(ws)

    assert result.state is State.FAIL


def injected_clock_should_fail_when_datetime_now_is_imported_from_datetime():
    ws = _armed("from datetime import datetime\ndatetime.now()\n")

    result = InjectedClock().check(ws)

    assert result.state is State.FAIL


def injected_clock_should_fail_when_datetime_datetime_now_is_called():
    ws = _armed("import datetime\ndatetime.datetime.now()\n")

    result = InjectedClock().check(ws)

    assert result.state is State.FAIL


def injected_clock_should_pass_when_system_clock_monotonic_is_called():
    ws = _armed("SYSTEM_CLOCK.monotonic()\n")

    result = InjectedClock().check(ws)

    assert result.state is State.PASS


def injected_clock_should_fail_when_time_is_imported_under_an_alias():
    ws = _armed("import time as t\nt.time()\n")

    result = InjectedClock().check(ws)

    assert result.state is State.FAIL


def injected_clock_should_fail_when_extra_time_attr_is_strftime():
    ws = _armed("import time\ntime.strftime('%Y')\n")

    result = InjectedClock(extra_time_attrs=("strftime",)).check(ws)

    assert result.state is State.FAIL


def injected_clock_should_fail_when_date_today_is_imported_from_datetime():
    ws = _armed("from datetime import date\ndate.today()\n")

    result = InjectedClock().check(ws)

    assert result.state is State.FAIL


def injected_clock_should_pass_when_strftime_is_called_on_a_datetime():
    ws = _armed("stamp.strftime('%Y')\n")

    result = InjectedClock(extra_time_attrs=("strftime",)).check(ws)

    assert result.state is State.PASS


def injected_clock_should_bite_its_plants_when_checked_against_its_own_fixture(tmp_path):
    check = InjectedClock()

    assert_bites(check, tmp_path)

    assert check.id


def injected_clock_should_be_discoverable_when_registered_as_an_entry_point():
    catalog = discover()

    loaded = catalog.get("injected-clock")

    assert loaded is InjectedClock


def injected_clock_should_pass_when_clock_paths_file_is_absent():
    ws = FakeWorkspace(files={"app.py": "import time\nnow = time.time()\n"})

    result = InjectedClock(clock_paths=("pkg/clock.py",)).check(ws)

    assert result.state is State.PASS


def injected_clock_should_fail_when_clock_paths_exists_and_app_reads_time():
    ws = FakeWorkspace(files={
        "pkg/clock.py": "class Clock:\n    pass\n",
        "pkg/app.py": "import time\nnow = time.time()\n",
    })

    result = InjectedClock(
        clock_paths=("pkg/clock.py",), paths=("pkg/**/*.py",),
    ).check(ws)

    assert result.state is State.FAIL
