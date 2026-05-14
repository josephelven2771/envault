"""CLI commands for quota inspection."""
from __future__ import annotations

import argparse

from envault.store import LocalStore
from envault.env_quota import QuotaConfig, check_quota


def cmd_quota_status(args: argparse.Namespace) -> None:
    store = LocalStore(args.store_dir)
    config = QuotaConfig(
        max_versions_per_project=args.max_versions,
        max_projects=args.max_projects,
    )
    status = check_quota(store, args.project, config)
    print(status.summary())


def cmd_quota_list(args: argparse.Namespace) -> None:
    store = LocalStore(args.store_dir)
    config = QuotaConfig(
        max_versions_per_project=args.max_versions,
        max_projects=args.max_projects,
    )
    projects = store.list_projects()
    if not projects:
        print("No projects found.")
        return
    print(f"{'Project':<30} {'Versions':>8} {'Limit':>8} {'Status':>10}")
    print("-" * 62)
    for proj in sorted(projects):
        status = check_quota(store, proj, config)
        flag = "OVER" if status.versions_exceeded else "ok"
        print(f"{proj:<30} {status.version_count:>8} {status.max_versions:>8} {flag:>10}")
    print(f"\nProjects: {len(projects)}/{config.max_projects}")


def add_quota_subcommand(subparsers: argparse._SubParsersAction) -> None:
    quota_parser = subparsers.add_parser("quota", help="Inspect storage quotas")
    quota_parser.add_argument("--store-dir", default=".envault", help="Path to store directory")
    quota_parser.add_argument("--max-versions", type=int, default=50, help="Max versions per project")
    quota_parser.add_argument("--max-projects", type=int, default=20, help="Max total projects")

    quota_sub = quota_parser.add_subparsers(dest="quota_cmd")

    status_p = quota_sub.add_parser("status", help="Show quota status for a project")
    status_p.add_argument("project", help="Project name")
    status_p.set_defaults(func=cmd_quota_status)

    list_p = quota_sub.add_parser("list", help="List quota usage for all projects")
    list_p.set_defaults(func=cmd_quota_list)
