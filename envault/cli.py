"""Command-line interface for envault.

Usage:
    envault push <project> <environment> [--env-file PATH] [--user EMAIL]
    envault pull <project> <environment> [--env-file PATH]
    envault list
"""

import argparse
import getpass
import sys
from pathlib import Path

from envault.store import LocalStore
from envault.sync import push, pull


def cmd_push(args):
    password = getpass.getpass("Encryption password: ")
    store = LocalStore()
    env_path = Path(args.env_file)
    if not env_path.exists():
        print(f"Error: env file not found: {env_path}", file=sys.stderr)
        sys.exit(1)
    entry = push(
        project=args.project,
        environment=args.environment,
        env_path=env_path,
        password=password,
        updated_by=args.user,
        store=store,
    )
    print(f"Pushed {args.project}/{args.environment} (version {entry.version}) at {entry.updated_at}")


def cmd_pull(args):
    password = getpass.getpass("Decryption password: ")
    store = LocalStore()
    env_path = Path(args.env_file)
    try:
        env_vars = pull(
            project=args.project,
            environment=args.environment,
            env_path=env_path,
            password=password,
            store=store,
        )
    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except ValueError as e:
        print(f"Error: decryption failed — wrong password? ({e})", file=sys.stderr)
        sys.exit(1)
    print(f"Pulled {len(env_vars)} variable(s) to {env_path}")


def cmd_list(args):
    store = LocalStore()
    entries = store.list_entries()
    if not entries:
        print("No stored environments found.")
        return
    print(f"{'PROJECT':<25} {'ENVIRONMENT'}")
    print("-" * 45)
    for e in entries:
        print(f"{e['project']:<25} {e['environment']}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="envault",
        description="Manage and sync encrypted .env files.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    push_p = sub.add_parser("push", help="Encrypt and push a .env file to the store.")
    push_p.add_argument("project", help="Project name")
    push_p.add_argument("environment", help="Environment name (e.g. production)")
    push_p.add_argument("--env-file", default=".env", help="Path to .env file (default: .env)")
    push_p.add_argument("--user", default="unknown", help="Your identifier (e.g. email)")
    push_p.set_defaults(func=cmd_push)

    pull_p = sub.add_parser("pull", help="Pull and decrypt a .env file from the store.")
    pull_p.add_argument("project", help="Project name")
    pull_p.add_argument("environment", help="Environment name")
    pull_p.add_argument("--env-file", default=".env", help="Destination .env file (default: .env)")
    pull_p.set_defaults(func=cmd_pull)

    list_p = sub.add_parser("list", help="List all stored environments.")
    list_p.set_defaults(func=cmd_list)

    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
