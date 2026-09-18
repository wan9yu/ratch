import os
import subprocess
import sys

import pytest

from ratch.checks.forbidden_literal import NoForbiddenLiteral
from ratch.pytest_plugin import iter_ratch_check_ids, resolve_plugin
from ratch.testing import make_tmp_repo


def resolve_plugin_should_return_the_class_when_spec_is_module_colon_name():
    cls = resolve_plugin("ratch.checks.forbidden_literal:NoForbiddenLiteral")
    assert cls is NoForbiddenLiteral


def resolve_plugin_should_raise_when_spec_has_no_colon():
    with pytest.raises(ValueError):
        resolve_plugin("ratch.checks.forbidden_literal")


def iter_ratch_check_ids_should_match_the_manifest_when_a_manifest_exists(tmp_path):
    (tmp_path / "ratch_checks.py").write_text(
        "from ratch.checks.forbidden_literal import NoForbiddenLiteral\n"
        "CHECKS = [NoForbiddenLiteral()]\n",
        encoding="utf-8",
    )
    assert iter_ratch_check_ids(tmp_path) == ["no-forbidden-literal"]


def pytest_ratch_should_collect_manifest_ids_when_flag_is_on(tmp_path):
    repo = make_tmp_repo(tmp_path / "repo", files={"ok.py": "x = 1\n"})
    (repo / "ratch_checks.py").write_text(
        "from ratch.checks.forbidden_literal import NoForbiddenLiteral\n"
        "CHECKS = [NoForbiddenLiteral()]\n",
        encoding="utf-8",
    )
    proc = subprocess.run(
        [sys.executable, "-m", "pytest", "--ratch", "--collect-only", "-q"],
        cwd=repo,
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0
    assert "ratch:no-forbidden-literal" in proc.stdout


def pytest_ratch_should_collect_nothing_extra_when_flag_is_off(tmp_path):
    repo = make_tmp_repo(tmp_path / "repo", files={"ok.py": "x = 1\n"})
    proc = subprocess.run(
        [sys.executable, "-m", "pytest", "--collect-only", "-q"],
        cwd=repo,
        capture_output=True,
        text=True,
    )
    assert "ratch:" not in proc.stdout


def pytest_ratch_plugin_should_collect_dotted_path_when_flag_is_set(tmp_path):
    repo = make_tmp_repo(tmp_path / "repo", files={"ok.py": "x = 1\n"})
    (repo / "ratch_checks.py").write_text(
        "from ratch.checks.forbidden_literal import NoForbiddenLiteral\n"
        "CHECKS = [NoForbiddenLiteral()]\n",
        encoding="utf-8",
    )
    plugin = tmp_path / "plug"
    plugin.mkdir()
    (plugin / "trivial_ratch_plugin.py").write_text(
        'from ratch.result import Result, State\n'
        "\n"
        "class TrivialCheck:\n"
        '    """Rule:\\n        always pass.\\n'
        "    Why:\\n        seam probe.\\n"
        "    Proven in:\\n        tests/test_pytest_seam.py\\n"
        "    Not this:\\n        not a real tooth.\\n"
        '    """\n'
        '    id = "trivial-check"\n'
        '    tier = "A"\n'
        '    kind = "gate"\n'
        '    scope = "global"\n'
        "    proven_in = ()\n"
        '    confidence = "net-new"\n'
        "    tolerates_unparseable = False\n"
        "    min_surface = 1\n"
        "    def check(self, ws):\n"
        "        return Result(self.id, State.PASS, examined_n=1)\n"
        "    def plants(self, ws):\n"
        "        return iter(())\n"
        "    def fixture(self, kit):\n"
        "        return ws\n",
        encoding="utf-8",
    )
    env = dict(os.environ)
    env["PYTHONPATH"] = str(plugin) + os.pathsep + env.get("PYTHONPATH", "")
    proc = subprocess.run(
        [
            sys.executable, "-m", "pytest", "--ratch",
            "--ratch-plugin=trivial_ratch_plugin:TrivialCheck",
            "--collect-only", "-q",
        ],
        cwd=repo,
        capture_output=True,
        text=True,
        env=env,
    )
    assert proc.returncode == 0
    assert "ratch:trivial-check" in proc.stdout
