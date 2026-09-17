import datetime

import pytest

from ratch.result import State
from ratch.testing import FakeClock, FakeWorkspace


def fakeclock_should_return_its_fixed_date_when_asked():
    clock = FakeClock(datetime.date(2026, 1, 2))

    result = clock.now()

    assert result == datetime.date(2026, 1, 2)


def fakeworkspace_should_answer_from_its_dict_when_queried():
    ws = FakeWorkspace({"a.py": "x = 1\ny = 2\n", "b.txt": "hello\n"})

    tracked = ws.tracked_files()
    content = ws.read("a.py")
    grep = ws.git_grep("y")

    assert tracked == ["a.py", "b.txt"]
    assert content == "x = 1\ny = 2\n"
    assert grep == [("a.py", 2, "y = 2")]


from ratch.check import Plant
from ratch.result import Result
from ratch.testing import assert_bites


class _ToothlessCheck:
    id = "toothless"

    def fixture(self, kit):
        return FakeWorkspace({"clean.py": "ok = 1\n"})

    def plants(self, ws):
        bad = FakeWorkspace({"bad.py": "boom = 1\n"})
        yield Plant(label="boom", planted_ws=bad,
                    expected=("toothless", "bad.py", "boom"))

    def check(self, ws):
        return Result(check_id="toothless", state=State.PASS)


def assert_bites_should_raise_when_check_lacks_teeth():
    toothless = _ToothlessCheck()

    with pytest.raises(AssertionError):
        assert_bites(toothless, kit=None)
