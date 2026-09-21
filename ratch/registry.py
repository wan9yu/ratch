"""Check discovery: installed entry points and a per-repo manifest.

Decision: a repository declares its gate set in code, not configuration.
The manifest is an importable module exposing CHECKS; an installed plugin
declares itself through the ratch.checks entry-point group. Rejected: a
TOML surface. Because: a check is an instance, and an instance is code.
"""
import importlib.metadata
import importlib.util
import pathlib

__all__ = ["discover", "load_manifest"]


def discover():
    """Return installed ratch.checks plugins as a name-to-class mapping."""
    eps = importlib.metadata.entry_points(group="ratch.checks")
    return {ep.name: ep.load() for ep in eps}


def load_manifest(repo_root):
    """Return the check instances a repo declares, or an empty list.

    A repo opts into checks by exposing CHECKS from ratch_checks.py at
    its root. Absent that file, nothing runs: a silent default gate
    would scan product names in consumer READMEs.
    """
    manifest = pathlib.Path(repo_root) / "ratch_checks.py"
    if not manifest.is_file():
        return []
    spec = importlib.util.spec_from_file_location("ratch_checks", manifest)
    if spec is None or spec.loader is None:
        return []
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return list(module.CHECKS)
