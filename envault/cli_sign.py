"""CLI subcommands for signing and verifying .env store entries."""

import argparse
import sys

from envault.env_sign import SignatureStore, sign_entry, verify_entry
from envault.store import LocalStore
from envault.whoami import get_current_user


def _get_stores(store_dir: str):
    store = LocalStore(store_dir)
    sig_store = SignatureStore(store_dir)
    return store, sig_store


def cmd_sign(args: argparse.Namespace) -> None:
    """Sign the latest (or specified) version of a project entry."""
    store, sig_store = _get_stores(args.store_dir)
    entry = store.load(args.project)
    if entry is None:
        print(f"[error] No entry found for project '{args.project}'.")
        sys.exit(1)

    version = args.version if args.version is not None else entry.version
    # Reload a specific version if needed
    if args.version is not None and args.version != entry.version:
        print(f"[error] Version {args.version} not found (latest is {entry.version}).")
        sys.exit(1)

    signer = get_current_user(override=getattr(args, "user", None))
    record = sign_entry(
        ciphertext=entry.ciphertext,
        project=args.project,
        version=version,
        signer=signer,
        secret=args.secret,
        note=getattr(args, "note", "") or "",
    )
    sig_store.add(record)
    print(f"Signed project='{args.project}' version={version} as '{signer}'.")
    print(f"Signature: {record.signature[:16]}...")


def cmd_verify(args: argparse.Namespace) -> None:
    """Verify the signature of a stored entry."""
    store, sig_store = _get_stores(args.store_dir)
    entry = store.load(args.project)
    if entry is None:
        print(f"[error] No entry found for project '{args.project}'.")
        sys.exit(1)

    version = args.version if args.version is not None else entry.version
    record = sig_store.get(args.project, version)
    if record is None:
        print(f"[error] No signature found for project='{args.project}' version={version}.")
        sys.exit(1)

    ok = verify_entry(entry.ciphertext, record, args.secret)
    if ok:
        print(f"[ok] Signature valid. Signed by '{record.signer}' at {record.signed_at}.")
    else:
        print("[FAIL] Signature mismatch — entry may have been tampered with.")
        sys.exit(2)


def cmd_list_signatures(args: argparse.Namespace) -> None:
    """List all signatures for a project."""
    _, sig_store = _get_stores(args.store_dir)
    records = sig_store.list_project(args.project)
    if not records:
        print(f"No signatures found for project '{args.project}'.")
        return
    for r in records:
        note = f" ({r.note})" if r.note else ""
        print(f"  v{r.version}  {r.signer}  {r.signed_at}{note}  sig={r.signature[:12]}...")


def add_sign_subcommand(subparsers) -> None:
    p_sign = subparsers.add_parser("sign", help="Sign a stored env entry")
    p_sign.add_argument("project")
    p_sign.add_argument("--secret", required=True, help="HMAC signing secret")
    p_sign.add_argument("--version", type=int, default=None)
    p_sign.add_argument("--note", default="")
    p_sign.add_argument("--store-dir", default=".envault")
    p_sign.set_defaults(func=cmd_sign)

    p_verify = subparsers.add_parser("verify", help="Verify a stored env entry signature")
    p_verify.add_argument("project")
    p_verify.add_argument("--secret", required=True)
    p_verify.add_argument("--version", type=int, default=None)
    p_verify.add_argument("--store-dir", default=".envault")
    p_verify.set_defaults(func=cmd_verify)

    p_list = subparsers.add_parser("signatures", help="List signatures for a project")
    p_list.add_argument("project")
    p_list.add_argument("--store-dir", default=".envault")
    p_list.set_defaults(func=cmd_list_signatures)
