"""Signing and verification of .env snapshots using HMAC-SHA256."""

import hashlib
import hmac
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional


@dataclass
class SignatureRecord:
    project: str
    version: int
    signer: str
    signature: str
    signed_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    note: str = ""

    def to_dict(self) -> dict:
        return {
            "project": self.project,
            "version": self.version,
            "signer": self.signer,
            "signature": self.signature,
            "signed_at": self.signed_at,
            "note": self.note,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "SignatureRecord":
        return cls(
            project=data["project"],
            version=data["version"],
            signer=data["signer"],
            signature=data["signature"],
            signed_at=data["signed_at"],
            note=data.get("note", ""),
        )


def _compute_signature(ciphertext: bytes, secret: str) -> str:
    """Compute HMAC-SHA256 over ciphertext using secret as the key."""
    mac = hmac.new(secret.encode(), ciphertext, hashlib.sha256)
    return mac.hexdigest()


def sign_entry(ciphertext: bytes, project: str, version: int, signer: str,
               secret: str, note: str = "") -> SignatureRecord:
    """Create a SignatureRecord for the given ciphertext."""
    sig = _compute_signature(ciphertext, secret)
    return SignatureRecord(
        project=project,
        version=version,
        signer=signer,
        signature=sig,
        note=note,
    )


def verify_entry(ciphertext: bytes, record: SignatureRecord, secret: str) -> bool:
    """Return True if the signature in record matches the ciphertext."""
    expected = _compute_signature(ciphertext, secret)
    return hmac.compare_digest(expected, record.signature)


class SignatureStore:
    """Persist and retrieve SignatureRecords alongside the store."""

    def __init__(self, store_dir: str):
        import os
        self._path = os.path.join(store_dir, "signatures.json")
        self._records: list[dict] = self._load()

    def _load(self) -> list:
        import os
        if not os.path.exists(self._path):
            return []
        with open(self._path, "r", encoding="utf-8") as fh:
            return json.load(fh)

    def _save(self) -> None:
        with open(self._path, "w", encoding="utf-8") as fh:
            json.dump(self._records, fh, indent=2)

    def add(self, record: SignatureRecord) -> None:
        self._records.append(record.to_dict())
        self._save()

    def get(self, project: str, version: int) -> Optional[SignatureRecord]:
        for r in reversed(self._records):
            if r["project"] == project and r["version"] == version:
                return SignatureRecord.from_dict(r)
        return None

    def list_project(self, project: str) -> list[SignatureRecord]:
        return [
            SignatureRecord.from_dict(r)
            for r in self._records
            if r["project"] == project
        ]
