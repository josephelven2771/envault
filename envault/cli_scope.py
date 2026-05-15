"""CLI commands for env scope management."""
from __future__ import annotations

import argparse

from envault.env_scope import ScopeRecord, ScopeStore, VALID_SCOPES


def _get_store(args: argparse.Namespace) -> ScopeStore:
    return ScopeStore(args.store_dir)


def cmd_scope_set(args: argparse.Namespace) -> None:
    store = _get_store(args)
    record = ScopeRecord(
        project=args.project,
        scope=args.scope,
        version=args.version,
        note=args.note or "",
    )
    try:
        store.set_scope(record)
        print(f"Scope '{args.scope}' set to version {args.version} for project '{args.project}'.")
    except ValueError as exc:
        print(f"Error: {exc}")


def cmd_scope_get(args: argparse.Namespace) -> None:
    store = _get_store(args)
    record = store.get_scope(args.project, args.scope)
    if record is None:
        print(f"No scope '{args.scope}' found for project '{args.project}'.")
    else:
        print(f"project={record.project}  scope={record.scope}  version={record.version}  note={record.note!r}")


def cmd_scope_list(args: argparse.Namespace) -> None:
    store = _get_store(args)
    records = store.list_scopes(args.project)
    if not records:
        print(f"No scopes defined for project '{args.project}'.")
    else:
        for r in sorted(records, key=lambda x: x.scope):
            print(f"  {r.scope:<12} -> version {r.version}  {r.note}")


def cmd_scope_delete(args: argparse.Namespace) -> None:
    store = _get_store(args)
    removed = store.delete_scope(args.project, args.scope)
    if removed:
        print(f"Scope '{args.scope}' removed from project '{args.project}'.")
    else:
        print(f"Scope '{args.scope}' not found for project '{args.project}'.")


def add_scope_subcommand(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = subparsers.add_parser("scope", help="Manage environment scopes")
    p.add_argument("--store-dir", default=".envault", help="Path to store directory")
    sp = p.add_subparsers(dest="scope_cmd", required=True)

    ps = sp.add_parser("set", help="Assign a scope to a version")
    ps.add_argument("project")
    ps.add_argument("scope", choices=sorted(VALID_SCOPES))
    ps.add_argument("version", type=int)
    ps.add_argument("--note", default="")
    ps.set_defaults(func=cmd_scope_set)

    pg = sp.add_parser("get", help="Get version pinned to a scope")
    pg.add_argument("project")
    pg.add_argument("scope")
    pg.set_defaults(func=cmd_scope_get)

    pl = sp.add_parser("list", help="List all scopes for a project")
    pl.add_argument("project")
    pl.set_defaults(func=cmd_scope_list)

    pd = sp.add_parser("delete", help="Remove a scope assignment")
    pd.add_argument("project")
    pd.add_argument("scope")
    pd.set_defaults(func=cmd_scope_delete)
