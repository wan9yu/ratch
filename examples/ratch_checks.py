"""Minimal manifest: one gate. Copy to the repository root as ratch_checks.py.

This repository's own root ratch_checks.py is the full dogfood set, not
this example. NoForbiddenLiteral() with no patterns is VACUOUS (exit 2);
pass the tokens this tree actually forbids. Eyes such as CommitHeatmap
print and do not fail the run.
"""
from ratch.checks.forbidden_literal import NoForbiddenLiteral

# from ratch.checks.commit_heatmap import CommitHeatmap

CHECKS = [
    NoForbiddenLiteral(patterns=("cl[a]ude",)),
    # CommitHeatmap(),
]
