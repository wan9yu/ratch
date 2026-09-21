import importlib

from ratch.result import State
from ratch.testing import FakeWorkspace, assert_bites

BddTestConventions = importlib.import_module(
    "ratch.checks.bdd_conventions"
).BddTestConventions

_GWT = (
    "def foo_should_bar_when_baz():\n"
    "    x = 1\n"
    "\n"
    "    y = 2\n"
    "\n"
    "    assert x\n"
)


def bdd_test_conventions_should_fail_when_a_test_uses_the_test_prefix():
    ws = FakeWorkspace(files={"tests/t.py": "def test_foo():\n    pass\n"})

    result = BddTestConventions().check(ws)

    assert result.state is State.FAIL
    assert any(
        f.identity == ("bdd-test-conventions", "tests/t.py", "test_foo")
        for f in result.findings
    )


def bdd_test_conventions_should_fail_when_a_name_has_a_disjunction_segment():
    ws = FakeWorkspace(
        files={"tests/t.py": "def foo_should_pass_or_fail_when_x():\n    pass\n"}
    )

    result = BddTestConventions().check(ws)

    assert result.state is State.FAIL
    assert any(
        f.identity == (
            "bdd-test-conventions",
            "tests/t.py",
            "foo_should_pass_or_fail_when_x",
        )
        for f in result.findings
    )


def bdd_test_conventions_should_fail_when_a_name_lacks_when():
    ws = FakeWorkspace(files={"tests/t.py": "def foo_should_bar():\n    pass\n"})

    result = BddTestConventions().check(ws)

    assert result.state is State.FAIL
    assert any(
        f.identity == ("bdd-test-conventions", "tests/t.py", "foo_should_bar")
        for f in result.findings
    )


def bdd_test_conventions_should_fail_when_a_body_has_fewer_than_three_blocks():
    src = "def foo_should_bar_when_baz():\n    x = 1\n    assert x\n"

    result = BddTestConventions().check(FakeWorkspace(files={"tests/t.py": src}))

    assert result.state is State.FAIL


def bdd_test_conventions_should_pass_when_a_name_has_should_and_when():
    ws = FakeWorkspace(files={"tests/t.py": _GWT})

    result = BddTestConventions().check(ws)

    assert result.state is State.PASS


def bdd_test_conventions_should_pass_when_a_helper_is_private():
    ws = FakeWorkspace(
        files={"tests/t.py": "def _helper():\n    pass\n" + _GWT}
    )

    result = BddTestConventions().check(ws)

    assert result.state is State.PASS


def bdd_test_conventions_should_bite_its_plants_when_checked_against_its_own_fixture(tmp_path):
    check = BddTestConventions()

    assert_bites(check, tmp_path)

    assert check.id


def bdd_test_conventions_should_pass_when_def_appears_inside_a_string():
    src = '''DOC = """
def test_foo():
    pass
"""
''' + _GWT
    ws = FakeWorkspace(files={"tests/t.py": src})

    result = BddTestConventions().check(ws)

    assert result.state is State.PASS


def bdd_test_conventions_should_be_discoverable_when_registered_as_an_entry_point():
    from ratch.registry import discover

    found = discover().get('bdd-test-conventions')

    expected = BddTestConventions

    assert found is expected


def bdd_test_conventions_should_ignore_helpers_when_prefix_is_test_():
    src = (
        "def make_toml():\n    return 1\n"
        "def test_foo_should_bar_when_baz():\n"
        "    x = 1\n\n    y = 2\n\n    assert x\n"
    )
    ws = FakeWorkspace(files={"tests/t.py": src})

    result = BddTestConventions(prefix="test_").check(ws)

    assert result.state is State.PASS


def bdd_test_conventions_should_skip_body_shape_when_blank_blocks_is_zero():
    src = "def foo_should_bar_when_baz():\n    x = 1\n    assert x\n"
    ws = FakeWorkspace(files={"tests/t.py": src})

    result = BddTestConventions(blank_blocks=0).check(ws)

    assert result.state is State.PASS
