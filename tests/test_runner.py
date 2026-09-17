"""Behavior specs for RunReport, derive_state, and Runner."""
from ratch.result import Finding, Result, State
from ratch.runner import Runner, derive_state
from ratch.testing import FakeWorkspace


def derive_state_should_be_fail_when_findings_present_below_min_surface():
    finding = Finding(rule_id="r", path="p", anchor="a")

    state = derive_state(State.PASS, examined_n=0, unparseable_n=0,
                          tolerates_unparseable=True, findings=[finding],
                          min_surface=5, has_unexpired_waiver=False)

    assert state is State.FAIL


def derive_state_should_be_vacuous_when_below_min_surface_and_no_findings():
    state = derive_state(State.PASS, examined_n=1, unparseable_n=0,
                          tolerates_unparseable=True, findings=[],
                          min_surface=5, has_unexpired_waiver=False)

    assert state is State.VACUOUS


def derive_state_should_be_not_applicable_when_nothing_addressable_and_waiver_unexpired():
    state = derive_state(State.PASS, examined_n=0, unparseable_n=0,
                          tolerates_unparseable=True, findings=[],
                          min_surface=1, has_unexpired_waiver=True, skipped_n=0)

    assert state is State.NOT_APPLICABLE


class _StubCheck:
    tolerates_unparseable = True

    def __init__(self, id, kind, result):
        self.id = id
        self.kind = kind
        self._result = result

    def check(self, ws):
        return self._result


class _RaisingCheck:
    id = "boom"
    kind = "check"
    tolerates_unparseable = True

    def check(self, ws):
        raise RuntimeError("boom")


def runner_should_exit_three_when_gate_check_returns_warn():
    gate = _StubCheck(id="warn-gate", kind="gate",
                       result=Result(check_id="warn-gate", state=State.WARN,
                                     examined_n=3))

    report = Runner().run([gate], FakeWorkspace({}))

    assert report.exit_code == 3


def runner_should_exit_one_when_fail_outranks_vacuous():
    failing = _StubCheck(id="fails", kind="check",
                          result=Result(check_id="fails", state=State.FAIL,
                                        examined_n=9,
                                        findings=[Finding("fails", "p", "a")]))
    thin = _StubCheck(id="thin", kind="check",
                       result=Result(check_id="thin", state=State.PASS,
                                     examined_n=0))

    report = Runner().run([failing, thin], FakeWorkspace({}))

    assert report.exit_code == 1


def runner_should_exit_three_when_non_gate_check_returns_warn():
    # WARN has no EXIT/PRECEDENCE entry of its own; a plain (non-gate)
    # check returning WARN must still be coerced to ERROR, not ignored.
    warn_check = _StubCheck(id="warn-plain", kind="check",
                             result=Result(check_id="warn-plain", state=State.WARN,
                                           examined_n=3))

    report = Runner(use_nice=False).run([warn_check], FakeWorkspace({}))

    assert report.exit_code == 3


def runner_should_mark_error_and_keep_running_other_checks_when_a_check_raises():
    raising = _RaisingCheck()
    ok = _StubCheck(id="ok", kind="check",
                     result=Result(check_id="ok", state=State.PASS, examined_n=3))

    report = Runner(use_nice=False).run([raising, ok], FakeWorkspace({}))

    assert report.results["boom"].state is State.ERROR
    assert report.results["ok"].state is State.PASS
    assert report.exit_code == 3
