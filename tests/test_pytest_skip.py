import importlib

from ratch.result import State
from ratch.testing import FakeWorkspace, assert_bites

NoPytestSkip = importlib.import_module("ratch.checks.pytest_skip").NoPytestSkip


def no_pytest_skip_should_fail_when_a_test_calls_pytest_skip():
    ws = FakeWorkspace(files={"tests/t.py": "import pytest\npytest.skip('x')\n"})

    result = NoPytestSkip().check(ws)

    assert result.state is State.FAIL
    assert any(
        f.identity == ("no-pytest-skip", "tests/t.py", "pytest.skip")
        for f in result.findings
    )


def no_pytest_skip_should_pass_when_tests_do_not_skip():
    ws = FakeWorkspace(files={"tests/t.py": "assert value is True\n"})

    result = NoPytestSkip().check(ws)

    assert result.state is State.PASS


def no_pytest_skip_should_be_vacuous_when_no_test_file_is_present():
    ws = FakeWorkspace(files={"src/mod.py": "import pytest\npytest.skip('x')\n"})

    result = NoPytestSkip().check(ws)

    assert result.state is State.VACUOUS


def no_pytest_skip_should_bite_its_plants_when_checked_against_its_own_fixture(tmp_path):
    check = NoPytestSkip()

    assert_bites(check, tmp_path)

    assert check.id


def no_pytest_skip_should_be_discoverable_when_registered_as_an_entry_point():
    from ratch.registry import discover

    found = discover().get('no-pytest-skip')

    expected = NoPytestSkip

    assert found is expected


def no_pytest_skip_should_ignore_e2e_when_paths_selects_invariants():
    ws = FakeWorkspace(files={
        "tests/e2e/t.py": "import pytest\npytest.skip('x')\n",
        "tests/invariants/t.py": "assert True is False, 'x'\n",
    })

    result = NoPytestSkip(paths=("tests/invariants/**/*.py",)).check(ws)

    assert result.state is State.PASS
