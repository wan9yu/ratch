"""no-autoclose-keywords-in-commits check."""
import re

from ratch.check import Plant
from ratch.result import Finding, Result, State
from ratch.testing import FakeWorkspace

_RX = re.compile(
    r"\b(?:fix(?:es|ed)?|close(?:s|d)?|resolve(?:s|d)?)\s+#\d+",
    re.IGNORECASE,
)


class NoAutocloseKeywords:
    """Forbid GitHub auto-close phrases in commit messages.

    Rule:
        git log subjects and bodies must not match fix/close/resolve
        plus a hash-number issue citation.

    Why:
        Agent-written trailers close issues by accident; the message
        is the SSOT that GitHub will act on.

    Proven in:
        git log format subject+body scanned with one regex.

    Not this:
        Not a ban on citing issues in code comments.
    """

    id = "no-autoclose-keywords-in-commits"
    tier = "A"
    kind = "gate"
    scope = "global"
    proven_in = ()
    confidence = "inferred"
    tolerates_unparseable = False

    def __init__(self, min_surface=1):
        if min_surface < 1:
            raise ValueError("min_surface must be >= 1")
        self.min_surface = min_surface

    def _state(self, findings, examined_n):
        if findings:
            return State.FAIL
        if examined_n < self.min_surface:
            return State.VACUOUS
        return State.PASS

    def check(self, ws):
        text = ws.git_log(fmt="%s%n%b%n%x1e")
        records = [block.strip() for block in text.split("\x1e") if block.strip()]
        findings = []
        examined_n = len(records)
        for block in records:
            hit = _RX.search(block)
            if hit:
                findings.append(
                    Finding(self.id, "<commit>", hit.group(0),
                            message=f"autoclose: {hit.group(0)}")
                )
        return Result(
            self.id, self._state(findings, examined_n),
            examined_n=examined_n, skipped_n=ws.skipped_n, findings=findings,
        )

    def plants(self, ws):
        yield Plant(
            label="fixes",
            planted_ws=FakeWorkspace(
                files={"a.py": "x = 1\n"},
                git_log_text="Fixes #12\n\x1e",
            ),
            expected=(self.id, "<commit>", "Fixes #12"),
        )

    def fixture(self, kit):
        return FakeWorkspace(
            files={"a.py": "x = 1\n"},
            git_log_text="tighten the parser\n\x1e",
        )
