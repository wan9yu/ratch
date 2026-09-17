"""Git-backed view over a repository under a single named view.

Reads never mutate the repository; the counters accumulate what a scan
declined to examine so a check can distinguish an empty surface from a
skipped one.
"""

import ast as _ast
import datetime
import io
import pathlib
import subprocess
import tarfile
import tempfile


class Workspace:
    def __init__(self, repo_root, view="worktree"):
        self.repo_root = pathlib.Path(repo_root)
        self.view = view
        self.skipped_n = 0
        self.unparseable_n = 0
        self._read_cache = {}
        self._ast_cache = {}
        self._tracked_cache = {}

    def _run_git(self, args, text=True):
        return subprocess.run(
            ["git", "-C", str(self.repo_root)] + args,
            capture_output=True,
            text=text,
        )

    def read(self, path):
        key = (self.view, path)
        if key in self._read_cache:
            return self._read_cache[key]
        if self.view == "worktree":
            data = (self.repo_root / path).read_bytes()
        else:
            spec = f":{path}" if self.view == "index" else f"HEAD:{path}"
            data = self._run_git(["show", spec], text=False).stdout
        text = data.decode("utf-8", errors="replace")
        self._read_cache[key] = text
        return text

    def tracked_files(self, glob=None):
        key = (self.view, glob)
        if key in self._tracked_cache:
            return list(self._tracked_cache[key])
        args = ["ls-files", "-s", "-z"]
        if glob is not None:
            args += ["--", glob]
        out = self._run_git(args).stdout
        kept = []
        for entry in out.split("\x00"):
            if not entry:
                continue
            meta, _, path = entry.partition("\t")
            mode = meta.split()[0]
            if mode in ("120000", "160000"):
                self.skipped_n += 1
                continue
            if b"\x00" in self._raw_bytes(path):
                self.skipped_n += 1
                continue
            kept.append(path)
        self._tracked_cache[key] = list(kept)
        return kept

    def _raw_bytes(self, path):
        if self.view == "worktree":
            return (self.repo_root / path).read_bytes()
        spec = f":{path}" if self.view == "index" else f"HEAD:{path}"
        return self._run_git(["show", spec], text=False).stdout

    def ast(self, path):
        key = (self.view, path)
        if key in self._ast_cache:
            return self._ast_cache[key]
        try:
            tree = _ast.parse(self.read(path))
        except SyntaxError:
            self.unparseable_n += 1
            tree = None
        self._ast_cache[key] = tree
        return tree

    def git_grep(self, pattern, cached=False, head=False):
        args = ["grep", "-n", "-z", "-I", "-E"]
        if cached:
            args.append("--cached")
        args += ["-e", pattern]
        if head:
            args.append("HEAD")
        proc = self._run_git(args)
        if proc.returncode not in (0, 1):
            raise RuntimeError(proc.stderr)
        hits = []
        for record in proc.stdout.split("\n"):
            if not record:
                continue
            # `git grep -n -z` emits `path\x00lineno\x00text` (both separators
            # are NUL), not `path\x00lineno:text`. Split on NUL, not ":".
            parts = record.split("\x00", 2)
            if len(parts) != 3:
                continue
            path, lineno, text = parts
            hits.append((path, int(lineno), text))
        return hits

    def commit_identity(self):
        if self.view == "HEAD":
            fmt = "%an%x00%ae%x00%cn%x00%ce%x00%s%x00%B"
            out = self._run_git(["show", "-s", "--format=" + fmt, "HEAD"]).stdout
            name, email, committer_name, committer_email, subject, body = out.split("\x00", 5)
            return {
                "name": name,
                "email": email,
                "committer_name": committer_name,
                "committer_email": committer_email,
                "subject": subject,
                "body": body,
            }
        name = self._run_git(["config", "user.name"]).stdout.strip()
        email = self._run_git(["config", "user.email"]).stdout.strip()
        return {"name": name, "email": email}
