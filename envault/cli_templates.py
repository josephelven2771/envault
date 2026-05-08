"""CLI subcommands for managing env templates."""

from __future__ import annotations

import argparse
import sys

from envault.templates import Template, TemplateStore


def _get_store(args: argparse.Namespace) -> TemplateStore:
    return TemplateStore(store_dir=args.store_dir)


def cmd_template_save(args: argparse.Namespace) -> None:
    store = _get_store(args)
    keys = [k.strip() for k in args.keys.split(",") if k.strip()]
    if not keys:
        print("Error: at least one key must be provided.", file=sys.stderr)
        sys.exit(1)
    tmpl = Template(name=args.name, keys=keys, description=args.description or "")
    store.set(tmpl)
    print(f"Template '{args.name}' saved with {len(keys)} key(s).")


def cmd_template_show(args: argparse.Namespace) -> None:
    store = _get_store(args)
    tmpl = store.get(args.name)
    if tmpl is None:
        print(f"Template '{args.name}' not found.", file=sys.stderr)
        sys.exit(1)
    print(f"Name       : {tmpl.name}")
    print(f"Description: {tmpl.description}")
    print(f"Keys       : {', '.join(tmpl.keys)}")


def cmd_template_list(args: argparse.Namespace) -> None:
    store = _get_store(args)
    templates = store.list()
    if not templates:
        print("No templates defined.")
        return
    for tmpl in templates:
        desc = f" — {tmpl.description}" if tmpl.description else ""
        print(f"  {tmpl.name}{desc} ({len(tmpl.keys)} keys)")


def cmd_template_delete(args: argparse.Namespace) -> None:
    store = _get_store(args)
    removed = store.delete(args.name)
    if removed:
        print(f"Template '{args.name}' deleted.")
    else:
        print(f"Template '{args.name}' not found.", file=sys.stderr)
        sys.exit(1)


def add_templates_subcommand(subparsers: argparse._SubParsersAction) -> None:
    p = subparsers.add_parser("template", help="Manage env key templates")
    p.add_argument("--store-dir", default=".envault", help="Path to the store directory")
    sub = p.add_subparsers(dest="template_cmd", required=True)

    ps = sub.add_parser("save", help="Save a named template")
    ps.add_argument("name", help="Template name")
    ps.add_argument("--keys", required=True, help="Comma-separated list of env keys")
    ps.add_argument("--description", default="", help="Optional description")
    ps.set_defaults(func=cmd_template_save)

    psh = sub.add_parser("show", help="Show a template")
    psh.add_argument("name", help="Template name")
    psh.set_defaults(func=cmd_template_show)

    pl = sub.add_parser("list", help="List all templates")
    pl.set_defaults(func=cmd_template_list)

    pd = sub.add_parser("delete", help="Delete a template")
    pd.add_argument("name", help="Template name")
    pd.set_defaults(func=cmd_template_delete)
