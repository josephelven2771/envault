"""CLI subcommand for exporting decrypted env variables in various formats."""

import argparse
import sys

from envault.store import LocalStore
from envault.crypto import decrypt
from envault.env_file import parse_env
from envault.export import export_env, SUPPORTED_FORMATS


def cmd_export(args: argparse.Namespace) -> None:
    """Handle the 'envault export' subcommand."""
    store = LocalStore(args.store_path)
    entry = store.load(args.project)

    if entry is None:
        print(
            f"Error: No data found for project '{args.project}'.",
            file=sys.stderr,
        )
        sys.exit(1)

    try:
        plaintext = decrypt(entry.ciphertext, args.password)
    except Exception:
        print(
            "Error: Decryption failed. Check your password.",
            file=sys.stderr,
        )
        sys.exit(1)

    env = parse_env(plaintext)

    try:
        output = export_env(env, args.format)
    except ValueError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)

    if args.output:
        with open(args.output, "w") as fh:
            fh.write(output + "\n")
        print(f"Exported {len(env)} variable(s) to '{args.output}' ({args.format}).")
    else:
        print(output)


def add_export_subcommand(subparsers: argparse._SubParsersAction) -> None:
    """Register the 'export' subcommand on the given subparsers object."""
    parser = subparsers.add_parser(
        "export",
        help="Export decrypted env vars in shell, JSON, or Docker format.",
    )
    parser.add_argument("project", help="Project name to export.")
    parser.add_argument(
        "--format",
        choices=SUPPORTED_FORMATS,
        default="shell",
        help="Output format (default: shell).",
    )
    parser.add_argument(
        "--output",
        metavar="FILE",
        default=None,
        help="Write output to FILE instead of stdout.",
    )
    parser.add_argument("--password", required=True, help="Decryption password.")
    parser.add_argument(
        "--store-path",
        default=".envault",
        help="Path to the local store directory (default: .envault).",
    )
    parser.set_defaults(func=cmd_export)
