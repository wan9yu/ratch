import importlib

from ratch.checks.doc_counts import render_checks_region
from ratch.registry import discover
from ratch.result import State
from ratch.testing import FakeWorkspace, assert_bites

DocsEqualFreshRender = importlib.import_module(
    "ratch.checks.docs_render"
).DocsEqualFreshRender

_START = "<!-- ratch:generated:checks -->"
_END = "<!-- ratch:generated:checks:end -->"


def docs_equal_fresh_render_should_be_vacuous_when_readme_is_absent():
    result = DocsEqualFreshRender().check(FakeWorkspace(files={'a.py': 'x = 1\n'}))

    found = result.state

    expected = State.VACUOUS

    assert found is expected


def docs_equal_fresh_render_should_fail_when_the_region_is_stale():
    ws = FakeWorkspace(files={"README.md": f"{_START}\ncatalog_n=0\n{_END}\n"})

    result = DocsEqualFreshRender().check(ws)

    assert result.state is State.FAIL
    assert any(
        f.identity == ("docs-equal-fresh-render", "README.md", "generated:checks")
        for f in result.findings
    )


def docs_equal_fresh_render_should_pass_when_the_region_matches_a_fresh_render():
    text = f"{_START}\n{render_checks_region()}{_END}\n"

    result = DocsEqualFreshRender().check(FakeWorkspace(files={"README.md": text}))

    assert result.state is State.PASS


def docs_equal_fresh_render_should_bite_its_plants_when_checked_against_its_own_fixture(tmp_path):
    check = DocsEqualFreshRender()

    assert_bites(check, tmp_path)

    assert check.id


def docs_equal_fresh_render_should_be_discoverable_when_registered_as_an_entry_point():
    catalog = discover()

    loaded = catalog.get("docs-equal-fresh-render")

    assert loaded is DocsEqualFreshRender
