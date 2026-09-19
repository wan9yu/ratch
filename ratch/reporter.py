"""Human-readable rendering of a run report.

Decision: rendering is a pure function of the report. Rejected: checks
that print for themselves. Because: one writer keeps the output format in
a single place, and a report stays inspectable without a terminal.
"""
from ratch.result import State

__all__ = ["render_text"]


def render_text(report):
    lines = []
    for check_id, result in report.results.items():
        line = f"{check_id}: {result.state.name}"
        if result.measured is not None:
            line = f"{line} {result.measured.value}"
        lines.append(line)
        if result.state is State.FAIL:
            for finding in result.findings:
                if finding.line is not None:
                    lines.append(f"  {finding.path}:{finding.line}: {finding.message}")
                else:
                    lines.append(f"  {finding.path}: {finding.message}")
    lines.append(f"exit_code {report.exit_code}")
    return "\n".join(lines) + "\n"
