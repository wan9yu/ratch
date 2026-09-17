"""Black-box proof that the shipped 'ratch check' CLI gates its own literal.

Every fixture repo here is hand-built with raw subprocess calls to git and a
hand-planted file, never through ratch.testing.make_tmp_repo or a check's own
plants(), and every assertion drives the installed ``python -m ratch``
entry point as a subprocess. Nothing here shares code with ratch itself, so
a passing run is external proof that the packaged CLI works, not a proof
that only holds because the test reuses the machinery under test.
"""
import pathlib
import subprocess
import sys
import tempfile


def _hand_rolled_repo():
    """Build a fresh git repo outside this repo, with one clean commit."""
    root = pathlib.Path(tempfile.mkdtemp(prefix="ratch-blackbox-"))
    subprocess.run(["git", "init", "-q"], cwd=root, check=True)
    subprocess.run(
        ["git", "config", "user.name", "ratch-blackbox"], cwd=root, check=True
    )
    subprocess.run(
        ["git", "config", "user.email", "ratch-blackbox@example.test"],
        cwd=root, check=True,
    )
    (root / "seed.py").write_text("x = 1\n")
    subprocess.run(["git", "add", "seed.py"], cwd=root, check=True)
    subprocess.run(["git", "commit", "-q", "-m", "seed"], cwd=root, check=True)
    return root


def _run_staged_check(repo):
    return subprocess.run(
        [sys.executable, "-m", "ratch", "check", "--staged"],
        cwd=repo, capture_output=True, text=True,
    )


def ratch_check_should_exit_nonzero_with_a_fail_line_when_a_staged_file_carries_the_literal():
    banned = "cl" + "aude"
    repo = _hand_rolled_repo()
    (repo / "bad.py").write_text(banned + "\n")
    subprocess.run(["git", "add", "bad.py"], cwd=repo, check=True)

    proc = _run_staged_check(repo)

    assert proc.returncode == 1
    assert "no-forbidden-literal: FAIL" in proc.stdout


def ratch_check_should_exit_zero_when_the_staged_tree_is_clean():
    repo = _hand_rolled_repo()
    (repo / "ok.py").write_text("y = 2\n")
    subprocess.run(["git", "add", "ok.py"], cwd=repo, check=True)

    proc = _run_staged_check(repo)

    assert proc.returncode == 0


def the_repository_should_carry_no_forbidden_literal_when_every_tracked_file_is_scanned():
    banned = "cl" + "aude"
    root = pathlib.Path(__file__).resolve().parent.parent
    listing = subprocess.run(
        ["git", "ls-files"], cwd=root, capture_output=True, text=True, check=True
    )
    tracked = [line for line in listing.stdout.split("\n") if line]

    offenders = [
        rel for rel in tracked
        if banned in (root / rel).read_text(errors="replace")
    ]

    assert offenders == []


def the_ci_workflow_should_deep_checkout_and_run_both_gates_when_read_from_disk():
    root = pathlib.Path(__file__).resolve().parent.parent
    text = (root / ".github" / "workflows" / "ci.yml").read_text()

    assert "fetch-depth: 0" in text
    assert "pytest" in text
    assert "python -m ratch check" in text
