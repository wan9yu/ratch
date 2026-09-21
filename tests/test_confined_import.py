import importlib

from ratch.registry import discover
from ratch.result import State
from ratch.testing import FakeWorkspace, assert_bites

ConfinedImport = importlib.import_module(
    "ratch.checks.confined_import"
).ConfinedImport


def confined_import_should_be_vacuous_when_no_name_is_configured():
    ws = FakeWorkspace(files={"app.py": "import asyncio\n"})

    result = ConfinedImport().check(ws)

    assert result.state is State.VACUOUS
    assert result.examined_n == 0


def confined_import_should_fail_when_a_confined_module_is_imported():
    ws = FakeWorkspace(files={"app.py": "import asyncio\n"})

    result = ConfinedImport(names=("asyncio",)).check(ws)

    assert result.state is State.FAIL
    assert any(
        f.identity == ("confined-import", "app.py", "asyncio")
        for f in result.findings
    )


def confined_import_should_pass_when_the_import_is_in_allow_paths():
    ws = FakeWorkspace(files={
        "_procwait.py": "import asyncio\n",
        "app.py": "x = 1\n",
    })

    result = ConfinedImport(
        names=("asyncio",), allow_paths=("_procwait.py",),
    ).check(ws)

    assert result.state is State.PASS


def confined_import_should_fail_when_the_module_is_imported_under_an_alias():
    ws = FakeWorkspace(files={"app.py": "import asyncio as aio\n"})

    result = ConfinedImport(names=("asyncio",)).check(ws)

    assert result.state is State.FAIL


def confined_import_should_fail_when_pidfd_open_is_called():
    ws = FakeWorkspace(files={"app.py": "import os\nos.pidfd_open(1)\n"})

    result = ConfinedImport(attrs=("os.pidfd_open",)).check(ws)

    assert result.state is State.FAIL


def confined_import_should_bite_its_plants_when_checked_against_its_own_fixture(tmp_path):
    check = ConfinedImport(names=("asyncio",))

    assert_bites(check, tmp_path)

    assert check.id


def confined_import_should_be_discoverable_when_registered_as_an_entry_point():
    catalog = discover()

    loaded = catalog.get("confined-import")

    assert loaded is ConfinedImport
