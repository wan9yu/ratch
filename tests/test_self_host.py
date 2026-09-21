"""The ratch repo dogfoods every tooth it ships.

load_manifest read at this repo's own root must return the twenty-three ids in
ratch_checks.py CHECKS, not the empty default a fresh repo falls back to.
no-external-font-cdn is shipped as an entry point only.
"""
import importlib

from ratch.registry import load_manifest

ROOT = importlib.import_module("tests.repo_root").ROOT


def load_manifest_should_return_all_twenty_three_teeth_when_read_from_the_ratch_repo_root():
    checks = load_manifest(ROOT)

    ids = {check.id for check in checks}

    assert ids == {
        "no-forbidden-literal",
        "no-first-person",
        "no-ai-signatures",
        "no-circular-import",
        "plugin-registry",
        "manifest-purity",
        "no-conflict-markers",
        "no-vacuous-assert",
        "bdd-test-conventions",
        "no-pytest-skip",
        "no-hash-named-test",
        "todo-has-issue-ref",
        "doc-counts-match-ssot",
        "docs-equal-fresh-render",
        "catalog-size",
        "commit-heatmap",
        "no-internal-refs",
        "no-reassurance-words",
        "tests-repo-root-ssot",
        "loc-cap",
        "injected-clock",
        "doc-cli-examples-valid",
        "no-autoclose-keywords-in-commits",
    }
