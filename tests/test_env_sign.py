"""Tests for envault.env_sign signing and verification."""

import os
import pytest

from envault.env_sign import (
    SignatureRecord,
    SignatureStore,
    sign_entry,
    verify_entry,
)

SECRET = "super-hmac-secret"
CIPHER = b"fake-encrypted-payload-bytes"


@pytest.fixture
def sig_store(tmp_path):
    return SignatureStore(str(tmp_path))


def make_record(project="myapp", version=1, signer="alice@example.com"):
    return sign_entry(CIPHER, project, version, signer, SECRET, note="test")


# --- SignatureRecord ---

def test_record_roundtrip_dict():
    rec = make_record()
    restored = SignatureRecord.from_dict(rec.to_dict())
    assert restored.project == rec.project
    assert restored.version == rec.version
    assert restored.signer == rec.signer
    assert restored.signature == rec.signature
    assert restored.note == rec.note


def test_record_default_note_empty():
    rec = sign_entry(CIPHER, "proj", 1, "bob", SECRET)
    assert rec.note == ""


def test_signed_at_is_set():
    rec = make_record()
    assert rec.signed_at != ""
    assert "T" in rec.signed_at  # ISO format


# --- sign_entry / verify_entry ---

def test_verify_correct_secret_returns_true():
    rec = sign_entry(CIPHER, "proj", 1, "alice", SECRET)
    assert verify_entry(CIPHER, rec, SECRET) is True


def test_verify_wrong_secret_returns_false():
    rec = sign_entry(CIPHER, "proj", 1, "alice", SECRET)
    assert verify_entry(CIPHER, rec, "wrong-secret") is False


def test_verify_tampered_ciphertext_returns_false():
    rec = sign_entry(CIPHER, "proj", 1, "alice", SECRET)
    tampered = CIPHER + b"extra"
    assert verify_entry(tampered, rec, SECRET) is False


def test_different_ciphertexts_produce_different_signatures():
    r1 = sign_entry(b"data-one", "proj", 1, "alice", SECRET)
    r2 = sign_entry(b"data-two", "proj", 1, "alice", SECRET)
    assert r1.signature != r2.signature


# --- SignatureStore ---

def test_get_nonexistent_returns_none(sig_store):
    assert sig_store.get("missing", 1) is None


def test_add_and_get(sig_store):
    rec = make_record(project="app", version=3)
    sig_store.add(rec)
    fetched = sig_store.get("app", 3)
    assert fetched is not None
    assert fetched.signature == rec.signature
    assert fetched.signer == rec.signer


def test_list_project_returns_all(sig_store):
    for v in [1, 2, 3]:
        sig_store.add(make_record(project="app", version=v))
    sig_store.add(make_record(project="other", version=1))
    results = sig_store.list_project("app")
    assert len(results) == 3
    assert all(r.project == "app" for r in results)


def test_list_project_empty(sig_store):
    assert sig_store.list_project("ghost") == []


def test_store_persists_to_disk(tmp_path):
    rec = make_record(project="persist", version=7)
    store1 = SignatureStore(str(tmp_path))
    store1.add(rec)
    store2 = SignatureStore(str(tmp_path))
    fetched = store2.get("persist", 7)
    assert fetched is not None
    assert fetched.signature == rec.signature


def test_get_returns_latest_for_duplicate_versions(sig_store):
    """If two records exist for same version, get returns the last added."""
    r1 = sign_entry(b"v1-data", "app", 1, "alice", SECRET)
    r2 = sign_entry(b"v1-data-new", "app", 1, "bob", SECRET)
    sig_store.add(r1)
    sig_store.add(r2)
    fetched = sig_store.get("app", 1)
    assert fetched.signer == "bob"
