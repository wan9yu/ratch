"""Command-line adapter: check, list, describe.

list and describe render the installed catalog from entry points.
Only check builds a Workspace and a Runner (and may request nicing).
"""
import argparse
import inspect
import pathlib
import sys

from ratch.registry import discover, load_manifest
from ratch.reporter import render_text
from ratch.runner import Runner
from ratch.workspace import Workspace

__all__ = ["main"]


def cmd_list(cwd):
    catalog = discover()
    enabled = {check.id for check in load_manifest(cwd)}
    for name in sorted(catalog):
        label = "enabled" if name in enabled else "catalog"
        print(f"{name:<24}{label}")
    return 0


def cmd_describe(check_id):
    cls = discover().get(check_id)
    if cls is None:
        print(check_id, file=sys.stderr)
        return 1
    print(inspect.getdoc(cls) or "")
    params = list(inspect.signature(cls.__init__).parameters.values())[1:]
    print(inspect.Signature(params))
    return 0


def main(argv=None):
    parser = argparse.ArgumentParser(prog="ratch")
    sub = parser.add_subparsers(dest="command", required=True)
    check = sub.add_parser("check")
    check.add_argument("--staged", action="store_true")
    sub.add_parser("list")
    describe = sub.add_parser("describe")
    describe.add_argument("id")
    args = parser.parse_args(argv)

    cwd = pathlib.Path.cwd()
    if args.command == "list":
        return cmd_list(cwd)
    if args.command == "describe":
        return cmd_describe(args.id)

    view = "index" if args.staged else "worktree"
    ws = Workspace(cwd, view)
    checks = load_manifest(cwd)
    report = Runner(use_nice=True).run(checks, ws)
    print(render_text(report))
    return report.exit_code
