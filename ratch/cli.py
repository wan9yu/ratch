"""Command-line adapter for 'ratch check [--staged]'.

The adapter wires a Workspace and the repo's manifest into a Runner and
renders the resulting report. Nicing the process is the Runner's own
concern; the adapter only decides whether niceing is requested.
"""
import argparse
import pathlib

from ratch.registry import load_manifest
from ratch.reporter import render_text
from ratch.runner import Runner
from ratch.workspace import Workspace

__all__ = ["main"]


def main(argv=None):
    parser = argparse.ArgumentParser(prog="ratch")
    sub = parser.add_subparsers(dest="command", required=True)
    check = sub.add_parser("check")
    check.add_argument("--staged", action="store_true")
    args = parser.parse_args(argv)

    cwd = pathlib.Path.cwd()
    view = "index" if args.staged else "worktree"
    ws = Workspace(cwd, view)
    checks = load_manifest(cwd)

    report = Runner(use_nice=True).run(checks, ws)
    print(render_text(report))
    return report.exit_code
