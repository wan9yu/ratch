"""Shipped check plugins. Discovery is via entry points, not this module."""


def is_test_py(path):
    return path.endswith(".py") and (
        path.startswith("tests/") or "/tests/" in path
    )
