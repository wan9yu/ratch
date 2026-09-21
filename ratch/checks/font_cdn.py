"""No-external-font-cdn check."""
from __future__ import annotations

from ratch.check import Plant
from ratch.result import Finding, Result, State
from ratch.testing import FakeWorkspace

_CDNS = (
    "fonts.googleapis.com",
    "fonts.gstatic.com",
    "typekit.net",
)
_WEB = (".html", ".css", ".js")


class NoExternalFontCdn:
    """Forbid hosted webfont CDNs in shipped HTML/CSS/JS.

    Rule:
        Tracked .html/.css/.js files must not contain known font-CDN
        host substrings.

    Why:
        A remote font fetch is a privacy and availability leak; fonts
        must be served from the same origin.

    Proven in:
        Shipped HTML/CSS/JS serves fonts locally, not from a webfont
        CDN.

    Not this:
        Not a ban on local @font-face. Not a scan of markdown prose.
    """

    id = "no-external-font-cdn"
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
            return State.NOT_APPLICABLE
        return State.PASS

    def check(self, ws):
        findings = []
        examined_n = 0
        for path in ws.tracked_files():
            if not path.endswith(_WEB):
                continue
            examined_n += 1
            text = ws.read(path)
            for cdn in _CDNS:
                if cdn in text:
                    findings.append(
                        Finding(self.id, path, cdn,
                                message=f"font cdn: {cdn}")
                    )
        return Result(
            self.id, self._state(findings, examined_n),
            examined_n=examined_n, skipped_n=ws.skipped_n, findings=findings,
        )

    def plants(self, ws):
        host = "fonts.googleapis.com"
        yield Plant(
            label="google-fonts",
            planted_ws=FakeWorkspace(
                files={"static/x.css": f"@import url(https://{host}/css);\n"}
            ),
            expected=(self.id, "static/x.css", host),
        )

    def fixture(self, kit):
        return FakeWorkspace(files={"static/x.css": "body { font-family: sans-serif; }\n"})
