import pytest

from ratch.checks.forbidden_literal import NoForbiddenLiteral
from ratch.registry import discover, load_manifest


def discover_should_resolve_no_forbidden_literal_when_the_package_is_installed():
    loaded = discover()

    found = loaded['no-forbidden-literal']

    expected = NoForbiddenLiteral

    assert found is expected


def load_manifest_should_return_the_default_check_when_no_manifest_exists(tmp_path):
    checks = load_manifest(tmp_path)

    assert len(checks) == 1

    assert isinstance(checks[0], NoForbiddenLiteral)


def no_forbidden_literal_should_raise_when_min_surface_is_zero():
    expected = ValueError

    with pytest.raises(expected):
        NoForbiddenLiteral(min_surface=0)

    assert expected is ValueError


def load_manifest_should_return_manifest_checks_when_a_manifest_module_exists(tmp_path):
    manifest = tmp_path / "ratch_checks.py"
    manifest.write_text('CHECKS = ["from-manifest-sentinel"]\n', encoding="utf-8")

    checks = load_manifest(tmp_path)

    assert checks == ["from-manifest-sentinel"]


def the_example_manifest_should_gate_on_the_forbidden_literal_check_when_read_from_examples():
    import importlib
    import importlib.util

    ROOT = importlib.import_module("tests.repo_root").ROOT
    spec = importlib.util.spec_from_file_location(
        "example_manifest", ROOT / "examples" / "ratch_checks.py"
    )
    if spec is None or spec.loader is None:
        raise AssertionError("could not load example manifest")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    assert len(module.CHECKS) == 1
    assert isinstance(module.CHECKS[0], NoForbiddenLiteral)


def the_pre_commit_hook_should_invoke_the_staged_gate_when_the_hook_file_is_read():
    import importlib
    ROOT = importlib.import_module("tests.repo_root").ROOT
    banned = "cl" + "aude"
    text = (ROOT / "hooks" / "pre-commit").read_text()

    body = [line for line in text.splitlines() if line.strip()]

    assert body[0].startswith("#!")
    assert "python3 -m ratch check --staged" in text
    assert banned not in text


def the_readme_should_declare_what_ratch_never_gates_when_the_authored_fence_is_present():
    import importlib
    ROOT = importlib.import_module("tests.repo_root").ROOT
    banned = "cl" + "aude"
    text = (ROOT / "README.md").read_text()

    for phrase in ("naming quality", "abstraction quality",
                   "prose quality", "test meaningfulness"):
        assert phrase in text

    assert banned not in text
    padded = f" {text.lower()} "
    assert not any(f" {pronoun} " in padded for pronoun in ("i", "we", "our", "my"))
    for name in discover():
        assert name in text


def the_package_docstring_should_state_the_single_source_of_truth_decision_when_ratch_is_imported():
    import ratch

    doc = ratch.__doc__ or ""

    assert "SSOT" in doc
    assert "copied fact rots" in doc
