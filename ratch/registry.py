"""Check discovery: installed entry points and a per-repo manifest.

Decision: a repository declares its gate set in code, not configuration.
The manifest is an importable module exposing CHECKS; an installed plugin
declares itself through the ratch.checks entry-point group. Rejected: a
TOML surface. Because: a check is an instance, and an instance is code.
"""
import importlib.metadata

__all__ = ["discover"]


def discover():
    """Return installed ratch.checks plugins as a name-to-class mapping."""
    eps = importlib.metadata.entry_points(group="ratch.checks")
    return {ep.name: ep.load() for ep in eps}
