"""Git-backed view over a repository under a single named view.

Reads never mutate the repository; the counters accumulate what a scan
declined to examine so a check can distinguish an empty surface from a
skipped one.
"""

import pathlib


class Workspace:
    def __init__(self, repo_root, view="worktree"):
        self.repo_root = pathlib.Path(repo_root)
        self.view = view
        self.skipped_n = 0
        self.unparseable_n = 0
        self._read_cache = {}
        self._ast_cache = {}
        self._tracked_cache = {}

    def read(self, path):
        key = (self.view, path)
        if key in self._read_cache:
            return self._read_cache[key]
        data = (self.repo_root / path).read_bytes()
        text = data.decode("utf-8", errors="replace")
        self._read_cache[key] = text
        return text
