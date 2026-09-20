import importlib

from ratch.registry import discover
from ratch.result import MState, State
from ratch.runner import Runner
from ratch.testing import FakeWorkspace

CatalogSize = importlib.import_module("ratch.checks.catalog_size").CatalogSize


def catalog_size_should_pass_when_the_workspace_has_plugins():
    ws = FakeWorkspace(
        files={"a.py": "x = 1\n"},
        plugin_classes={"no-forbidden-literal": object},
    )

    result = CatalogSize().check(ws)

    assert result.state is State.PASS
    assert result.measured is not None
    assert result.measured.value == 1
    assert result.measured.state is MState.MEASURED


def catalog_size_should_be_vacuous_when_the_catalog_is_empty():
    result = CatalogSize().check(FakeWorkspace(files={'a.py': 'x = 1\n'}))

    found = result.state

    expected = State.VACUOUS

    assert found is expected


def runner_should_exit_zero_when_only_an_eye_is_vacuous():
    report = Runner(use_nice=False).run(
        [CatalogSize()],
        FakeWorkspace(files={"a.py": "x = 1\n"}),
    )

    assert report.results["catalog-size"].state is State.VACUOUS

    assert report.exit_code == 0


def catalog_size_should_be_discoverable_when_registered_as_an_entry_point():
    catalog = discover()

    loaded = catalog.get("catalog-size")

    assert loaded is CatalogSize
