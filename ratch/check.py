"""The Check contract: the shape every rule instance must present.

A check is configured by instantiation — constructor arguments on the
instance, never a config file. The runtime-checkable Protocol lets the
runner accept any object that exposes this shape, keeping rules and the
engine decoupled.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from typing import Protocol, runtime_checkable

from ratch.result import Result


@dataclass(frozen=True)
class Plant:
    label: str
    planted_ws: Workspace
    expected: tuple[str, str, str]


@runtime_checkable
class Check(Protocol):
    id: str
    tier: str
    kind: str
    scope: str
    proven_in: tuple[str, ...]
    confidence: str
    tolerates_unparseable: bool

    def check(self, ws) -> Result: ...

    def plants(self, ws) -> Iterable[Plant]: ...

    def fixture(self, kit) -> Workspace: ...
