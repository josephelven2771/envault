"""CLI subcommands for pinning/unpinning project env versions."""

from __future__ import annotations

import argparse
import sys

from envault.env_pin import PinRecord, PinStore
from envault.whoami import get_current_user


def _get_store(args: argparse.Namespace) -> PinStore:
    return PinStore(args.store_dir)


def cmd_pin(args: argparse.Namespace) -> None:
    store = _get_store(args)
    user = get_current_user()
    record = PinRecord(
        project=args.project,
        version=args.version,
        pinned_by=user,
        note=args.note or "",
    )
    store.set_pin(record)
    print(f"Pinned '{args.project}' at version {args.version} (by {user}).")


def cmd_unpin(args: argparse.Namespace) -> None:
    store = _get_store(args)
    removed = store.remove_pin(args.project)
    if removed:
        print(f"Unpinned '{args.project}'.")
    else:
        print(f"No pin found for '{args.project}'.")
        sys.exit(1)


def cmd_pin_status(args: argparse.Namespace) -> None:
    store = _get_store(args)
    record = store.get_pin(args.project)
    if record is None:
        print(f"'{args.project}' is not pinned.")
    else:
        print(
            f"'{args.project}' is pinned at version {record.version} "
            f"by {record.pinned_by} on {record.pinned_at}"
            + (f" — {record.note}" if record.note else "")
        )


def cmd_pin_list(args: argparse.Namespace) -> None:
    store = _get_store(args)
    pins = store.list_pins()
    if not pins:
        print("No pins set.")
        return
    for p in pins:
        note_str = f" [{p.note}]" if p.note else ""
        print(f"{p.project}  v{p.version}  by {p.pinned_by}  at {p.pinned_at}{note_str}")


def add_pin_subcommand(subparsers: argparse._SubParsersAction) -> None:
    pin_parser = subparsers.add_parser("pin", help="Pin/unpin project env versions")
    pin_sub = pin_parser.add_subparsers(dest="pin_cmd", required=True)

    p_set = pin_sub.add_parser("set", help="Pin a project at a specific version")
    p_set.add_argument("project")
    p_set.add_argument("version", type=int)
    p_set.add_argument("--note", default="")
    p_set.add_argument("--store-dir", default=".envault")
    p_set.set_defaults(func=cmd_pin)

    p_rm = pin_sub.add_parser("remove", help="Remove a pin from a project")
    p_rm.add_argument("project")
    p_rm.add_argument("--store-dir", default=".envault")
    p_rm.set_defaults(func=cmd_unpin)

    p_st = pin_sub.add_parser("status", help="Show pin status for a project")
    p_st.add_argument("project")
    p_st.add_argument("--store-dir", default=".envault")
    p_st.set_defaults(func=cmd_pin_status)

    p_ls = pin_sub.add_parser("list", help="List all pinned projects")
    p_ls.add_argument("--store-dir", default=".envault")
    p_ls.set_defaults(func=cmd_pin_list)
