"""Check discovery: installed entry points and a per-repo manifest.

Decision: a repository declares its gate set in code, not configuration.
The manifest is an importable module exposing CHECKS; an installed plugin
declares itself through the ratch.checks entry-point group. Rejected: a
TOML surface. Because: a check is an instance, and an instance is code.
"""
import importlib.metadata
import importlib.util
import pathlib

from ratch.checks.forbidden_literal import NoForbiddenLiteral

__all__ = ["discover", "load_manifest"]


def discover():
    """Return installed ratch.checks plugins as a name-to-class mapping."""
    eps = importlib.metadata.entry_points(group="ratch.checks")
    return {ep.name: ep.load() for ep in eps}


def load_manifest(repo_root):
    """Return the check instances a repo declares, or the default gate.

    A repo opts into a custom check set by exposing a CHECKS list from a
    ratch_checks.py module at its root; absent that file, the default
    surface is the single forbidden-literal gate.
    """
    manifest = pathlib.Path(repo_root) / "ratch_checks.py"
    if manifest.is_file():
        spec = importlib.util.spec_from_file_location("ratch_checks", manifest)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return list(module.CHECKS)
    return [NoForbiddenLiteral()]
