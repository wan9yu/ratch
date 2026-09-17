"""Behavior specs for render_text."""
from ratch.reporter import render_text
from ratch.result import Finding, Result, State
from ratch.runner import RunReport


def render_text_should_include_a_fail_line_with_path_and_message_when_a_check_fails():
    finding = Finding(rule_id="no-forbidden-literal", path="pkg/mod.py", anchor="pkg/mod.py", line=7, message="banned literal present")
    result = Result(check_id="no-forbidden-literal", state=State.FAIL, findings=[finding])
    report = RunReport(view="worktree", results={"no-forbidden-literal": result}, exit_code=1)

    rendered = render_text(report)

    assert "no-forbidden-literal: FAIL" in rendered
    assert "pkg/mod.py:7: banned literal present" in rendered
    assert "exit_code 1" in rendered


def render_text_should_use_path_and_message_without_line_when_a_finding_has_no_line():
    finding = Finding(rule_id="no-forbidden-literal", path="pkg/x.py", anchor="pkg/x.py", line=None, message="banned literal present")
    result = Result(check_id="no-forbidden-literal", state=State.FAIL, findings=[finding])
    report = RunReport(view="worktree", results={"no-forbidden-literal": result}, exit_code=1)

    rendered = render_text(report)

    assert "pkg/x.py: banned literal present" in rendered
    assert "pkg/x.py:None:" not in rendered
    assert "pkg/x.py::" not in rendered
