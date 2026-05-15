"""CLI subcommands for managing per-key labels."""
from __future__ import annotations

import argparse
from pathlib import Path

from envault.env_labels import LabelStore


def _get_store(store_dir: str) -> LabelStore:
    return LabelStore(store_dir)


def cmd_label_set(args: argparse.Namespace) -> None:
    store = _get_store(args.store_dir)
    labels = [l.strip() for l in args.labels.split(",") if l.strip()]
    record = store.set_labels(
        project=args.project,
        key=args.key,
        labels=labels,
        note=args.note or "",
    )
    print(f"Labels set for '{args.key}' in project '{args.project}': {', '.join(record.labels)}")


def cmd_label_get(args: argparse.Namespace) -> None:
    store = _get_store(args.store_dir)
    record = store.get_labels(args.project, args.key)
    if record is None:
        print(f"No labels found for '{args.key}' in project '{args.project}'.")
    else:
        print(f"{args.key}: {', '.join(record.labels)}")
        if record.note:
            print(f"  note: {record.note}")


def cmd_label_delete(args: argparse.Namespace) -> None:
    store = _get_store(args.store_dir)
    removed = store.delete_labels(args.project, args.key)
    if removed:
        print(f"Labels removed for '{args.key}' in project '{args.project}'.")
    else:
        print(f"No labels found for '{args.key}' in project '{args.project}'.")


def cmd_label_list(args: argparse.Namespace) -> None:
    store = _get_store(args.store_dir)
    records = store.list_by_project(args.project)
    if not records:
        print(f"No labels defined for project '{args.project}'.")
        return
    for r in sorted(records, key=lambda x: x.key):
        print(f"  {r.key}: {', '.join(r.labels)}")


def cmd_label_find(args: argparse.Namespace) -> None:
    store = _get_store(args.store_dir)
    records = store.find_by_label(args.project, args.label)
    if not records:
        print(f"No keys with label '{args.label}' in project '{args.project}'.")
        return
    for r in sorted(records, key=lambda x: x.key):
        print(f"  {r.key}")


def add_labels_subcommand(subparsers: argparse.Action) -> None:
    p = subparsers.add_parser("label", help="Manage per-key labels")
    sp = p.add_subparsers(dest="label_cmd", required=True)

    for name, func, extra in [
        ("set", cmd_label_set, [("--labels", dict(required=True, help="Comma-separated labels")),
                                 ("--note", dict(default="", help="Optional note"))])  ,
        ("get", cmd_label_get, []),
        ("delete", cmd_label_delete, []),
        ("list", cmd_label_list, []),
    ]:
        sub = sp.add_parser(name)
        sub.add_argument("--store-dir", default=".envault", dest="store_dir")
        sub.add_argument("--project", required=True)
        if name not in ("list",):
            sub.add_argument("--key", required=True)
        for flag, kwargs in extra:
            sub.add_argument(flag, **kwargs)
        sub.set_defaults(func=func)

    find_p = sp.add_parser("find")
    find_p.add_argument("--store-dir", default=".envault", dest="store_dir")
    find_p.add_argument("--project", required=True)
    find_p.add_argument("--label", required=True)
    find_p.set_defaults(func=cmd_label_find)
