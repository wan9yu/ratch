from ratch.checks.manifest_purity import ManifestPurity
from ratch.result import State
from ratch.testing import FakeWorkspace, assert_bites

_CLEAN = (
    "from ratch.checks.forbidden_literal import NoForbiddenLiteral\n"
    "CHECKS = [NoForbiddenLiteral()]\n"
)


def manifest_purity_should_be_vacuous_when_no_manifest_file_exists():
    ws = FakeWorkspace(files={"ok.py": "x = 1\n"})

    result = ManifestPurity().check(ws)

    assert result.state is State.VACUOUS
    assert result.examined_n == 0


def manifest_purity_should_fail_when_the_manifest_reads_os_environ():
    text = (
        "import os\n"
        "from ratch.checks.forbidden_literal import NoForbiddenLiteral\n"
        "CHECKS = [NoForbiddenLiteral()]\n"
        "os.environ.get('STRICT')\n"
    )

    ws = FakeWorkspace(files={"ratch_checks.py": text})

    result = ManifestPurity().check(ws)
    assert result.state is State.FAIL
    assert any(
        f.identity == ("manifest-purity", "ratch_checks.py", "os.environ")
        for f in result.findings
    )


def manifest_purity_should_fail_when_the_manifest_calls_open():
    text = (
        "from ratch.checks.forbidden_literal import NoForbiddenLiteral\n"
        "open('/tmp/x')\n"
        "CHECKS = [NoForbiddenLiteral()]\n"
    )

    ws = FakeWorkspace(files={"ratch_checks.py": text})

    result = ManifestPurity().check(ws)
    assert result.state is State.FAIL
    assert any(
        f.identity == ("manifest-purity", "ratch_checks.py", "open")
        for f in result.findings
    )


def manifest_purity_should_fail_when_the_manifest_calls_os_getenv():
    text = (
        "import os\n"
        "from ratch.checks.forbidden_literal import NoForbiddenLiteral\n"
        "os.getenv('STRICT')\n"
        "CHECKS = [NoForbiddenLiteral()]\n"
    )

    ws = FakeWorkspace(files={"ratch_checks.py": text})

    result = ManifestPurity().check(ws)
    assert result.state is State.FAIL
    assert any(
        f.identity == ("manifest-purity", "ratch_checks.py", "os.getenv")
        for f in result.findings
    )


def manifest_purity_should_pass_when_the_manifest_is_a_pure_checks_list():
    ws = FakeWorkspace(files={"ratch_checks.py": _CLEAN})

    result = ManifestPurity().check(ws)

    assert result.state is State.PASS
    assert result.findings == []
    assert result.examined_n == 1


def manifest_purity_should_fail_when_two_loads_disagree_on_repr():
    text = (
        "import uuid\n"
        "CHECKS = [str(uuid.uuid4())]\n"
    )

    ws = FakeWorkspace(files={"ratch_checks.py": text})

    result = ManifestPurity().check(ws)

    assert result.state is State.FAIL
    assert result.examined_n == 1
    assert any(
        f.identity == ("manifest-purity", "ratch_checks.py", "repr(CHECKS)")
        for f in result.findings
    )


def manifest_purity_should_bite_its_plants_when_checked_against_its_own_fixture(tmp_path):
    check = ManifestPurity()

    assert_bites(check, tmp_path)

    assert check.id


def manifest_purity_should_be_discoverable_when_registered_as_an_entry_point():
    from ratch.registry import discover

    found = discover().get('manifest-purity')

    expected = ManifestPurity

    assert found is expected
