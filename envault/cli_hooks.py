"""CLI subcommands for managing envault hooks."""

import argparse
import sys
from pathlib import Path

from envault.hooks import (
    HOOK_NAMES,
    install_hook,
    remove_hook,
    list_hooks,
    hook_path,
)


def cmd_hook_install(args: argparse.Namespace) -> None:
    script_path = Path(args.script)
    if not script_path.exists():
        print(f"Error: script file not found: {args.script}", file=sys.stderr)
        sys.exit(1)
    script = script_path.read_text()
    path = install_hook(args.store_dir, args.hook_name, script)
    print(f"Installed hook '{args.hook_name}' -> {path}")


def cmd_hook_remove(args: argparse.Namespace) -> None:
    removed = remove_hook(args.store_dir, args.hook_name)
    if removed:
        print(f"Removed hook '{args.hook_name}'.")
    else:
        print(f"Hook '{args.hook_name}' was not installed.")


def cmd_hook_list(args: argparse.Namespace) -> None:
    hooks = list_hooks(args.store_dir)
    if not hooks:
        print("No hooks installed.")
    else:
        print("Installed hooks:")
        for name in hooks:
            path = hook_path(args.store_dir, name)
            print(f"  {name}  ({path})")


def cmd_hook_show(args: argparse.Namespace) -> None:
    path = hook_path(args.store_dir, args.hook_name)
    if not path.exists():
        print(f"Hook '{args.hook_name}' is not installed.", file=sys.stderr)
        sys.exit(1)
    print(path.read_text())


def add_hooks_subcommand(subparsers: argparse._SubParsersAction) -> None:
    hooks_parser = subparsers.add_parser("hook", help="Manage push/pull hooks")
    hooks_parser.add_argument(
        "--store-dir", default=".envault", help="Path to the envault store directory"
    )
    hook_sub = hooks_parser.add_subparsers(dest="hook_cmd", required=True)

    install_p = hook_sub.add_parser("install", help="Install a hook script")
    install_p.add_argument(
        "hook_name", choices=sorted(HOOK_NAMES), help="Hook to install"
    )
    install_p.add_argument("script", help="Path to the script file to install")
    install_p.set_defaults(func=cmd_hook_install)

    remove_p = hook_sub.add_parser("remove", help="Remove an installed hook")
    remove_p.add_argument(
        "hook_name", choices=sorted(HOOK_NAMES), help="Hook to remove"
    )
    remove_p.set_defaults(func=cmd_hook_remove)

    list_p = hook_sub.add_parser("list", help="List installed hooks")
    list_p.set_defaults(func=cmd_hook_list)

    show_p = hook_sub.add_parser("show", help="Print the contents of a hook script")
    show_p.add_argument(
        "hook_name", choices=sorted(HOOK_NAMES), help="Hook to show"
    )
    show_p.set_defaults(func=cmd_hook_show)
