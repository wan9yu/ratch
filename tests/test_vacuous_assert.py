import importlib

from ratch.result import State
from ratch.testing import FakeWorkspace, assert_bites

NoVacuousAssert = importlib.import_module(
    "ratch.checks.vacuous_assert"
).NoVacuousAssert


def no_vacuous_assert_should_fail_when_a_test_file_has_assert_true():
    ws = FakeWorkspace(files={"tests/t.py": "    assert True\n"})
    result = NoVacuousAssert().check(ws)
    assert result.state is State.FAIL
    assert any(
        f.identity == ("no-vacuous-assert", "tests/t.py", "assert True")
        for f in result.findings
    )


def no_vacuous_assert_should_pass_when_assert_false_has_a_message():
    ws = FakeWorkspace(files={"tests/t.py": "assert False, \"boom\"\n"})
    result = NoVacuousAssert().check(ws)
    assert result.state is State.PASS


def no_vacuous_assert_should_pass_when_assert_uses_is_true():
    ws = FakeWorkspace(files={"tests/t.py": "assert x is True\n"})
    result = NoVacuousAssert().check(ws)
    assert result.state is State.PASS


def no_vacuous_assert_should_be_vacuous_when_no_test_file_is_present():
    ws = FakeWorkspace(files={"src/mod.py": "assert True\n"})
    result = NoVacuousAssert().check(ws)
    assert result.state is State.VACUOUS


def no_vacuous_assert_should_bite_its_plants_when_checked_against_its_own_fixture(tmp_path):
    assert_bites(NoVacuousAssert(), tmp_path)
