import importlib

from ratch.result import State
from ratch.testing import FakeWorkspace, assert_bites

NoHashNamedTest = importlib.import_module("ratch.checks.hash_named_test").NoHashNamedTest


def no_hash_named_test_should_fail_when_a_test_stem_ends_in_hex():
    path = "tests/test_foo_a1b2c3d4.py"

    ws = FakeWorkspace(files={path: "x = 1\n"})

    result = NoHashNamedTest().check(ws)
    assert result.state is State.FAIL
    assert any(
        f.identity == ("no-hash-named-test", path, path)
        for f in result.findings
    )


def no_hash_named_test_should_pass_when_a_test_stem_is_readable():
    ws = FakeWorkspace(files={"tests/test_foo.py": "x = 1\n"})

    result = NoHashNamedTest().check(ws)

    assert result.state is State.PASS


def no_hash_named_test_should_bite_its_plants_when_checked_against_its_own_fixture(tmp_path):
    check = NoHashNamedTest()

    assert_bites(check, tmp_path)

    assert check.id


def no_hash_named_test_should_be_discoverable_when_registered_as_an_entry_point():
    from ratch.registry import discover

    found = discover().get('no-hash-named-test')

    expected = NoHashNamedTest

    assert found is expected
