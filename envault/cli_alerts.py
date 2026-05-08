"""CLI subcommands for envault alert rules."""
from __future__ import annotations

import argparse
import sys

from envault.alerts import AlertRule, check_alerts, format_alerts, ALERT_RULES
from envault.diff import diff_envs
from envault.store import LocalStore
from envault.crypto import decrypt


def cmd_check_alerts(args: argparse.Namespace) -> None:
    store = LocalStore(args.store_dir)
    project = args.project

    entries = []
    for v in [args.version_a, args.version_b]:
        entry = store.load(project, v)
        if entry is None:
            print(f"Error: version {v} not found for project '{project}'.", file=sys.stderr)
            sys.exit(1)
        entries.append(entry)

    env_a = {}
    env_b = {}
    try:
        from envault.env_file import parse_env
        env_a = parse_env(decrypt(entries[0].ciphertext, args.password))
        env_b = parse_env(decrypt(entries[1].ciphertext, args.password))
    except Exception as exc:
        print(f"Error decrypting: {exc}", file=sys.stderr)
        sys.exit(1)

    diff_results = diff_envs(env_a, env_b)
    matches = check_alerts(diff_results)
    print(format_alerts(matches))
    if matches:
        sys.exit(2)


def cmd_list_rules(args: argparse.Namespace) -> None:
    print("Default alert keywords:")
    for kw in ALERT_RULES:
        print(f"  - {kw}")


def add_alerts_subcommand(subparsers: argparse._SubParsersAction) -> None:
    alerts_parser = subparsers.add_parser("alerts", help="Manage and run alert checks")
    alerts_sub = alerts_parser.add_subparsers(dest="alerts_cmd")

    check_parser = alerts_sub.add_parser(
        "check", help="Check for sensitive-key changes between two versions"
    )
    check_parser.add_argument("project")
    check_parser.add_argument("version_a", type=int)
    check_parser.add_argument("version_b", type=int)
    check_parser.add_argument("--password", required=True)
    check_parser.add_argument("--store-dir", default=".envault")
    check_parser.set_defaults(func=cmd_check_alerts)

    list_parser = alerts_sub.add_parser("rules", help="List default alert rules")
    list_parser.set_defaults(func=cmd_list_rules)
