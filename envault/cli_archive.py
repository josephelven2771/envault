"""CLI subcommands for archiving and restoring projects."""
from __future__ import annotations

import argparse
import sys

from envault.env_archive import ArchiveStore
from envault.whoami import get_current_user


def _get_store(args: argparse.Namespace) -> ArchiveStore:
    return ArchiveStore(store_dir=args.store_dir)


def cmd_archive(args: argparse.Namespace) -> None:
    store = _get_store(args)
    if store.is_archived(args.project):
        print(f"Project '{args.project}' is already archived.")
        sys.exit(1)
    user = get_current_user()
    record = store.archive(args.project, archived_by=user, note=args.note or "")
    print(f"Archived '{record.project}' at {record.archived_at} by {record.archived_by}.")


def cmd_restore(args: argparse.Namespace) -> None:
    store = _get_store(args)
    if not store.is_archived(args.project):
        print(f"Project '{args.project}' is not archived.")
        sys.exit(1)
    store.restore(args.project)
    print(f"Restored project '{args.project}'.")


def cmd_list_archived(args: argparse.Namespace) -> None:
    store = _get_store(args)
    records = store.list_archived()
    if not records:
        print("No archived projects.")
        return
    for r in records:
        note_part = f"  # {r.note}" if r.note else ""
        print(f"  {r.project:<30} archived={r.archived_at}  by={r.archived_by}{note_part}")


def add_archive_subcommand(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p_archive = subparsers.add_parser("archive", help="Archive a project (soft-delete)")
    p_archive.add_argument("project")
    p_archive.add_argument("--store-dir", default=".envault", dest="store_dir")
    p_archive.add_argument("--note", default="", help="Optional reason for archiving")
    p_archive.set_defaults(func=cmd_archive)

    p_restore = subparsers.add_parser("restore", help="Restore an archived project")
    p_restore.add_argument("project")
    p_restore.add_argument("--store-dir", default=".envault", dest="store_dir")
    p_restore.set_defaults(func=cmd_restore)

    p_list = subparsers.add_parser("list-archived", help="List all archived projects")
    p_list.add_argument("--store-dir", default=".envault", dest="store_dir")
    p_list.set_defaults(func=cmd_list_archived)
