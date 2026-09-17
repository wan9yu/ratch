"""Tests for the git-backed Workspace over the worktree/index/HEAD views."""

import datetime
import os
import pathlib
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


def read_should_return_staged_content_when_view_is_index(tmp_path):
    repo = make_tmp_repo(tmp_path, {"a.py": "HEAD = 1\n"})
    (repo / "a.py").write_text("INDEX = 2\n")
    subprocess.run(["git", "-C", str(repo), "add", "a.py"], check=True)
    (repo / "a.py").write_text("WORKTREE = 3\n")

    ws = Workspace(repo, "index")
    content = ws.read("a.py")

    assert content == "INDEX = 2\n"


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


def tracked_files_should_skip_gitlink_and_increment_skipped_n_when_view_is_worktree(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "init", "-q", str(repo)], check=True)
    subprocess.run(["git", "-C", str(repo), "config", "user.email", "dev@example.test"], check=True)
    subprocess.run(["git", "-C", str(repo), "config", "user.name", "dev"], check=True)
    (repo / "real.py").write_text("VALUE = 1\n")
    subprocess.run(["git", "-C", str(repo), "add", "real.py"], check=True)
    fake_sha = "1" * 40
    subprocess.run(
        ["git", "-C", str(repo), "update-index", "--add", "--cacheinfo",
         f"160000,{fake_sha},sub"],
        check=True,
    )
    subprocess.run(["git", "-C", str(repo), "commit", "-q", "-m", "init"], check=True)

    ws = Workspace(repo, "worktree")
    tracked = ws.tracked_files()

    assert "real.py" in tracked
    assert "sub" not in tracked
    assert ws.skipped_n >= 1


def tracked_files_should_skip_binary_file_and_increment_skipped_n_when_view_is_worktree(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "init", "-q", str(repo)], check=True)
    subprocess.run(["git", "-C", str(repo), "config", "user.email", "dev@example.test"], check=True)
    subprocess.run(["git", "-C", str(repo), "config", "user.name", "dev"], check=True)
    (repo / "real.py").write_text("VALUE = 1\n")
    (repo / "blob.bin").write_bytes(b"a\x00b")
    subprocess.run(["git", "-C", str(repo), "add", "-A"], check=True)
    subprocess.run(["git", "-C", str(repo), "commit", "-q", "-m", "init"], check=True)

    ws = Workspace(repo, "worktree")
    tracked = ws.tracked_files()

    assert "real.py" in tracked
    assert "blob.bin" not in tracked
    assert ws.skipped_n >= 1


def read_should_return_cached_content_when_called_twice_after_file_removal(tmp_path):
    repo = make_tmp_repo(tmp_path, {"a.py": "X = 1\n"})
    ws = Workspace(repo, "worktree")

    first = ws.read("a.py")
    (repo / "a.py").unlink()
    second = ws.read("a.py")

    assert first == "X = 1\n"
    assert second == "X = 1\n"


def tracked_files_should_return_cached_result_when_called_twice_with_same_glob(tmp_path):
    repo = make_tmp_repo(tmp_path, {"a.py": "X = 1\n", "b.py": "Y = 2\n"})
    ws = Workspace(repo, "worktree")

    first = ws.tracked_files("*.py")

    def _forbidden_run_git(*args, **kwargs):
        raise AssertionError(
            "git should not be re-invoked for a memoized tracked_files call")

    ws._run_git = _forbidden_run_git
    second = ws.tracked_files("*.py")

    assert second == first


def ast_should_return_none_and_count_once_when_source_has_syntax_error(tmp_path):
    repo = make_tmp_repo(tmp_path, {"broken.py": "def (:\n    pass\n"})

    ws = Workspace(repo, "worktree")
    first = ws.ast("broken.py")
    second = ws.ast("broken.py")

    assert first is None
    assert second is None
    assert ws.unparseable_n == 1


def git_grep_should_find_planted_token_with_its_line_number_when_pattern_matches(tmp_path):
    token = "cl" + "aude"
    repo = make_tmp_repo(tmp_path, {"hit.py": "a = 1\nbad = '" + token + "'\n"})

    ws = Workspace(repo, "worktree")
    hits = ws.git_grep("cl[a]ude")

    assert any(path == "hit.py" and line == 2 for path, line, _ in hits)


def commit_identity_should_return_head_author_email_when_view_is_head(tmp_path):
    repo = make_tmp_repo(tmp_path, {"a.py": "X = 1\n"}, user_email="author@example.test")

    ws = Workspace(repo, "HEAD")
    identity = ws.commit_identity()

    assert identity["email"] == "author@example.test"


def commit_identity_should_include_committer_fields_distinct_from_author_when_view_is_head(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "init", "-q", str(repo)], check=True)
    subprocess.run(["git", "-C", str(repo), "config", "user.email", "author@example.test"], check=True)
    subprocess.run(["git", "-C", str(repo), "config", "user.name", "author-dev"], check=True)
    (repo / "a.py").write_text("X = 1\n")
    subprocess.run(["git", "-C", str(repo), "add", "-A"], check=True)
    env = dict(os.environ)
    env["GIT_COMMITTER_NAME"] = "committer-dev"
    env["GIT_COMMITTER_EMAIL"] = "committer@example.test"
    subprocess.run(["git", "-C", str(repo), "commit", "-q", "-m", "seed"], check=True, env=env)

    ws = Workspace(repo, "HEAD")
    identity = ws.commit_identity()

    assert identity["name"] == "author-dev"
    assert identity["email"] == "author@example.test"
    assert identity["committer_name"] == "committer-dev"
    assert identity["committer_email"] == "committer@example.test"


def commit_identity_should_return_empty_email_when_config_unset_and_view_is_index(tmp_path, monkeypatch):
    repo = tmp_path / "bare"
    repo.mkdir()
    empty = tmp_path / "none.gitconfig"
    monkeypatch.setenv("GIT_CONFIG_GLOBAL", str(empty))
    monkeypatch.setenv("GIT_CONFIG_SYSTEM", str(empty))
    subprocess.run(["git", "init", "-q", str(repo)], check=True)

    ws = Workspace(repo, "index")
    identity = ws.commit_identity()

    assert identity["email"] == ""
    assert identity["name"] == ""


def git_log_should_return_head_hash_matching_run_rev_parse_when_no_range_given(tmp_path):
    repo = make_tmp_repo(tmp_path, {"a.py": "X = 1\n"})

    ws = Workspace(repo, "worktree")
    log = ws.git_log()
    head = ws.run(["git", "-C", str(repo), "rev-parse", "HEAD"]).stdout.strip()

    assert log.strip() == head


def now_should_return_todays_date_when_called(tmp_path):
    repo = make_tmp_repo(tmp_path, {"a.py": "X = 1\n"})

    ws = Workspace(repo, "worktree")
    today = ws.now()

    assert today == datetime.date.today()
