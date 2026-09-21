import importlib

from ratch.registry import discover
from ratch.result import State
from ratch.runner import Runner
from ratch.testing import FakeWorkspace

_mod = importlib.import_module("ratch.checks.commit_heatmap")
CommitHeatmap = _mod.CommitHeatmap
_parse_log = _mod._parse_log
_growth_char = _mod._growth_char

_LOG = (
    "\x1e1700000000\n"
    "12\t0\tratch/checks/a.py\n"
    "3\t1\ttests/t.py\n"
)


def _ws(log=_LOG):
    return FakeWorkspace(
        files={
            "a.py": "x = 1\n",
            "ratch/checks/a.py": "x = 1\n",
            "tests/t.py": "x = 1\n",
        },
        git_log_text=log,
    )


def parse_log_should_read_insert_and_delete_counts_when_numstat_line_is_plain():
    commits = _parse_log('\x1e1700000000\n12\t3\tratch/cli.py\n')

    found = commits

    expected = [(1700000000, [('ratch/cli.py', 12, 3)])]

    assert found == expected


def parse_log_should_keep_the_path_when_the_entry_is_binary():
    commits = _parse_log('\x1e1700000000\n-\t-\tbin.dat\n')

    found = commits

    expected = [(1700000000, [('bin.dat', None, None)])]

    assert found == expected


def parse_log_should_keep_a_touch_when_net_is_zero():
    commits = _parse_log('\x1e1700000000\n5\t5\ta.py\n')

    found = commits

    expected = [(1700000000, [('a.py', 5, 5)])]

    assert found == expected


def parse_log_should_keep_the_new_path_when_the_entry_is_a_rename():
    commits = _parse_log('\x1e1700000000\n10\t0\told.py => new.py\n')

    found = commits

    expected = [(1700000000, [('new.py', 10, 0)])]

    assert found == expected


def parse_log_should_keep_the_new_path_when_the_entry_is_a_brace_rename():
    commits = _parse_log('\x1e1700000000\n8\t1\tdir/{a.py => b.py}\n')

    found = commits

    expected = [(1700000000, [('dir/b.py', 8, 1)])]

    assert found == expected


def growth_char_should_be_blank_when_net_is_zero():
    found = _growth_char(0)

    expected = ' '

    assert found == expected


def growth_char_should_use_a_positive_glyph_when_net_grows():
    assert _growth_char(1) == "."

    assert _growth_char(12) == ":"

    assert _growth_char(-12) == "~"


def commit_heatmap_should_pass_when_git_log_has_files():
    result = CommitHeatmap().check(_ws())

    assert result.state is State.PASS

    text = str(result.measured.value)
    assert "touches" in text
    assert "growth" in text
    assert "dirs" in text
    assert "files" in text
    assert "ratch" in text
    assert "tests" in text


def commit_heatmap_should_group_files_under_their_top_directory_when_rendering():
    text = str(CommitHeatmap().check(_ws()).measured.value)

    touches = text.split("growth", 1)[0]

    ratch_at = touches.index("ratch/")
    file_at = touches.index("ratch/checks/a.py")
    tests_at = touches.index("tests/")
    assert ratch_at < file_at < tests_at


def commit_heatmap_should_be_vacuous_when_git_log_is_empty():
    result = CommitHeatmap().check(_ws(''))

    found = result.state

    expected = State.VACUOUS

    assert found is expected


def runner_should_exit_zero_when_only_commit_heatmap_is_vacuous():
    report = Runner(use_nice=False).run([CommitHeatmap()], _ws(''))

    found = report.exit_code

    expected = 0

    assert found == expected


def commit_heatmap_should_be_discoverable_when_registered_as_an_entry_point():
    catalog = discover()

    loaded = catalog.get("commit-heatmap")

    assert loaded is CommitHeatmap
