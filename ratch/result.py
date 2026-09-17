"""Outcome vocabulary shared by every check and by the runner.

A check reports a Result; the runner folds Results into an exit code by
severity precedence. States are ordered once, here, so no downstream
module re-invents the ranking.
"""

import enum
from collections.abc import Iterable
from dataclasses import dataclass, field

State = enum.Enum('State', 'PASS FAIL VACUOUS NOT_APPLICABLE WARN ERROR')
MState = enum.Enum('MState', 'MEASURED ABSENT PARTIAL VACUOUS')

EXIT: dict[State, int] = {
    State.PASS: 0,
    State.NOT_APPLICABLE: 0,
    State.FAIL: 1,
    State.VACUOUS: 2,
    State.ERROR: 3,
}

PRECEDENCE: tuple[State, ...] = (
    State.ERROR,
    State.FAIL,
    State.VACUOUS,
    State.NOT_APPLICABLE,
    State.PASS,
)


@dataclass(frozen=True)
class Finding:
    rule_id: str
    path: str
    anchor: str
    line: int | None = None
    count: int = 1
    message: str = ""


@dataclass(frozen=True)
class MeasuredValue:
    value: object
    state: MState
    source: str
    measured_at: object
    threshold: object | None = None


@dataclass
class Result:
    check_id: str
    state: State
    examined_n: int = 0
    skipped_n: int = 0
    unparseable_n: int = 0
    findings: list[Finding] = field(default_factory=list)
    measured: MeasuredValue | None = None


def run_exit_code(results: Iterable[Result]) -> int:
    present = {r.state for r in results}
    for state in PRECEDENCE:
        if state in present:
            return EXIT[state]
    return 0
