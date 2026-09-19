"""The ratch repo dogfoods every tooth it ships.

load_manifest read at this repo's own root must return the full nine-check
gate declared in ratch_checks.py, not the single-check default a fresh
repo falls back to.
"""
import pathlib

from ratch.registry import load_manifest

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent


def load_manifest_should_return_all_nine_teeth_when_read_from_the_ratch_repo_root():
    checks = load_manifest(REPO_ROOT)

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
    }
