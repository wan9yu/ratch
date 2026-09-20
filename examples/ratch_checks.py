"""Minimal manifest: one gate. Copy to the repository root as ratch_checks.py.

This repository's own root ratch_checks.py is the full dogfood set, not
this example. Eyes such as CommitHeatmap print and do not fail the run.
"""
from ratch.checks.forbidden_literal import NoForbiddenLiteral

# from ratch.checks.commit_heatmap import CommitHeatmap

CHECKS = [
    NoForbiddenLiteral(),
    # CommitHeatmap(),
]
