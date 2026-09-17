"""Tests for the git-backed Workspace over the worktree/index/HEAD views."""

import subprocess

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


def tracked_files_should_skip_symlink_and_increment_skipped_n_when_view_is_worktree(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "init", "-q", str(repo)], check=True)
    subprocess.run(["git", "-C", str(repo), "config", "user.email", "dev@example.test"], check=True)
    subprocess.run(["git", "-C", str(repo), "config", "user.name", "dev"], check=True)
    (repo / "real.py").write_text("VALUE = 1\n")
    (repo / "link.py").symlink_to("real.py")
    subprocess.run(["git", "-C", str(repo), "add", "-A"], check=True)
    subprocess.run(["git", "-C", str(repo), "commit", "-q", "-m", "init"], check=True)

    ws = Workspace(repo, "worktree")
    tracked = ws.tracked_files("*.py")

    assert "real.py" in tracked
    assert "link.py" not in tracked
    assert ws.skipped_n >= 1
