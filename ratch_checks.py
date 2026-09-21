"""ratch's own gate set: the dogfood manifest.

ratch gates itself with every tooth it ships. load_manifest returns this
CHECKS list for the ratch repo root; a fresh repo with no such module
runs nothing. Needles that encode this tree are passed explicitly.
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
NoReassuranceWords = importlib.import_module(
    "ratch.checks.reassurance"
).NoReassuranceWords
RepoRootSSot = importlib.import_module(
    "ratch.checks.repo_root_ssot"
).RepoRootSSot
LocCap = importlib.import_module(
    "ratch.checks.loc_cap"
).LocCap
InjectedClock = importlib.import_module(
    "ratch.checks.injected_clock"
).InjectedClock
DocCliExamplesValid = importlib.import_module(
    "ratch.checks.doc_cli"
).DocCliExamplesValid
NoAutocloseKeywords = importlib.import_module(
    "ratch.checks.autoclose"
).NoAutocloseKeywords

# no-external-font-cdn is an entry point but omitted here: this repo has
# no html/css/js, so the tooth would be VACUOUS (exit 2).
CHECKS = [
    NoForbiddenLiteral(patterns=("cl[a]ude",)),
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
    NoInternalRefs(needles=("inter" + "nal/",)),
    NoReassuranceWords(),
    RepoRootSSot(),
    LocCap(),
    InjectedClock(),
    DocCliExamplesValid(),
    NoAutocloseKeywords(),
]
