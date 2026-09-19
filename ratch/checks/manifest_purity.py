"""Manifest-purity check."""
from __future__ import annotations

import ast
import importlib.util
import pathlib
import re
import tempfile

from ratch.check import Plant
from ratch.result import Finding, Result, State
from ratch.testing import FakeWorkspace

_MANIFEST = "ratch_checks.py"
_ADDR = re.compile(r"0x[0-9a-fA-F]+")

_CLEAN = (
    "from ratch.checks.forbidden_literal import NoForbiddenLiteral\n"
    "CHECKS = [NoForbiddenLiteral()]\n"
)


def _fingerprint(checks):
    return [_ADDR.sub("0x…", repr(item)) for item in checks]


def _ambient_findings(rule_id, path, tree):
    findings = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name):
            if node.value.id == "os" and node.attr == "environ":
                findings.append(
                    Finding(rule_id, path, "os.environ",
                            message="manifest reads os.environ")
                )
            elif node.value.id == "os" and node.attr == "getenv":
                findings.append(
                    Finding(rule_id, path, "os.getenv",
                            message="manifest reads os.getenv")
                )
        if (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id == "open"
        ):
            findings.append(
                Finding(rule_id, path, "open",
                        message="manifest calls open")
            )
    return findings


def _load(source, name):
    root = pathlib.Path(tempfile.mkdtemp(prefix="ratch-manifest-"))
    path = root / _MANIFEST
    path.write_text(source)
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError("could not load manifest")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class ManifestPurity:
    """Refuse a manifest that is not a side-effect-free CHECKS list.

    Rule:
        The repo-root ratch_checks.py, if present, must not read os.environ,
        call os.getenv, or call open, and two loads of CHECKS must share
        an address-normalized fingerprint.

    Why:
        The manifest is the enabled set. Ambient reads or a non-repeatable
        CHECKS list make the gate unreproducible, so a meta spine that
        diffs the manifest across commits is meaningless.

    Proven in:
        This repository's manifest contract: ratch_checks.py is a
        side-effect-free CHECKS list, imported twice with the same
        fingerprint.

    Not this:
        Not a ban on importlib or on from ratch.checks imports. Not a
        scan of any file other than repo-root ratch_checks.py. Not a
        requirement that the module dict contain only CHECKS.
    """

    id = "manifest-purity"
    tier = "A"
    kind = "gate"
    scope = "global"
    proven_in = ()
    confidence = "inferred"
    tolerates_unparseable = False

    def __init__(self, min_surface=1):
        if min_surface < 1:
            raise ValueError("min_surface must be >= 1")
        self.min_surface = min_surface

    def _state(self, findings, examined_n):
        if findings:
            return State.FAIL
        if examined_n < self.min_surface:
            return State.VACUOUS
        return State.PASS

    def check(self, ws):
        if _MANIFEST not in ws.tracked_files():
            return Result(
                self.id, self._state([], 0),
                examined_n=0, skipped_n=ws.skipped_n, findings=[],
            )
        tree = ws.ast(_MANIFEST)
        if tree is None:
            return Result(
                self.id, State.ERROR, examined_n=0,
                skipped_n=ws.skipped_n, unparseable_n=ws.unparseable_n,
                findings=[],
            )
        findings = _ambient_findings(self.id, _MANIFEST, tree)
        if findings:
            return Result(
                self.id, State.FAIL, examined_n=1,
                skipped_n=ws.skipped_n, findings=findings,
            )
        source = ws.read(_MANIFEST)
        try:
            first = _load(source, "ratch_checks_purity_a")
            second = _load(source, "ratch_checks_purity_b")
        except Exception:
            return Result(
                self.id, State.ERROR, examined_n=0,
                skipped_n=ws.skipped_n, findings=[],
            )
        if not hasattr(first, "CHECKS") or not hasattr(second, "CHECKS"):
            return Result(
                self.id, State.FAIL, examined_n=1,
                skipped_n=ws.skipped_n,
                findings=[Finding(self.id, _MANIFEST, "CHECKS",
                                  message="manifest missing CHECKS")],
            )
        if _fingerprint(first.CHECKS) != _fingerprint(second.CHECKS):
            return Result(
                self.id, State.FAIL, examined_n=1,
                skipped_n=ws.skipped_n,
                findings=[Finding(self.id, _MANIFEST, "repr(CHECKS)",
                                  message="CHECKS fingerprint disagrees")],
            )
        return Result(
            self.id, State.PASS, examined_n=1,
            skipped_n=ws.skipped_n, findings=[],
        )

    def plants(self, ws):
        environ = (
            "import os\n"
            "from ratch.checks.forbidden_literal import NoForbiddenLiteral\n"
            "CHECKS = [NoForbiddenLiteral()]\n"
            "os.environ.get('STRICT')\n"
        )
        yield Plant(
            label="os.environ",
            planted_ws=FakeWorkspace(files={_MANIFEST: environ}),
            expected=(self.id, _MANIFEST, "os.environ"),
        )
        opened = (
            "from ratch.checks.forbidden_literal import NoForbiddenLiteral\n"
            "open('/tmp/x')\n"
            "CHECKS = [NoForbiddenLiteral()]\n"
        )
        yield Plant(
            label="open",
            planted_ws=FakeWorkspace(files={_MANIFEST: opened}),
            expected=(self.id, _MANIFEST, "open"),
        )
        varying = (
            "import uuid\n"
            "CHECKS = [str(uuid.uuid4())]\n"
        )
        yield Plant(
            label="repr(CHECKS)",
            planted_ws=FakeWorkspace(files={_MANIFEST: varying}),
            expected=(self.id, _MANIFEST, "repr(CHECKS)"),
        )

    def fixture(self, kit):
        return FakeWorkspace(files={_MANIFEST: _CLEAN})
