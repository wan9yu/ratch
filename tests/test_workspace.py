"""Tests for the git-backed Workspace over the worktree/index/HEAD views."""

from ratch.testing import make_tmp_repo
from ratch.workspace import Workspace


def read_should_return_file_content_when_view_is_worktree(tmp_path):
    repo = make_tmp_repo(tmp_path, {"a.py": "X = 1\n"})

    ws = Workspace(repo, "worktree")
    content = ws.read("a.py")

    assert content == "X = 1\n"


def read_should_return_committed_content_when_view_is_head(tmp_path):
    repo = make_tmp_repo(tmp_path, {"a.py": "COMMITTED = 1\n"})
    (repo / "a.py").write_text("WORKTREE = 2\n")

    ws = Workspace(repo, "HEAD")
    content = ws.read("a.py")

    assert content == "COMMITTED = 1\n"
