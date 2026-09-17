from ratch.checks.forbidden_literal import NoForbiddenLiteral
from ratch.registry import discover


def discover_should_resolve_no_forbidden_literal_when_the_package_is_installed():
    loaded = discover()

    assert loaded["no-forbidden-literal"] is NoForbiddenLiteral
