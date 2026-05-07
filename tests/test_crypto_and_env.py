"""Tests for envault crypto and env_file modules."""

import pytest
from envault.crypto import encrypt, decrypt, derive_key, SALT_SIZE
from envault.env_file import parse_env, serialize_env, read_env_file, write_env_file


# --- crypto tests ---

def test_encrypt_decrypt_roundtrip():
    password = "super-secret-pass"
    plaintext = "DB_HOST=localhost\nDB_PORT=5432\n"
    encoded = encrypt(plaintext, password)
    assert isinstance(encoded, str)
    result = decrypt(encoded, password)
    assert result == plaintext


def test_encrypt_produces_different_ciphertext_each_time():
    password = "pass"
    plaintext = "KEY=value"
    assert encrypt(plaintext, password) != encrypt(plaintext, password)


def test_decrypt_wrong_password_raises():
    encoded = encrypt("SECRET=abc", "correct-password")
    with pytest.raises(Exception):
        decrypt(encoded, "wrong-password")


def test_derive_key_length():
    import os
    salt = os.urandom(SALT_SIZE)
    key = derive_key("mypassword", salt)
    assert len(key) == 32


def test_derive_key_is_deterministic():
    """Same password and salt should always produce the same key."""
    import os
    salt = os.urandom(SALT_SIZE)
    key1 = derive_key("mypassword", salt)
    key2 = derive_key("mypassword", salt)
    assert key1 == key2


def test_derive_key_differs_with_different_salt():
    """Different salts should produce different keys for the same password."""
    import os
    salt1 = os.urandom(SALT_SIZE)
    salt2 = os.urandom(SALT_SIZE)
    key1 = derive_key("mypassword", salt1)
    key2 = derive_key("mypassword", salt2)
    assert key1 != key2


# --- env_file tests ---

def test_parse_env_basic():
    content = "DB_HOST=localhost\nDB_PORT=5432\n"
    result = parse_env(content)
    assert result == {"DB_HOST": "localhost", "DB_PORT": "5432"}


def test_parse_env_ignores_comments_and_blanks():
    content = "# comment\n\nKEY=value\n"
    assert parse_env(content) == {"KEY": "value"}


def test_parse_env_strips_quotes():
    content = 'API_KEY="my secret key"\n'
    assert parse_env(content) == {"API_KEY": "my secret key"}


def test_serialize_env_roundtrip():
    data = {"HOST": "localhost", "PORT": "5432", "DEBUG": "true"}
    serialized = serialize_env(data)
    parsed = parse_env(serialized)
    assert parsed == data


def test_read_write_env_file(tmp_path):
    env_file = tmp_path / ".env"
    content = "KEY=value\nANOTHER=123\n"
    write_env_file(str(env_file), content)
    assert read_env_file(str(env_file)) == content
