"""Run a batch of checks and fold their raw results into an exit code.

Each check reports a raw state; the runner re-derives the shipped state
from surface counts and findings, coerces any WARN to ERROR so a soft
gate can never let a run exit clean, and resolves the run to the exit
code of the most severe state present. A crashing check never aborts
the run: its exception becomes an ERROR result for that check alone,
and every other check still runs to completion.
"""
from ratch.result import State


def derive_state(raw, examined_n, unparseable_n, tolerates_unparseable,
                  findings, min_surface, has_unexpired_waiver, skipped_n=0):
    """Re-derive the shipped state for one check from its raw report.

    ``addressable`` is everything the check could have ruled on: what
    it examined, what it skipped, and what it could not parse. A check
    with nothing addressable and an unexpired waiver is not applicable
    rather than vacuous.
    """
    if raw is State.ERROR:
        return State.ERROR
    if unparseable_n > 0 and not tolerates_unparseable:
        return State.FAIL
    if findings:
        return State.FAIL
    addressable = examined_n + skipped_n + unparseable_n
    if addressable == 0 and has_unexpired_waiver:
        return State.NOT_APPLICABLE
    if examined_n < min_surface:
        return State.VACUOUS
    return State.PASS
