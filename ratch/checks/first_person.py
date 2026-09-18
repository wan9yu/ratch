"""No-first-person check."""
from __future__ import annotations

import fnmatch
import re

from ratch.check import Plant
from ratch.result import Finding, Result, State
from ratch.testing import FakeWorkspace


class NoFirstPerson:
    """Forbid first-person voice in tracked prose.

    Rule:
        No tracked file matching the configured path globs may contain a
        first-person pronoun: the English words I, we, our, us as whole
        words, or the CJK self-reference 我.

    Why:
        First-person voice binds shipped prose to one author's standpoint
        where the project must speak with a single impersonal voice; a
        machine proves the pronoun's absence so no reviewer polices tone
        by eye on every commit.

    Proven in:
        this repository

    Not this:
        Not a grammar, clarity, or readability rule. It never rewrites
        prose and never judges style; it rejects only an exact pronoun
        match, and deliberately exempts the "I/O" boundary term and, under
        the allow-team-we polarity, the collective 我们.
    """

    id = "no-first-person"
    tier = "A"
    kind = "gate"
    scope = "global"
    proven_in = ("this repository",)
    confidence = "breadth"
    tolerates_unparseable = False

    def __init__(self, polarity="forbid-all", tokens_en=("I", "we", "our", "us"),
                 tokens_cjk=("我",), paths=("*.md",), min_surface=1):
        if min_surface < 1:
            raise ValueError("min_surface must be >= 1")
        self.polarity = polarity
        self.paths = tuple(paths)
        self.min_surface = min_surface
        # allow-team-we: drop the collective EN pronouns (keep only "I"),
        # and let the CJK builder exempt 我们.
        if polarity == "allow-team-we":
            self.tokens_en = tuple(t for t in tokens_en if t == "I")
        else:
            self.tokens_en = tuple(tokens_en)
        self.tokens_cjk = tuple(tokens_cjk)
        self._en_rx = self._build_en_rx()
        self._cjk_rx = self._build_cjk_rx()

    def _build_en_rx(self):
        if not self.tokens_en:
            return None
        # Self-host critical (blocking, non-weakenable gate): "I" never matches
        # inside the I/O boundary term, and NO re.IGNORECASE — IGNORECASE would
        # bite a lowercase loop variable `i`, `i.e.`, or the acronym `US`.
        # Match only sentence-case forms: I, We/we, Our/our, Us/us.
        parts = ["I(?!/O)" if t == "I"
                 else f"[{t[0].upper()}{t[0]}]{re.escape(t[1:])}"
                 for t in self.tokens_en]
        return re.compile(r"\b(?:" + "|".join(parts) + r")\b")

    def _build_cjk_rx(self):
        if not self.tokens_cjk:
            return None
        parts = []
        for t in self.tokens_cjk:
            if t == "我" and self.polarity == "allow-team-we":
                parts.append("我(?!们)")  # allow the collective 我们
            else:
                parts.append(re.escape(t))
        return re.compile("|".join(parts))

    def _state(self, findings, examined_n):
        if findings:
            return State.FAIL
        if examined_n < self.min_surface:
            return State.VACUOUS
        return State.PASS

    def check(self, ws):
        files = [p for p in ws.tracked_files()
                 if any(fnmatch.fnmatch(p, g) for g in self.paths)]
        findings = []
        examined_n = 0
        for path in files:
            examined_n += 1
            for lineno, line in enumerate(ws.read(path).splitlines(), start=1):
                if (self._en_rx and self._en_rx.search(line)) or \
                   (self._cjk_rx and self._cjk_rx.search(line)):
                    anchor = " ".join(line.split())
                    findings.append(
                        Finding(self.id, path, anchor, line=lineno,
                                message=f"first-person: {anchor}")
                    )
        return Result(
            self.id, self._state(findings, examined_n),
            examined_n=examined_n, skipped_n=ws.skipped_n,
            unparseable_n=0, findings=findings,
        )
