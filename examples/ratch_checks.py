"""Example manifest: the checks this repository gates on."""
from ratch.checks.forbidden_literal import NoForbiddenLiteral

CHECKS = [NoForbiddenLiteral()]
