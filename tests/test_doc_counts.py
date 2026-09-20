import importlib

from ratch.registry import discover
from ratch.result import State
from ratch.testing import FakeWorkspace, assert_bites

_mod = importlib.import_module("ratch.checks.doc_counts")
DocCountsMatchSSot = _mod.DocCountsMatchSSot
render_checks_region = _mod.render_checks_region


def doc_counts_should_be_vacuous_when_readme_is_absent():
    result = DocCountsMatchSSot().check(FakeWorkspace(files={"a.py": "x = 1\n"}))

    assert result.state is State.VACUOUS

    assert result.examined_n == 0


def doc_counts_should_fail_when_catalog_n_disagrees_with_discover():
    ws = FakeWorkspace(files={"README.md": f"catalog_n={len(discover()) + 1}\n"})

    result = DocCountsMatchSSot().check(ws)

    assert result.state is State.FAIL
    assert any(
        f.identity == ("doc-counts-match-ssot", "README.md", "catalog_n")
        for f in result.findings
    )


def doc_counts_should_fail_when_catalog_n_line_is_missing():
    ws = FakeWorkspace(files={"README.md": "no counts here\n"})

    result = DocCountsMatchSSot().check(ws)

    assert result.state is State.FAIL
    assert result.examined_n == 1


def doc_counts_should_pass_when_catalog_n_matches_discover():
    ws = FakeWorkspace(files={"README.md": render_checks_region()})

    result = DocCountsMatchSSot().check(ws)

    assert result.state is State.PASS


def render_checks_region_should_equal_discover_n_when_called():
    found = render_checks_region()

    expected = f'catalog_n={len(discover())}\n'

    assert found == expected


def doc_counts_should_bite_its_plants_when_checked_against_its_own_fixture(tmp_path):
    check = DocCountsMatchSSot()

    assert_bites(check, tmp_path)

    assert check.id


def doc_counts_should_be_discoverable_when_registered_as_an_entry_point():
    catalog = discover()

    loaded = catalog.get("doc-counts-match-ssot")

    assert loaded is DocCountsMatchSSot
