"""CLI subcommands for variable interpolation."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from envault.crypto import decrypt
from envault.env_file import parse_env
from envault.env_variables import interpolate, list_references
from envault.store import LocalStore


def _load_env(store_dir: str, project: str, password: str) -> dict:
    store = LocalStore(store_dir)
    entry = store.load(project)
    if entry is None:
        print(f"No entry found for project '{project}'", file=sys.stderr)
        sys.exit(1)
    raw = decrypt(entry.ciphertext, password)
    return parse_env(raw)


def cmd_interpolate(args: argparse.Namespace) -> None:
    """Print the env after resolving all variable references."""
    env = _load_env(args.store_dir, args.project, args.password)
    result = interpolate(env)

    if not result.clean:
        for w in result.warnings:
            print(f"WARNING: {w}", file=sys.stderr)

    if args.format == "json":
        print(json.dumps(result.resolved, indent=2, sort_keys=True))
    else:
        for k, v in sorted(result.resolved.items()):
            print(f"{k}={v}")


def cmd_refs(args: argparse.Namespace) -> None:
    """List variable references found in the env."""
    env = _load_env(args.store_dir, args.project, args.password)
    refs = list_references(env)

    if not refs:
        print("No variable references found.")
        return

    for key, deps in sorted(refs.items()):
        print(f"  {key} -> {', '.join(deps)}")


def add_variables_subcommand(subparsers: argparse._SubParsersAction) -> None:
    p = subparsers.add_parser("interpolate", help="Resolve variable references in stored env")
    p.add_argument("project")
    p.add_argument("--password", required=True)
    p.add_argument("--store-dir", default=".envault")
    p.add_argument("--format", choices=["env", "json"], default="env")
    p.set_defaults(func=cmd_interpolate)

    r = subparsers.add_parser("refs", help="List variable references in stored env")
    r.add_argument("project")
    r.add_argument("--password", required=True)
    r.add_argument("--store-dir", default=".envault")
    r.set_defaults(func=cmd_refs)
