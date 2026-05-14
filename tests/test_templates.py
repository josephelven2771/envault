"""Tests for envault.templates module."""

import pytest

from envault.templates import Template, TemplateStore


@pytest.fixture
def tmpl_store(tmp_path):
    return TemplateStore(store_dir=str(tmp_path))


def make_template(name="base", keys=None, description=""):
    return Template(name=name, keys=keys or ["DB_URL", "SECRET_KEY"], description=description)


def test_template_roundtrip_dict():
    tmpl = make_template(description="A base template")
    assert Template.from_dict(tmpl.to_dict()) == tmpl


def test_template_default_description_empty():
    tmpl = Template(name="t", keys=["A"])
    assert tmpl.description == ""


def test_set_and_get(tmpl_store):
    tmpl = make_template()
    tmpl_store.set(tmpl)
    result = tmpl_store.get("base")
    assert result is not None
    assert result.name == "base"
    assert result.keys == ["DB_URL", "SECRET_KEY"]


def test_get_nonexistent_returns_none(tmpl_store):
    assert tmpl_store.get("missing") is None


def test_list_empty(tmpl_store):
    assert tmpl_store.list() == []


def test_list_multiple(tmpl_store):
    tmpl_store.set(make_template("a", ["X"]))
    tmpl_store.set(make_template("b", ["Y", "Z"]))
    names = {t.name for t in tmpl_store.list()}
    assert names == {"a", "b"}


def test_delete_existing(tmpl_store):
    tmpl_store.set(make_template())
    removed = tmpl_store.delete("base")
    assert removed is True
    assert tmpl_store.get("base") is None


def test_delete_nonexistent_returns_false(tmpl_store):
    assert tmpl_store.delete("ghost") is False


def test_overwrite_template(tmpl_store):
    tmpl_store.set(make_template(keys=["A"]))
    tmpl_store.set(make_template(keys=["A", "B"]))
    result = tmpl_store.get("base")
    assert result.keys == ["A", "B"]


def test_apply_filters_env(tmpl_store):
    tmpl_store.set(make_template(keys=["DB_URL", "SECRET_KEY"]))
    env = {"DB_URL": "postgres://", "SECRET_KEY": "abc", "EXTRA": "ignored"}
    filtered = tmpl_store.apply("base", env)
    assert filtered == {"DB_URL": "postgres://", "SECRET_KEY": "abc"}
    assert "EXTRA" not in filtered


def test_apply_missing_keys_skipped(tmpl_store):
    tmpl_store.set(make_template(keys=["A", "B"]))
    env = {"A": "1"}  # B is absent
    filtered = tmpl_store.apply("base", env)
    assert filtered == {"A": "1"}


def test_apply_unknown_template_raises(tmpl_store):
    with pytest.raises(KeyError, match="not found"):
        tmpl_store.apply("ghost", {"A": "1"})


def test_apply_empty_env_returns_empty(tmpl_store):
    """Applying a template against an empty env dict should return an empty dict."""
    tmpl_store.set(make_template(keys=["A", "B"]))
    filtered = tmpl_store.apply("base", {})
    assert filtered == {}


def test_template_with_empty_keys_list(tmpl_store):
    """A template with no keys should always produce an empty filtered result."""
    tmpl_store.set(Template(name="empty", keys=[]))
    env = {"A": "1", "B": "2"}
    filtered = tmpl_store.apply("empty", env)
    assert filtered == {}
