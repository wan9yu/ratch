import importlib

from ratch.result import State
from ratch.testing import FakeWorkspace, assert_bites

NoExternalFontCdn = importlib.import_module("ratch.checks.font_cdn").NoExternalFontCdn


def no_external_font_cdn_should_fail_when_css_points_at_google_fonts():
    host = "fonts.googleapis.com"

    ws = FakeWorkspace(files={"static/x.css": f"@import url(https://{host}/css);\n"})

    result = NoExternalFontCdn().check(ws)
    assert result.state is State.FAIL
    assert any(
        f.identity == ("no-external-font-cdn", "static/x.css", host)
        for f in result.findings
    )


def no_external_font_cdn_should_pass_when_css_uses_local_fonts():
    ws = FakeWorkspace(files={"static/x.css": "body { font-family: sans-serif; }\n"})

    result = NoExternalFontCdn().check(ws)

    assert result.state is State.PASS


def no_external_font_cdn_should_be_not_applicable_when_no_web_file_is_present():
    ws = FakeWorkspace(files={"a.py": "x = 1\n"})

    result = NoExternalFontCdn().check(ws)

    assert result.state is State.NOT_APPLICABLE


def no_external_font_cdn_should_bite_its_plants_when_checked_against_its_own_fixture(tmp_path):
    check = NoExternalFontCdn()

    assert_bites(check, tmp_path)

    assert check.id


def no_external_font_cdn_should_be_discoverable_when_registered_as_an_entry_point():
    from ratch.registry import discover

    found = discover().get('no-external-font-cdn')

    expected = NoExternalFontCdn

    assert found is expected
