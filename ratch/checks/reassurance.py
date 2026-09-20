"""no-reassurance-words check."""
from ratch.check import Plant
from ratch.result import Finding, Result, State
from ratch.testing import FakeWorkspace

# Assembled so the guard file never contains the banned tokens.
_WORDS = (
    "".join(["放", "心"]),
    "rest assured",
    "don't worry",
)


class NoReassuranceWords:
    """Forbid reassurance words that tell the reader to stop checking.

    Rule:
        Tracked markdown must not contain configured reassurance
        phrases.

    Why:
        A phrase that tells the reader to stop verifying is the
        opposite of a ratchet: the machine must keep proving, not
        soothing.

    Proven in:
        Record prose scanned for a small frozen phrase list; the
        guard file never spells a banned token in one piece.

    Not this:
        Not a ban on confidence in code comments. Markdown only.
    """

    id = "no-reassurance-words"
    tier = "A"
    kind = "gate"
    scope = "global"
    proven_in = ()
    confidence = "inferred"
    tolerates_unparseable = False

    def __init__(self, min_surface=1, phrases=None):
        if min_surface < 1:
            raise ValueError("min_surface must be >= 1")
        self.min_surface = min_surface
        self.phrases = _WORDS if phrases is None else tuple(phrases)

    def _state(self, findings, examined_n):
        if findings:
            return State.FAIL
        if examined_n < self.min_surface:
            return State.VACUOUS
        return State.PASS

    def check(self, ws):
        findings = []
        examined_n = 0
        for path in ws.tracked_files():
            if not path.endswith(".md"):
                continue
            examined_n += 1
            text = ws.read(path)
            lowered = text.lower()
            for phrase in self.phrases:
                if phrase.lower() in lowered:
                    findings.append(
                        Finding(self.id, path, phrase,
                                message=f"reassurance: {phrase}")
                    )
        return Result(
            self.id, self._state(findings, examined_n),
            examined_n=examined_n, skipped_n=ws.skipped_n, findings=findings,
        )

    def plants(self, ws):
        leak = _WORDS[0]
        yield Plant(
            label="soothe",
            planted_ws=FakeWorkspace(files={"note.md": leak + "\n"}),
            expected=(self.id, "note.md", leak),
        )

    def fixture(self, kit):
        return FakeWorkspace(files={"note.md": "a machine can prove it.\n"})
