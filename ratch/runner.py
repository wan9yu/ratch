"""Run a batch of checks and fold their raw results into an exit code.

Each check reports a raw state; the runner re-derives the shipped state
from surface counts and findings, coerces any WARN to ERROR so a soft
gate can never let a run exit clean, and resolves the run to the exit
code of the most severe state present. A crashing check never aborts
the run: its exception becomes an ERROR result for that check alone,
and every other check still runs to completion.

Decision: no asyncio; the Runner schedules checks on a bounded
ThreadPoolExecutor. Rejected: asyncio (it would color every check and
its paired self-tests, forcing the non-stdlib pytest-asyncio, and an
async memo cache dies with pytest's per-test event loop) and a default
ProcessPool (a memoized Workspace does not cross process boundaries).
Because: the proven corpus has zero async specimens; the concurrency
here is I/O-bound subprocess work that threads cover, while pure-CPU
scans stay on ~one core under the GIL, leaving the machine headroom.

Decision: the run-level exit code is the code of the highest-precedence
state present (ERROR > FAIL > VACUOUS > PASS), never a numeric max.
Because: FAIL (a real violation) must outrank VACUOUS even though
VACUOUS's exit code (2) is numerically higher than FAIL's (1).
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


def _worker_count(jobs):
    """Resolve the ``jobs`` setting to a concrete thread-pool size.

    ``"auto"`` leaves headroom on the machine; an int is an explicit
    worker count; a float is a fraction of the available CPUs. Every
    branch floors at 1 so a starved or misconfigured machine still runs.
    """
    cpu_n = os.cpu_count() or 1
    if jobs == "auto":
        return max(1, cpu_n - 2)
    if isinstance(jobs, float):
        return max(1, round(cpu_n * jobs))
    return max(1, jobs)


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

        workers = _worker_count(self.jobs)
        with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as pool:
            pairs = list(pool.map(lambda check: self._run_one(check, ws), checks))

        results = {check.id: result for check, result in pairs}
        gates = [
            result for check, result in pairs
            if getattr(check, "kind", "gate") != "eye"
        ]
        exit_code = run_exit_code(gates)
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
        return check, r
