"""Test doubles and helpers for exercising checks without a live repo.

Duck-types the Workspace surface from a plain dict so a check can be
run against canned content, and packages the bite contract that proves
a check both catches its planted violation and passes a clean fixture.
"""
import ast
import datetime
import fnmatch
import pathlib
import re
import subprocess
import tempfile

from ratch.result import State


class FakeClock:
    """A clock whose today never moves, for deterministic date logic."""

    def __init__(self, today):
        self._today = today

    def now(self):
        return self._today


class FakeWorkspace:
    """A Workspace-shaped view backed by an in-memory ``{path: text}`` dict."""

    def __init__(self, files, view="worktree", run_table=None, git_log_text="",
                 identity=None, today=None, plugin_classes=None):
        self.files = dict(files)
        self.view = view
        self.run_table = dict(run_table or {})
        self.git_log_text = git_log_text
        self._identity = dict(identity or {"name": "", "email": ""})
        self._today = today or datetime.date.today()
        self.skipped_n = 0
        self.unparseable_n = 0
        self._plugin_classes = dict(plugin_classes or {})

    def tracked_files(self, glob=None):
        paths = sorted(self.files)
        if glob is not None:
            paths = [p for p in paths if fnmatch.fnmatch(p, glob)]
        return paths

    def read(self, path):
        return self.files[path]

    def ast(self, path):
        try:
            return ast.parse(self.read(path))
        except SyntaxError:
            self.unparseable_n += 1
            return None

    def git_grep(self, pattern, cached=False, head=False):
        rx = re.compile(pattern)
        hits = []
        for path in sorted(self.files):
            for lineno, line in enumerate(self.files[path].splitlines(), start=1):
                if rx.search(line):
                    hits.append((path, lineno, line))
        return hits

    def git_log(self, rng=None, fmt="%H", extra=None):
        return self.git_log_text

    def commit_identity(self):
        return dict(self._identity)

    def now(self):
        return self._today

    def run(self, argv, cwd=None, env=None):
        return self.run_table[tuple(argv)]

    def plugin_classes(self):
        return dict(self._plugin_classes)

    def tmp_tree(self):
        root = pathlib.Path(tempfile.mkdtemp())
        for path, text in self.files.items():
            target = root / path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(text)
        return root


def make_tmp_repo(tmp_path, files, user_email="dev@example.test"):
    """Materialize ``files`` into a fresh committed git repo, return its path."""
    repo = pathlib.Path(tmp_path)
    repo.mkdir(parents=True, exist_ok=True)

    def git(*args):
        subprocess.run(["git", *args], cwd=repo, check=True,
                        capture_output=True, text=True)

    git("init", "-q")
    git("config", "user.email", user_email)
    git("config", "user.name", "ratch-dev")
    for path, text in files.items():
        target = repo / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text)
    git("add", "-A")
    git("commit", "-q", "-m", "seed")
    return repo


def assert_bites(check, kit):
    """Assert a check FAILs each planted violation and PASSes its clean fixture."""
    clean = check.fixture(kit)
    plants = list(check.plants(clean))
    if not plants:
        raise AssertionError(f"{check.id}: plants() yielded nothing to bite")
    for plant in plants:
        bitten = check.check(plant.planted_ws)
        if bitten.state is not State.FAIL:
            raise AssertionError(
                f"{check.id}: plant {plant.label!r} did not FAIL "
                f"(got {bitten.state})")
        identities = {finding.identity for finding in bitten.findings}
        if plant.expected not in identities:
            raise AssertionError(
                f"{check.id}: plant {plant.label!r} missing finding "
                f"{plant.expected}")
    clean_result = check.check(clean)
    if clean_result.state is not State.PASS:
        raise AssertionError(
            f"{check.id}: fixture was not clean (got {clean_result.state})")
