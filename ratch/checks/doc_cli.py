"""doc-cli-examples-valid check."""
import io
import re
import shlex
from contextlib import redirect_stderr

from ratch.check import Plant
from ratch.checks import match_globs
from ratch.cli import build_parser
from ratch.result import Finding, Result, State
from ratch.testing import FakeWorkspace

_FENCE = re.compile(r"```(?:bash|shell|text)?\n(.*?)```", re.S)


class DocCliExamplesValid:
    """Require documented ratch invocations to match argparse.

    Rule:
        Every `prog …` or `python -m prog …` example in selected
        markdown must parse with parser(). Default prog is ratch.
        paths=None scans every tracked .md (this repo's default).

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

    def __init__(self, min_surface=1, parser=None, prog="ratch", paths=None):
        if min_surface < 1:
            raise ValueError("min_surface must be >= 1")
        self.min_surface = min_surface
        self._parser = parser or build_parser
        self.prog = prog
        self.paths = None if paths is None else tuple(paths)

    def _state(self, findings, examined_n):
        if findings:
            return State.FAIL
        if examined_n < self.min_surface:
            return State.VACUOUS
        return State.PASS

    def check(self, ws):
        parser = self._parser()
        tick = re.compile(
            r"`(?:python(?:3)?\s+-m\s+)?"
            + re.escape(self.prog)
            + r"\s+([^`]+)`"
        )
        findings = []
        examined_n = 0
        for path in ws.tracked_files():
            if not path.endswith(".md"):
                continue
            if not match_globs(path, self.paths):
                continue
            examined_n += 1
            text = ws.read(path)
            snippets = [m.group(1).strip() for m in tick.finditer(text)]
            prefixes = (
                f"python3 -m {self.prog} ",
                f"python -m {self.prog} ",
                f"{self.prog} ",
            )
            for block in _FENCE.findall(text):
                for line in block.splitlines():
                    line = line.strip().lstrip("$").strip()
                    for prefix in prefixes:
                        if line.startswith(prefix):
                            snippets.append(line[len(prefix):])
                            break
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
