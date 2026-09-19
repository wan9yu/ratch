"""No-AI-signatures check."""
from __future__ import annotations

import re
from subprocess import CompletedProcess

from ratch.check import Plant
from ratch.result import Finding, Result, State
from ratch.testing import FakeWorkspace


def _log_text(commits):
    """Render commits exactly as ws.git_log(fmt=...) would: each commit is
    ``sha\\0an\\0ae\\0cn\\0ce\\0body\\0`` and git joins records with ``\\n``."""
    recs = ["\x00".join(c) + "\x00" for c in commits]
    return "\n".join(recs) + "\n"


class NoAiSignatures:
    """Forbid AI-attribution shapes anywhere in the full commit history.

    Rule:
        No commit message or committer/author identity, across the entire
        reachable history, may match any configured attribution shape.

    Why:
        An AI attribution trailer or bot identity is a provenance leak that
        survives squash and rebase; only a scan of the whole history proves
        its absence, and a shallow clone that hides history must not read as
        clean.

    Proven in:
        A full-history scan of attribution trailers (Co-Authored-By,
        Generated with, Assisted by, robot glyph, noreply addresses);
        a shallow clone must not read as clean.

    Not this:
        Not a judgment on who or what wrote the code. Only fixed attribution
        SHAPES are rejected; authorship, naming, and content are untouched.
    """

    id = "no-ai-signatures"
    tier = "A"
    kind = "gate"
    scope = "global"
    proven_in = ()
    confidence = "breadth"
    tolerates_unparseable = False

    def __init__(self, patterns=(
        r"Co-Authored-By:",
        r"Generated with",
        r"Assisted by",
        "\N{ROBOT FACE}",
        r"[\w.+-]+@users\.noreply\.[\w.]+",
    ), min_surface=1):
        if min_surface < 1:
            raise ValueError("min_surface must be >= 1")
        self.patterns = tuple(patterns)
        self.min_surface = min_surface

    def _state(self, findings, examined_n):
        if findings:
            return State.FAIL
        if examined_n < self.min_surface:
            return State.VACUOUS
        return State.PASS

    def _is_shallow(self, ws):
        proc = ws.run(["git", "rev-parse", "--is-shallow-repository"])
        return proc.stdout.strip() == "true"

    def check(self, ws):
        findings = []
        examined_n = 0
        if not self._is_shallow(ws):
            raw = ws.git_log(
                rng=None,
                fmt="%H%x00%an%x00%ae%x00%cn%x00%ce%x00%B%x00",
            )
            fields = raw.split("\x00")
            for i in range(0, len(fields) - 5, 6):
                sha = fields[i].strip()
                an, ae, cn, ce, body = fields[i + 1:i + 6]
                examined_n += 1
                haystack = "\n".join([an, ae, cn, ce, body])
                for pattern in self.patterns:
                    # IGNORECASE so GitHub's canonical `Co-authored-by:` casing
                    # (and `generated with` / `assisted by`) is caught too
                    # (resolves Fable finding: default missed lowercase trailers).
                    if re.search(pattern, haystack, re.IGNORECASE):
                        anchor = f"{sha[:9]}:{pattern}"
                        findings.append(
                            Finding(self.id, "<commit>", anchor,
                                    message=f"provenance leak {anchor}")
                        )
        return Result(
            self.id, self._state(findings, examined_n),
            examined_n=examined_n, skipped_n=ws.skipped_n,
            unparseable_n=0, findings=findings,
        )

    def plants(self, ws):
        sha = "0f1e2d3c4b5a6978"
        bot = "".join(["c", "l", "a", "u", "d", "e"])  # vendor token, never typed whole
        body = f"feat: thing\n\nCo-Authored-By: {bot} <{bot}-bot@example.test>\n"
        planted = FakeWorkspace(
            files={"ok.py": "x = 1\n"},
            run_table={("git", "rev-parse", "--is-shallow-repository"):
                       CompletedProcess([], 0, stdout="false\n")},
            git_log_text=_log_text([(sha, "Dev", "dev@example.test",
                                     "Dev", "dev@example.test", body)]),
        )
        yield Plant(
            label="commit:co-authored-by",
            planted_ws=planted,  # type: ignore[arg-type]
            expected=(self.id, "<commit>", f"{sha[:9]}:Co-Authored-By:"),
        )

    def fixture(self, kit):
        return FakeWorkspace(
            files={"clean.py": "x = 1\n"},
            run_table={("git", "rev-parse", "--is-shallow-repository"):
                       CompletedProcess([], 0, stdout="false\n")},
            git_log_text=_log_text([("feedface12345678", "Dev", "dev@example.test",
                                     "Dev", "dev@example.test", "feat: initial\n")]),
        )
