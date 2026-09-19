"""ratch's own gate set: the dogfood manifest.

ratch gates itself with every tooth it ships. load_manifest returns this
CHECKS list for the ratch repo root; a fresh repo with no such module
still falls back to the single forbidden-literal default.
"""
import importlib

from ratch.checks.ai_signatures import NoAiSignatures
from ratch.checks.circular_import import NoCircularImport
from ratch.checks.first_person import NoFirstPerson
from ratch.checks.forbidden_literal import NoForbiddenLiteral

PluginRegistry = importlib.import_module(
    "ratch.checks.plugin_registry"
).PluginRegistry
ManifestPurity = importlib.import_module(
    "ratch.checks.manifest_purity"
).ManifestPurity
NoConflictMarkers = importlib.import_module(
    "ratch.checks.conflict_markers"
).NoConflictMarkers
NoVacuousAssert = importlib.import_module(
    "ratch.checks.vacuous_assert"
).NoVacuousAssert
BddTestConventions = importlib.import_module(
    "ratch.checks.bdd_conventions"
).BddTestConventions
NoPytestSkip = importlib.import_module(
    "ratch.checks.pytest_skip"
).NoPytestSkip
NoHashNamedTest = importlib.import_module(
    "ratch.checks.hash_named_test"
).NoHashNamedTest
TodoHasIssueRef = importlib.import_module(
    "ratch.checks.todo_issue"
).TodoHasIssueRef
DocCountsMatchSSot = importlib.import_module(
    "ratch.checks.doc_counts"
).DocCountsMatchSSot
DocsEqualFreshRender = importlib.import_module(
    "ratch.checks.docs_render"
).DocsEqualFreshRender
CatalogSize = importlib.import_module(
    "ratch.checks.catalog_size"
).CatalogSize
CommitHeatmap = importlib.import_module(
    "ratch.checks.commit_heatmap"
).CommitHeatmap
NoInternalRefs = importlib.import_module(
    "ratch.checks.internal_refs"
).NoInternalRefs

# no-external-font-cdn is an entry point but omitted here: this repo has
# no html/css/js, so the tooth would be VACUOUS (exit 2).
CHECKS = [
    NoForbiddenLiteral(),
    NoFirstPerson(),
    NoAiSignatures(),
    NoCircularImport(package="ratch"),
    PluginRegistry(),
    ManifestPurity(),
    NoConflictMarkers(),
    NoVacuousAssert(),
    BddTestConventions(),
    NoPytestSkip(),
    NoHashNamedTest(),
    TodoHasIssueRef(),
    DocCountsMatchSSot(),
    DocsEqualFreshRender(),
    CatalogSize(),
    CommitHeatmap(),
    NoInternalRefs(),
]
