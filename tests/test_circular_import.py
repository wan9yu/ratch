"""BDD tests for the no-circular-import subprocess-effect check."""
import pathlib

from ratch.checks.circular_import import NoCircularImport
from ratch.result import State
from ratch.workspace import Workspace


def _pkg(root, name, modules):
    pkg = pathlib.Path(root) / name
    pkg.mkdir(parents=True, exist_ok=True)
    for mod_name, text in modules.items():
        (pkg / mod_name).write_text(text)
    return Workspace(root)


def circular_import_should_fail_when_package_imports_itself_cyclically(tmp_path):
    ws = _pkg(tmp_path, "cyc_pkg", {
        "__init__.py": "from cyc_pkg import a\n",
        "a.py": "from cyc_pkg.b import beta\n\nalpha = 1\n",
        "b.py": "from cyc_pkg.a import alpha\n\nbeta = 2\n",
    })
    result = NoCircularImport("cyc_pkg").check(ws)
    assert result.state is State.FAIL
    assert result.findings[0].path == "cyc_pkg"
    assert "circular import" in result.findings[0].anchor
