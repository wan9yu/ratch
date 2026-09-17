"""Run a batch of checks and fold their raw results into an exit code.

Each check reports a raw state; the runner re-derives the shipped state
from surface counts and findings, coerces any WARN to ERROR so a soft
gate can never let a run exit clean, and resolves the run to the exit
code of the most severe state present. A crashing check never aborts
the run: its exception becomes an ERROR result for that check alone,
and every other check still runs to completion.
"""
import concurrent.futures
import os
from dataclasses import dataclass

from ratch.result import Result, State, run_exit_code


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


@dataclass
class RunReport:
    view: str
    results: dict
    exit_code: int


class Runner:
    """Runs checks across a thread pool and folds them into a RunReport."""

    def __init__(self, jobs="auto", nice=10, use_nice=False):
        self.jobs = jobs
        self.nice = nice
        self.use_nice = use_nice

    def run(self, checks, ws):
        if self.use_nice:
            os.nice(self.nice)

        workers = max(1, (os.cpu_count() or 1) - 2)
        with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as pool:
            pairs = list(pool.map(lambda check: self._run_one(check, ws), checks))

        results = {check_id: result for check_id, result in pairs}
        exit_code = run_exit_code(results.values())
        return RunReport(view=ws.view, results=results, exit_code=exit_code)

    def _run_one(self, check, ws):
        # A crashing check must never abort the run or count as a pass:
        # capture it as this check's own ERROR result and move on.
        try:
            r = check.check(ws)
        except Exception:
            r = Result(check_id=check.id, state=State.ERROR)

        # EXIT/PRECEDENCE carry no WARN entry, so any WARN that survived
        # here would silently exit 0. Coerce every kind's WARN to ERROR.
        if r.state is State.WARN:
            r.state = State.ERROR

        min_surface = getattr(check, "min_surface", 1)
        r.state = derive_state(
            r.state, r.examined_n, r.unparseable_n, check.tolerates_unparseable,
            r.findings, min_surface, False, skipped_n=r.skipped_n,
        )
        return check.id, r
