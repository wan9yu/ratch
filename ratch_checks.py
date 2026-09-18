"""ratch's own gate set: the dogfood manifest.

ratch gates itself with every tooth it ships. load_manifest returns this
CHECKS list for the ratch repo root; a fresh repo with no such module
still falls back to the single forbidden-literal default.
"""
from ratch.checks.ai_signatures import NoAiSignatures
from ratch.checks.circular_import import NoCircularImport
from ratch.checks.first_person import NoFirstPerson
from ratch.checks.forbidden_literal import NoForbiddenLiteral

CHECKS = [
    NoForbiddenLiteral(),
    NoFirstPerson(),
    NoAiSignatures(),
    NoCircularImport(package="ratch"),
]
