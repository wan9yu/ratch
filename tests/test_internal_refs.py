import importlib

from ratch.registry import discover
from ratch.result import State
from ratch.testing import FakeWorkspace, assert_bites

_mod = importlib.import_module("ratch.checks.internal_refs")
NoInternalRefs = _mod.NoInternalRefs
_NEEDLE = _mod._NEEDLE


def no_internal_refs_should_fail_when_a_tracked_file_names_the_notes_prefix():
    ws = FakeWorkspace(files={"a.py": _NEEDLE + "notes.md\n"})
    result = NoInternalRefs().check(ws)
    assert result.state is State.FAIL
    assert any(
        f.identity == ("no-internal-refs", "a.py", _NEEDLE)
        for f in result.findings
    )


def no_internal_refs_should_pass_when_only_gitignore_names_the_prefix():
    ws = FakeWorkspace(files={"a.py": "x = 1\n", ".gitignore": _NEEDLE + "\n"})
    result = NoInternalRefs().check(ws)
    assert result.state is State.PASS


def no_internal_refs_should_bite_its_plants_when_checked_against_its_own_fixture(tmp_path):
    assert_bites(NoInternalRefs(), tmp_path)


def no_internal_refs_should_be_discoverable_when_registered_as_an_entry_point():
    assert discover().get("no-internal-refs") is NoInternalRefs
