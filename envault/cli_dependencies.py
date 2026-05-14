"""CLI sub-command: envault deps — show key dependency graph."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from envault.crypto import decrypt
from envault.env_file import parse_env
from envault.store import LocalStore
from envault.env_dependencies import (
    build_dependency_graph,
    find_cycles,
    format_dependency_report,
)


def cmd_deps(args: argparse.Namespace) -> None:
    store = LocalStore(args.store_dir)
    entry = store.load(args.project)
    if entry is None:
        print(f"No data found for project '{args.project}'.", file=sys.stderr)
        sys.exit(1)

    try:
        plaintext = decrypt(entry.ciphertext, args.password)
    except Exception:
        print("Decryption failed — wrong password?", file=sys.stderr)
        sys.exit(1)

    env = parse_env(plaintext)
    graph = build_dependency_graph(env)

    if args.key:
        refs = graph.references(args.key)
        deps = graph.dependents(args.key)
        print(f"Key: {args.key}")
        print(f"  References : {', '.join(refs) if refs else '(none)'}")
        print(f"  Used by    : {', '.join(deps) if deps else '(none)'}")
        return

    print(format_dependency_report(graph))

    cycles = find_cycles(graph)
    if cycles:
        sys.exit(2)  # non-zero exit so CI pipelines can catch it


def add_deps_subcommand(subparsers: argparse._SubParsersAction) -> None:  # noqa: SLF001
    p = subparsers.add_parser(
        "deps",
        help="Show inter-key dependency graph for a project's .env",
    )
    p.add_argument("project", help="Project name")
    p.add_argument("--password", required=True, help="Decryption password")
    p.add_argument(
        "--store-dir",
        default=".envault",
        help="Path to local store directory (default: .envault)",
    )
    p.add_argument(
        "--key",
        default=None,
        help="Inspect a single key's references and dependents",
    )
    p.set_defaults(func=cmd_deps)
