from ratch.checks.forbidden_literal import NoForbiddenLiteral
from ratch.registry import discover, load_manifest


def discover_should_resolve_no_forbidden_literal_when_the_package_is_installed():
    loaded = discover()

    assert loaded["no-forbidden-literal"] is NoForbiddenLiteral


def load_manifest_should_return_the_default_check_when_no_manifest_exists(tmp_path):
    checks = load_manifest(tmp_path)

    assert len(checks) == 1
    assert isinstance(checks[0], NoForbiddenLiteral)


def load_manifest_should_return_manifest_checks_when_a_manifest_module_exists(tmp_path):
    manifest = tmp_path / "ratch_checks.py"
    manifest.write_text(
        "from ratch.checks.forbidden_literal import NoForbiddenLiteral\n"
        "CHECKS = [NoForbiddenLiteral()]\n",
        encoding="utf-8",
    )

    checks = load_manifest(tmp_path)

    assert len(checks) == 1
    assert isinstance(checks[0], NoForbiddenLiteral)
