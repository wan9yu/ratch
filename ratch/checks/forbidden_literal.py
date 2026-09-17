"""No-forbidden-literal check."""
from __future__ import annotations

import re

from ratch.check import Plant
from ratch.result import Finding, Result, State
from ratch.testing import FakeWorkspace


def _sample_for(pattern):
    parts = []
    i = 0
    while i < len(pattern):
        if pattern[i] == "[" and i + 2 < len(pattern) and pattern[i + 2] == "]":
            parts.append(pattern[i + 1])
            i += 3
        else:
            parts.append(pattern[i])
            i += 1
    return "".join(parts)


class NoForbiddenLiteral:
    """Forbid a fixed set of author-tool literals anywhere they can leak.

    Rule:
        No tracked file content, tracked filename, or committer identity may
        match any configured forbidden pattern.

    Why:
        An author-tool literal in shipped content, a path, or a commit trailer
        is a provenance leak that no reviewer reliably catches by eye; a
        machine can prove its absence on every commit.

    Proven in:
        this repository

    Not this:
        Not a style or taste rule. Naming, wording, and intent are untouched;
        only an exact pattern match across three mechanical vectors is rejected.
    """

    id = "no-forbidden-literal"
    tier = "A"
    kind = "gate"
    scope = "global"
    proven_in = ("this repository",)
    confidence = "breadth"
    tolerates_unparseable = False

    def __init__(self, patterns=("cl[a]ude",), min_surface=1):
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

    def check(self, ws):
        tracked = ws.tracked_files()
        cached = ws.view == "index"
        head = ws.view == "HEAD"
        findings = []
        for pattern in self.patterns:
            rx = re.compile(pattern)
            for path, line, text in ws.git_grep(pattern, cached=cached, head=head):
                anchor = " ".join(text.split())
                findings.append(
                    Finding(self.id, path, anchor, line=line,
                            message=f"content: {anchor}")
                )
            for path in tracked:
                if rx.search(path):
                    findings.append(
                        Finding(self.id, path, path, message=f"filename: {path}")
                    )
            for field, value in ws.commit_identity().items():
                if rx.search(str(value)):
                    anchor = f"{field}:{value}"
                    findings.append(
                        Finding(self.id, "<commit>", anchor,
                                message=f"commit {anchor}")
                    )
        examined_n = len(tracked) + 1
        return Result(
            self.id, self._state(findings, examined_n),
            examined_n=examined_n, skipped_n=ws.skipped_n,
            unparseable_n=0, findings=findings,
        )

    def plants(self, ws):
        for pattern in self.patterns:
            sample = _sample_for(pattern)

            content_path = "planted/content.py"
            yield Plant(
                label=f"content:{pattern}",
                planted_ws=FakeWorkspace(files={content_path: sample + "\n"}),
                expected=(self.id, content_path, sample),
            )

            fname = f"planted/{sample}_helper.py"
            yield Plant(
                label=f"filename:{pattern}",
                planted_ws=FakeWorkspace(files={fname: "x = 1\n"}),
                expected=(self.id, fname, fname),
            )

            email = sample + "@example.test"
            yield Plant(
                label=f"commit:{pattern}",
                planted_ws=FakeWorkspace(
                    files={"ok.py": "x = 1\n"},
                    identity={"name": "Dev", "email": email,
                              "subject": "init", "body": ""},
                ),
                expected=(self.id, "<commit>", f"email:{email}"),
            )

    def fixture(self, kit):
        return FakeWorkspace(
            files={"clean.py": "x = 1\n"},
            identity={"name": "Dev", "email": "dev@example.test",
                      "subject": "init", "body": ""},
        )
