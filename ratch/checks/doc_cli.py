"""doc-cli-examples-valid check."""
import io
import re
import shlex
from contextlib import redirect_stderr

from ratch.check import Plant
from ratch.cli import build_parser
from ratch.result import Finding, Result, State
from ratch.testing import FakeWorkspace

_TICK = re.compile(r"`(?:python(?:3)?\s+-m\s+)?ratch\s+([^`]+)`")
_FENCE = re.compile(r"```(?:bash|shell|text)?\n(.*?)```", re.S)


class DocCliExamplesValid:
    """Require documented ratch invocations to match argparse.

    Rule:
        Every `ratch …` or `python -m ratch …` example in tracked
        markdown must parse with the real CLI parser.

    Why:
        A copied command that argparse would reject is a rotting
        example; the parser is the SSOT.

    Proven in:
        Regex harvest of ratch invocations, then parse_args.

    Not this:
        Not execution. Not a check of pip or git commands.
    """

    id = "doc-cli-examples-valid"
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
        parser = build_parser()
        findings = []
        examined_n = 0
        for path in ws.tracked_files():
            if not path.endswith(".md"):
                continue
            examined_n += 1
            text = ws.read(path)
            snippets = [m.group(1).strip() for m in _TICK.finditer(text)]
            for block in _FENCE.findall(text):
                for line in block.splitlines():
                    line = line.strip().lstrip("$").strip()
                    if line.startswith("python -m ratch "):
                        snippets.append(line[len("python -m ratch "):])
                    elif line.startswith("python3 -m ratch "):
                        snippets.append(line[len("python3 -m ratch "):])
                    elif line.startswith("ratch "):
                        snippets.append(line[len("ratch "):])
            for rest in snippets:
                try:
                    argv = shlex.split(rest)
                except ValueError:
                    findings.append(
                        Finding(self.id, path, rest,
                                message=f"unquoted: {rest}")
                    )
                    continue
                try:
                    with redirect_stderr(io.StringIO()):
                        parser.parse_args(argv)
                except SystemExit:
                    findings.append(
                        Finding(self.id, path, rest,
                                message=f"unknown ratch argv: {rest}")
                    )
        return Result(
            self.id, self._state(findings, examined_n),
            examined_n=examined_n, skipped_n=ws.skipped_n, findings=findings,
        )

    def plants(self, ws):
        yield Plant(
            label="bad-verb",
            planted_ws=FakeWorkspace(
                files={"README.md": "run `ratch frobnicate` please\n"}
            ),
            expected=(self.id, "README.md", "frobnicate"),
        )

    def fixture(self, kit):
        return FakeWorkspace(files={"README.md": "run `ratch check`\n"})
