import importlib

from ratch.registry import discover
from ratch.result import State
from ratch.runner import Runner
from ratch.testing import FakeWorkspace

CommitHeatmap = importlib.import_module(
    "ratch.checks.commit_heatmap"
).CommitHeatmap


def commit_heatmap_should_pass_when_git_log_has_timestamps():
    ws = FakeWorkspace(files={"a.py": "x = 1\n"}, git_log_text="1700000000\n")
    result = CommitHeatmap().check(ws)
    assert result.state is State.PASS
    assert result.measured is not None
    assert "/" in str(result.measured.value)


def commit_heatmap_should_be_vacuous_when_git_log_is_empty():
    result = CommitHeatmap().check(
        FakeWorkspace(files={"a.py": "x = 1\n"}, git_log_text="")
    )
    assert result.state is State.VACUOUS


def runner_should_exit_zero_when_only_commit_heatmap_is_vacuous():
    report = Runner(use_nice=False).run(
        [CommitHeatmap()],
        FakeWorkspace(files={"a.py": "x = 1\n"}, git_log_text=""),
    )
    assert report.exit_code == 0


def commit_heatmap_should_be_discoverable_when_registered_as_an_entry_point():
    assert discover().get("commit-heatmap") is CommitHeatmap
