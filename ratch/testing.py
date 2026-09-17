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
                 identity=None, today=None):
        self.files = dict(files)
        self.view = view
        self.run_table = dict(run_table or {})
        self.git_log_text = git_log_text
        self._identity = dict(identity or {"name": "", "email": ""})
        self._today = today or datetime.date.today()
        self.skipped_n = 0
        self.unparseable_n = 0

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

    def git_log(self, rng=None, fmt="%H"):
        return self.git_log_text

    def commit_identity(self):
        return dict(self._identity)

    def now(self):
        return self._today

    def run(self, argv, cwd=None, env=None):
        return self.run_table[tuple(argv)]

    def tmp_tree(self):
        root = pathlib.Path(tempfile.mkdtemp())
        for path, text in self.files.items():
            target = root / path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(text)
        return root
