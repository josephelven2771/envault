"""CLI sub-command: envault watch — auto-push on local .env changes."""

import argparse
import sys
from pathlib import Path

from envault.store import LocalStore
from envault.env_watch import watch


def cmd_watch(args: argparse.Namespace) -> None:
    """Entry point for `envault watch`."""
    env_path = Path(args.env_file)
    if not env_path.exists():
        print(f"[envault] error: file not found: {env_path}", file=sys.stderr)
        sys.exit(1)

    store = LocalStore(args.store_dir)

    print(
        f"[envault] watching {env_path} for project '{args.project}' "
        f"(interval={args.interval}s) — press Ctrl+C to stop."
    )

    def _on_push(project: str, version: int) -> None:
        print(f"[envault] change detected → pushed version {version} for '{project}'")

    def _on_error(exc: Exception) -> None:
        print(f"[envault] error during push: {exc}", file=sys.stderr)

    try:
        watch(
            env_path=env_path,
            store=store,
            project=args.project,
            password=args.password,
            poll_interval=args.interval,
            on_push=_on_push,
            on_error=_on_error,
        )
    except KeyboardInterrupt:
        print("\n[envault] watch stopped.")


def add_watch_subcommand(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    """Register the `watch` sub-command on *subparsers*."""
    p = subparsers.add_parser(
        "watch",
        help="Watch a .env file and auto-push changes to the store.",
    )
    p.add_argument("project", help="Project name in the store.")
    p.add_argument("--env-file", default=".env", help="Path to the .env file (default: .env).")
    p.add_argument("--store-dir", default=".envault_store", help="Path to the local store directory.")
    p.add_argument("--password", required=True, help="Encryption password.")
    p.add_argument(
        "--interval",
        type=float,
        default=2.0,
        help="Poll interval in seconds (default: 2.0).",
    )
    p.set_defaults(func=cmd_watch)
