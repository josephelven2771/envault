"""CLI subcommands for alias management."""
from __future__ import annotations

import argparse
import sys

from envault.env_alias import AliasRecord, AliasStore


def _get_store(args: argparse.Namespace) -> AliasStore:
    return AliasStore(args.store_dir)


def cmd_alias_set(args: argparse.Namespace) -> None:
    store = _get_store(args)
    record = AliasRecord(alias=args.alias, project=args.project, note=args.note or "")
    store.set(record)
    print(f"Alias '{args.alias}' -> '{args.project}' saved.")


def cmd_alias_get(args: argparse.Namespace) -> None:
    store = _get_store(args)
    record = store.get(args.alias)
    if record is None:
        print(f"No alias '{args.alias}' found.", file=sys.stderr)
        sys.exit(1)
    print(f"{record.alias} -> {record.project}" + (f"  # {record.note}" if record.note else ""))


def cmd_alias_resolve(args: argparse.Namespace) -> None:
    store = _get_store(args)
    print(store.resolve(args.alias_or_project))


def cmd_alias_delete(args: argparse.Namespace) -> None:
    store = _get_store(args)
    if store.delete(args.alias):
        print(f"Alias '{args.alias}' removed.")
    else:
        print(f"Alias '{args.alias}' not found.", file=sys.stderr)
        sys.exit(1)


def cmd_alias_list(args: argparse.Namespace) -> None:
    store = _get_store(args)
    records = store.list_all()
    if not records:
        print("No aliases defined.")
        return
    for r in sorted(records, key=lambda x: x.alias):
        note_part = f"  # {r.note}" if r.note else ""
        print(f"{r.alias:<20} -> {r.project}{note_part}")


def add_alias_subcommand(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = subparsers.add_parser("alias", help="Manage project aliases")
    sp = p.add_subparsers(dest="alias_cmd", required=True)

    s = sp.add_parser("set", help="Create or update an alias")
    s.add_argument("alias")
    s.add_argument("project")
    s.add_argument("--note", default="")
    s.set_defaults(func=cmd_alias_set)

    g = sp.add_parser("get", help="Show a single alias")
    g.add_argument("alias")
    g.set_defaults(func=cmd_alias_get)

    rv = sp.add_parser("resolve", help="Resolve alias or return input unchanged")
    rv.add_argument("alias_or_project")
    rv.set_defaults(func=cmd_alias_resolve)

    d = sp.add_parser("delete", help="Remove an alias")
    d.add_argument("alias")
    d.set_defaults(func=cmd_alias_delete)

    ls = sp.add_parser("list", help="List all aliases")
    ls.set_defaults(func=cmd_alias_list)
