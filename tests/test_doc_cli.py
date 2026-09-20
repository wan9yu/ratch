import importlib

from ratch.registry import discover
from ratch.result import State
from ratch.testing import FakeWorkspace, assert_bites

DocCliExamplesValid = importlib.import_module(
    "ratch.checks.doc_cli"
).DocCliExamplesValid


def doc_cli_examples_valid_should_fail_when_a_ratch_verb_is_unknown():
    ws = FakeWorkspace(files={"README.md": "run `ratch frobnicate` please\n"})

    result = DocCliExamplesValid().check(ws)

    assert result.state is State.FAIL


def doc_cli_examples_valid_should_pass_when_examples_match_argparse():
    ws = FakeWorkspace(files={'README.md': 'run `ratch check`\n'})

    found = DocCliExamplesValid().check(ws).state

    expected = State.PASS

    assert found is expected


def doc_cli_examples_valid_should_bite_its_plants_when_checked_against_its_own_fixture(tmp_path):
    check = DocCliExamplesValid()

    assert_bites(check, tmp_path)

    assert check.id


def doc_cli_examples_valid_should_be_discoverable_when_registered_as_an_entry_point():
    catalog = discover()

    loaded = catalog.get("doc-cli-examples-valid")

    assert loaded is DocCliExamplesValid


def doc_cli_examples_valid_should_ignore_other_markdown_when_paths_selects_readme():
    ws = FakeWorkspace(files={
        "README.md": "`ratch check`\n",
        "notes.md": "`ratch frobnicate`\n",
    })

    result = DocCliExamplesValid(paths=("README.md",)).check(ws)

    assert result.state is State.PASS
