import importlib

from ratch.registry import discover
from ratch.result import State
from ratch.runner import Runner
from ratch.testing import FakeWorkspace

CommitHeatmap = importlib.import_module(
    "ratch.checks.commit_heatmap"
).CommitHeatmap

_LOG = "\x1e1700000000\nratch/checks/a.py\ntests/t.py\n"


def _ws(log=_LOG):
    return FakeWorkspace(files={"a.py": "x = 1\n"}, git_log_text=log)


def commit_heatmap_should_pass_when_git_log_has_files():
    result = CommitHeatmap().check(_ws())
    assert result.state is State.PASS
    text = str(result.measured.value)
    assert "dirs" in text
    assert "files" in text
    assert "ratch" in text
    assert "tests" in text


def commit_heatmap_should_group_files_under_their_top_directory_when_rendering():
    text = str(CommitHeatmap().check(_ws()).measured.value)
    ratch_at = text.index("ratch/")
    file_at = text.index("ratch/checks/a.py")
    tests_at = text.index("tests/")
    assert ratch_at < file_at < tests_at


def commit_heatmap_should_be_vacuous_when_git_log_is_empty():
    result = CommitHeatmap().check(_ws(""))
    assert result.state is State.VACUOUS


def runner_should_exit_zero_when_only_commit_heatmap_is_vacuous():
    report = Runner(use_nice=False).run(
        [CommitHeatmap()],
        _ws(""),
    )
    assert report.exit_code == 0


def commit_heatmap_should_be_discoverable_when_registered_as_an_entry_point():
    assert discover().get("commit-heatmap") is CommitHeatmap
