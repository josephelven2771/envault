"""CLI subcommand for merging env files from two projects."""

import argparse
import sys

from envault.crypto import decrypt
from envault.env_file import parse_env, write_env_file
from envault.env_merge import MergeConflict, merge_envs
from envault.store import LocalStore


def _decrypt_latest(store: LocalStore, project: str, password: str) -> dict:
    entry = store.load(project)
    if entry is None:
        print(f"[envault] Project '{project}' not found in store.", file=sys.stderr)
        sys.exit(1)
    raw = decrypt(entry.ciphertext, password)
    return parse_env(raw)


def cmd_merge(args: argparse.Namespace) -> None:
    store = LocalStore(args.store_dir)

    base_env = _decrypt_latest(store, args.base, args.password)
    ours_env = _decrypt_latest(store, args.ours, args.password)
    theirs_env = _decrypt_latest(store, args.theirs, args.password)

    try:
        merged, conflicts = merge_envs(
            base=base_env,
            ours=ours_env,
            theirs=theirs_env,
            strategy=args.strategy,
        )
    except MergeConflict as exc:
        print(f"[envault] Merge conflict on key '{exc.key}'.", file=sys.stderr)
        print(f"  ours   = {exc.ours!r}", file=sys.stderr)
        print(f"  theirs = {exc.theirs!r}", file=sys.stderr)
        print("Use --strategy ours|theirs|union to resolve automatically.", file=sys.stderr)
        sys.exit(2)

    if conflicts:
        print(f"[envault] Resolved {len(conflicts)} conflict(s) using strategy '{args.strategy}': {', '.join(conflicts)}")

    if args.output:
        write_env_file(args.output, merged)
        print(f"[envault] Merged env written to {args.output}")
    else:
        for k, v in merged.items():
            print(f"{k}={v}")


def add_merge_subcommand(subparsers: argparse._SubParsersAction) -> None:
    p = subparsers.add_parser(
        "merge",
        help="Three-way merge env vars from two projects relative to a base.",
    )
    p.add_argument("--base", required=True, help="Base project name (common ancestor).")
    p.add_argument("--ours", required=True, help="Our project name.")
    p.add_argument("--theirs", required=True, help="Their project name.")
    p.add_argument("--password", required=True, help="Decryption password.")
    p.add_argument(
        "--strategy",
        choices=["ours", "theirs", "union", "ask"],
        default="ours",
        help="Conflict resolution strategy (default: ours).",
    )
    p.add_argument("--output", default=None, help="Write merged env to this file.")
    p.add_argument("--store-dir", default=".envault_store", help="Path to local store.")
    p.set_defaults(func=cmd_merge)
