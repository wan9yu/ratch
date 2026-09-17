import datetime

import pytest

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
