"""Shipped check plugins. Discovery is via entry points, not this module."""
import fnmatch


def is_test_py(path):
    return path.endswith(".py") and (
        path.startswith("tests/") or "/tests/" in path
    )


def match_globs(path, globs):
    """True if globs is None or path matches any glob (``**`` = any dirs)."""
    if globs is None:
        return True
    return any(_match_one(path, pattern) for pattern in globs)


def _match_one(path, pattern):
    if fnmatch.fnmatch(path, pattern):
        return True
    if "**" not in pattern:
        return False
    head, tail = pattern.split("**", 1)
    prefix = head.rstrip("/")
    suffix = tail.lstrip("/")
    if prefix and path != prefix and not path.startswith(prefix + "/"):
        return False
    rest = path[len(prefix):].lstrip("/") if prefix else path
    if not suffix:
        return True
    base = rest.rsplit("/", 1)[-1]
    return fnmatch.fnmatch(rest, suffix) or fnmatch.fnmatch(base, suffix)
