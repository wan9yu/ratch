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
]
