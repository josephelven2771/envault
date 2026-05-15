"""CLI commands for managing environment variable groups."""

from __future__ import annotations

import argparse
from typing import List

from envault.env_groups import GroupRecord, GroupStore


def _get_store(store_dir: str) -> GroupStore:
    return GroupStore(store_dir)


def cmd_group_set(args: argparse.Namespace) -> None:
    store = _get_store(args.store_dir)
    keys: List[str] = [k.strip() for k in args.keys.split(",") if k.strip()]
    record = GroupRecord(
        name=args.name,
        keys=keys,
        description=args.description or "",
    )
    store.set(record)
    print(f"Group '{args.name}' saved with {len(keys)} key(s).")


def cmd_group_get(args: argparse.Namespace) -> None:
    store = _get_store(args.store_dir)
    record = store.get(args.name)
    if record is None:
        print(f"Group '{args.name}' not found.")
        return
    print(f"Group: {record.name}")
    if record.description:
        print(f"Description: {record.description}")
    print("Keys:")
    for k in record.keys:
        print(f"  - {k}")


def cmd_group_delete(args: argparse.Namespace) -> None:
    store = _get_store(args.store_dir)
    removed = store.delete(args.name)
    if removed:
        print(f"Group '{args.name}' deleted.")
    else:
        print(f"Group '{args.name}' not found.")


def cmd_group_list(args: argparse.Namespace) -> None:
    store = _get_store(args.store_dir)
    groups = store.list_groups()
    if not groups:
        print("No groups defined.")
        return
    for g in sorted(groups, key=lambda r: r.name):
        key_count = len(g.keys)
        desc = f" — {g.description}" if g.description else ""
        print(f"  {g.name} ({key_count} key(s)){desc}")


def cmd_group_lookup(args: argparse.Namespace) -> None:
    store = _get_store(args.store_dir)
    groups = store.groups_for_key(args.key)
    if not groups:
        print(f"Key '{args.key}' is not in any group.")
    else:
        print(f"Key '{args.key}' belongs to: {', '.join(sorted(groups))}")


def add_groups_subcommand(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = subparsers.add_parser("group", help="Manage variable groups")
    sp = p.add_subparsers(dest="group_cmd", required=True)

    s = sp.add_parser("set", help="Create or update a group")
    s.add_argument("name")
    s.add_argument("--keys", required=True, help="Comma-separated key names")
    s.add_argument("--description", default="")
    s.set_defaults(func=cmd_group_set)

    g = sp.add_parser("get", help="Show a group")
    g.add_argument("name")
    g.set_defaults(func=cmd_group_get)

    d = sp.add_parser("delete", help="Delete a group")
    d.add_argument("name")
    d.set_defaults(func=cmd_group_delete)

    ls = sp.add_parser("list", help="List all groups")
    ls.set_defaults(func=cmd_group_list)

    lk = sp.add_parser("lookup", help="Find groups containing a key")
    lk.add_argument("key")
    lk.set_defaults(func=cmd_group_lookup)
