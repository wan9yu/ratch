from ratch.checks.ai_signatures import NoAiSignatures
from ratch.checks.circular_import import NoCircularImport
from ratch.checks.first_person import NoFirstPerson
from ratch.checks.forbidden_literal import NoForbiddenLiteral
from ratch.checks.plugin_registry import PluginRegistry
from ratch.result import State
from ratch.testing import FakeWorkspace, assert_bites


def _ws(plugin_classes):
    return FakeWorkspace(files={"ok.py": "x = 1\n"}, plugin_classes=plugin_classes)


def plugin_registry_should_fail_when_a_plugin_docstring_omits_a_required_heading():
    from ratch.checks.plugin_registry import _MissingWhy

    result = PluginRegistry().check(_ws({"missing-why": _MissingWhy}))

    assert result.state is State.FAIL
    assert any(
        finding.identity == ("plugin-registry", "missing-why", "four-heading docstring")
        for finding in result.findings
    )


def plugin_registry_should_fail_when_a_plugin_declares_no_min_surface():
    from ratch.checks.plugin_registry import _NoMinSurface

    result = PluginRegistry().check(_ws({"no-min-surface": _NoMinSurface}))

    assert result.state is State.FAIL
    assert any(
        finding.identity == ("plugin-registry", "no-min-surface", "min_surface")
        for finding in result.findings
    )


def plugin_registry_should_fail_when_a_plugin_exposes_no_plants():
    from ratch.checks.plugin_registry import _Toothless

    result = PluginRegistry().check(_ws({"toothless": _Toothless}))

    assert result.state is State.FAIL
    assert any(
        finding.identity == ("plugin-registry", "toothless", "plants")
        for finding in result.findings
    )


def plugin_registry_should_fail_when_a_plugin_exposes_no_fixture():
    from ratch.checks.plugin_registry import _NoFixture

    result = PluginRegistry().check(_ws({"no-fixture": _NoFixture}))

    assert result.state is State.FAIL
    assert any(
        finding.identity == ("plugin-registry", "no-fixture", "fixture")
        for finding in result.findings
    )


def plugin_registry_should_fail_when_a_plugin_does_not_bite_its_plants():
    from ratch.checks.plugin_registry import _BrokenBite

    result = PluginRegistry().check(_ws({"broken-bite": _BrokenBite}))

    assert result.state is State.FAIL
    assert any(
        finding.identity == ("plugin-registry", "broken-bite", "assert_bites")
        for finding in result.findings
    )


def plugin_registry_should_pass_when_a_plugin_carries_the_full_contract():
    from ratch.checks.plugin_registry import _CleanTooth

    result = PluginRegistry().check(_ws({"clean-tooth": _CleanTooth}))

    assert result.state is State.PASS
    assert result.findings == []


def plugin_registry_should_be_vacuous_when_no_plugin_is_registered():
    result = PluginRegistry().check(_ws({}))

    assert result.state is State.VACUOUS

    assert result.examined_n == 0


def plugin_registry_should_pass_when_the_shipped_teeth_are_the_catalog():
    result = PluginRegistry().check(_ws({
        "no-forbidden-literal": NoForbiddenLiteral,
        "no-first-person": NoFirstPerson,
        "no-ai-signatures": NoAiSignatures,
        "no-circular-import": NoCircularImport,
    }))

    assert result.state is State.PASS

    assert result.findings == []


def plugin_registry_should_bite_its_plants_when_checked_against_its_own_fixture(tmp_path):
    check = PluginRegistry()

    assert_bites(check, tmp_path)

    assert check.id


def plugin_registry_should_be_discoverable_when_registered_as_an_entry_point():
    from ratch.registry import discover

    found = discover().get('plugin-registry')

    expected = PluginRegistry

    assert found is expected
