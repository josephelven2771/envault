"""CLI subcommands for backup and restore of envault store data."""

from __future__ import annotations

import argparse
from pathlib import Path

from envault.env_backup import create_backup, restore_backup, read_backup_manifest
from envault.store import LocalStore


def cmd_backup(args: argparse.Namespace) -> None:
    store = LocalStore(args.store_dir)
    dest = Path(args.output)
    notes = args.notes or ""

    manifest = create_backup(store, dest, notes=notes)
    print(f"Backup created: {dest}")
    print(f"  Projects : {', '.join(manifest.projects) or '(none)'}")
    print(f"  Entries  : {manifest.entry_count}")
    print(f"  Timestamp: {manifest.created_at}")
    if notes:
        print(f"  Notes    : {notes}")


def cmd_restore(args: argparse.Namespace) -> None:
    store = LocalStore(args.store_dir)
    src = Path(args.input)

    if not src.exists():
        print(f"Error: backup file not found: {src}")
        raise SystemExit(1)

    manifest = restore_backup(store, src, overwrite=args.overwrite)
    print(f"Restore complete from: {src}")
    print(f"  Projects restored: {', '.join(manifest.projects) or '(none)'}")
    print(f"  Entries processed: {manifest.entry_count}")


def cmd_backup_info(args: argparse.Namespace) -> None:
    src = Path(args.input)
    manifest = read_backup_manifest(src)
    if manifest is None:
        print(f"Error: could not read manifest from {src}")
        raise SystemExit(1)
    print(f"Backup file : {src}")
    print(f"Created at  : {manifest.created_at}")
    print(f"Projects    : {', '.join(manifest.projects) or '(none)'}")
    print(f"Entry count : {manifest.entry_count}")
    if manifest.notes:
        print(f"Notes       : {manifest.notes}")


def add_backup_subcommand(subparsers: argparse._SubParsersAction) -> None:
    p_backup = subparsers.add_parser("backup", help="Back up all store entries to a zip file")
    p_backup.add_argument("--store-dir", required=True, help="Path to the local store directory")
    p_backup.add_argument("--output", required=True, help="Destination zip file path")
    p_backup.add_argument("--notes", default="", help="Optional notes to embed in the backup")
    p_backup.set_defaults(func=cmd_backup)

    p_restore = subparsers.add_parser("restore", help="Restore store entries from a zip backup")
    p_restore.add_argument("--store-dir", required=True, help="Path to the local store directory")
    p_restore.add_argument("--input", required=True, help="Source zip file path")
    p_restore.add_argument("--overwrite", action="store_true", help="Overwrite existing entries")
    p_restore.set_defaults(func=cmd_restore)

    p_info = subparsers.add_parser("backup-info", help="Show manifest info from a backup file")
    p_info.add_argument("--input", required=True, help="Backup zip file path")
    p_info.set_defaults(func=cmd_backup_info)
