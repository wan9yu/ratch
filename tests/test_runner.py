"""Behavior specs for RunReport, derive_state, and Runner."""
from ratch.result import Finding, State
from ratch.runner import derive_state


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
