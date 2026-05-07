"""CLI subcommands for access control management."""

from __future__ import annotations

import argparse
from pathlib import Path

from envault.access import AccessControl, ALL_PERMISSIONS


def _get_access(project: str, store_dir: str) -> AccessControl:
    path = Path(store_dir) / project / "access.json"
    return AccessControl(path)


def cmd_grant(args: argparse.Namespace) -> None:
    ac = _get_access(args.project, args.store)
    if args.permission not in ALL_PERMISSIONS:
        print(f"Error: permission must be one of {sorted(ALL_PERMISSIONS)}")
        return
    ac.grant(args.user, args.permission)
    print(f"Granted '{args.permission}' to {args.user} on project '{args.project}'.")


def cmd_revoke(args: argparse.Namespace) -> None:
    ac = _get_access(args.project, args.store)
    removed = ac.revoke(args.user)
    if removed:
        print(f"Revoked access for {args.user} on project '{args.project}'.")
    else:
        print(f"User {args.user} had no access entry for project '{args.project}'.")


def cmd_list_access(args: argparse.Namespace) -> None:
    ac = _get_access(args.project, args.store)
    users = ac.list_users()
    if not users:
        print(f"No access entries for project '{args.project}'.")
        return
    print(f"Access list for project '{args.project}':")
    for entry in users:
        print(f"  {entry.user:<30} {entry.permission}")


def cmd_check(args: argparse.Namespace) -> None:
    ac = _get_access(args.project, args.store)
    allowed = ac.can(args.user, args.permission)
    status = "ALLOWED" if allowed else "DENIED"
    print(f"{args.user} -> {args.permission} on '{args.project}': {status}")


def add_access_subcommands(subparsers: argparse._SubParsersAction) -> None:
    p = subparsers.add_parser("access", help="Manage project access control")
    p.add_argument("--store", default=".envault", help="Store directory")
    sub = p.add_subparsers(dest="access_cmd", required=True)

    grant_p = sub.add_parser("grant", help="Grant permission to a user")
    grant_p.add_argument("project")
    grant_p.add_argument("user")
    grant_p.add_argument("permission", choices=sorted(ALL_PERMISSIONS))
    grant_p.set_defaults(func=cmd_grant)

    revoke_p = sub.add_parser("revoke", help="Revoke a user's access")
    revoke_p.add_argument("project")
    revoke_p.add_argument("user")
    revoke_p.set_defaults(func=cmd_revoke)

    list_p = sub.add_parser("list", help="List users with access")
    list_p.add_argument("project")
    list_p.set_defaults(func=cmd_list_access)

    check_p = sub.add_parser("check", help="Check if a user has a given permission")
    check_p.add_argument("project")
    check_p.add_argument("user")
    check_p.add_argument("permission", choices=sorted(ALL_PERMISSIONS))
    check_p.set_defaults(func=cmd_check)
