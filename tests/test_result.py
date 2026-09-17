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
