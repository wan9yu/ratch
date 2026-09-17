from ratch.result import Result, State, run_exit_code


def run_exit_code_should_return_fail_code_when_fail_and_vacuous_both_present():
    results = [
        Result(check_id="a", state=State.VACUOUS),
        Result(check_id="b", state=State.FAIL),
    ]

    code = run_exit_code(results)

    assert code == 1


def run_exit_code_should_return_zero_when_results_are_empty():
    code = run_exit_code([])

    assert code == 0


def run_exit_code_should_return_error_code_when_an_error_is_present():
    results = [
        Result(check_id="a", state=State.PASS),
        Result(check_id="b", state=State.ERROR),
        Result(check_id="c", state=State.FAIL),
    ]

    code = run_exit_code(results)

    assert code == 3


from ratch.result import Finding


def finding_identity_should_exclude_line_and_count_when_two_findings_differ_only_there():
    early = Finding(rule_id="r", path="p", anchor="x", line=10, count=3)
    late = Finding(rule_id="r", path="p", anchor="x", line=99, count=1)

    assert early.identity == late.identity
    assert early.identity == ("r", "p", "x")
