"""ratch — a ratchet for repository invariants.

Decision: code is the single source of truth (SSOT); docs are pointers,
generated, or signed. Rejected: a docs/ tree. Because: a copied fact rots.
"""

from ratch.result import (
    EXIT,
    PRECEDENCE,
    Finding,
    MeasuredValue,
    MState,
    Result,
    State,
    run_exit_code,
)

__all__ = [
    "EXIT",
    "PRECEDENCE",
    "Finding",
    "MeasuredValue",
    "MState",
    "Result",
    "State",
    "run_exit_code",
]
