"""Tests for envault.env_variables interpolation module."""
from __future__ import annotations

import pytest

from envault.env_variables import (
    InterpolationResult,
    InterpolationWarning,
    interpolate,
    list_references,
)


# ---------------------------------------------------------------------------
# interpolate()
# ---------------------------------------------------------------------------

def test_no_references_unchanged():
    env = {"HOST": "localhost", "PORT": "5432"}
    result = interpolate(env)
    assert result.resolved == env
    assert result.clean


def test_brace_reference_resolved():
    env = {"BASE": "postgres", "URL": "${BASE}://localhost"}
    result = interpolate(env)
    assert result.resolved["URL"] == "postgres://localhost"
    assert result.clean


def test_bare_dollar_reference_resolved():
    env = {"HOST": "db", "CONN": "$HOST:5432"}
    result = interpolate(env)
    assert result.resolved["CONN"] == "db:5432"
    assert result.clean


def test_chained_references_resolved():
    env = {"A": "hello", "B": "${A}_world", "C": "${B}!"}
    result = interpolate(env)
    assert result.resolved["C"] == "hello_world!"


def test_undefined_reference_produces_warning():
    env = {"URL": "${MISSING}/path"}
    result = interpolate(env)
    assert not result.clean
    assert any(w.ref == "MISSING" for w in result.warnings)
    # original token preserved
    assert "${MISSING}" in result.resolved["URL"]


def test_self_reference_produces_warning():
    env = {"A": "${A}_suffix"}
    result = interpolate(env)
    assert not result.clean
    assert any(w.ref == "A" for w in result.warnings)


def test_multiple_references_in_one_value():
    env = {"PROTO": "https", "HOST": "example.com", "URL": "${PROTO}://${HOST}"}
    result = interpolate(env)
    assert result.resolved["URL"] == "https://example.com"
    assert result.clean


def test_interpolation_warning_str():
    w = InterpolationWarning(key="URL", ref="MISSING", message="undefined variable")
    assert "URL" in str(w)
    assert "MISSING" in str(w)


# ---------------------------------------------------------------------------
# list_references()
# ---------------------------------------------------------------------------

def test_list_references_empty_env():
    assert list_references({}) == {}


def test_list_references_no_refs():
    env = {"FOO": "bar", "BAZ": "qux"}
    assert list_references(env) == {}


def test_list_references_brace_style():
    env = {"URL": "${PROTO}://${HOST}/path"}
    refs = list_references(env)
    assert set(refs["URL"]) == {"PROTO", "HOST"}


def test_list_references_bare_style():
    env = {"CONN": "$HOST:$PORT"}
    refs = list_references(env)
    assert set(refs["CONN"]) == {"HOST", "PORT"}


def test_list_references_excludes_self():
    env = {"A": "${A}_extra"}
    refs = list_references(env)
    assert "A" not in refs.get("A", [])


def test_list_references_deduplicates():
    env = {"X": "${Y}-${Y}"}
    refs = list_references(env)
    assert refs["X"].count("Y") == 1
