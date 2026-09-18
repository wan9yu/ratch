"""Thin pytest adapter (Tier B seam). CLI remains the tooth; this re-runs
the same manifest without nicing."""
from __future__ import annotations

import importlib
import pathlib

import pytest

from ratch.registry import load_manifest
from ratch.runner import Runner
from ratch.workspace import Workspace


def resolve_plugin(spec):
    module_name, sep, class_name = spec.partition(":")
    if sep != ":" or not module_name or not class_name:
        raise ValueError("expected module:Class")
    module = importlib.import_module(module_name)
    return getattr(module, class_name)


def iter_ratch_check_ids(cwd):
    return [check.id for check in load_manifest(cwd)]


def pytest_addoption(parser):
    parser.addoption("--ratch", action="store_true", default=False)
    parser.addoption("--ratch-plugin", action="store", default=None)


class RatchItem(pytest.Item):
    def __init__(self, name, parent, check):
        super().__init__(name, parent)
        self.check = check

    def runtest(self):
        cwd = pathlib.Path.cwd()
        report = Runner(use_nice=False).run([self.check], Workspace(cwd))
        if report.exit_code != 0:
            pytest.fail(f"{self.check.id} exit_code {report.exit_code}")


def pytest_collection_modifyitems(session, config, items):
    if not config.getoption("--ratch"):
        return
    cwd = pathlib.Path.cwd()
    for check in load_manifest(cwd):
        items.append(
            RatchItem.from_parent(session, name=f"ratch:{check.id}", check=check)
        )
    spec = config.getoption("--ratch-plugin")
    if spec:
        cls = resolve_plugin(spec)
        extra = cls()
        items.append(
            RatchItem.from_parent(session, name=f"ratch:{extra.id}", check=extra)
        )
