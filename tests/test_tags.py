"""Tests for envault.tags (TagStore and Tag)."""

import pytest

from envault.tags import Tag, TagStore


@pytest.fixture
def tag_store(tmp_path):
    return TagStore(str(tmp_path))


def make_tag(name="v1.0", project="myapp", version=3, user="alice@x", note=""):
    return Tag(name=name, project=project, version=version, created_by=user, note=note)


# ---------------------------------------------------------------------------
# Tag dataclass
# ---------------------------------------------------------------------------

def test_tag_roundtrip_dict():
    tag = make_tag(note="initial release")
    assert Tag.from_dict(tag.to_dict()) == tag


def test_tag_default_note_empty():
    data = {"name": "v2", "project": "p", "version": 1, "created_by": "bob"}
    tag = Tag.from_dict(data)
    assert tag.note == ""


# ---------------------------------------------------------------------------
# TagStore – basic CRUD
# ---------------------------------------------------------------------------

def test_set_and_get_tag(tag_store):
    tag = make_tag()
    tag_store.set_tag(tag)
    retrieved = tag_store.get_tag("myapp", "v1.0")
    assert retrieved == tag


def test_get_nonexistent_returns_none(tag_store):
    assert tag_store.get_tag("ghost", "v9") is None


def test_list_tags_sorted(tag_store):
    for name in ("v3", "v1", "v2"):
        tag_store.set_tag(make_tag(name=name))
    names = [t.name for t in tag_store.list_tags("myapp")]
    assert names == ["v1", "v2", "v3"]


def test_list_tags_empty_project(tag_store):
    assert tag_store.list_tags("unknown") == []


def test_overwrite_existing_tag(tag_store):
    tag_store.set_tag(make_tag(version=1))
    tag_store.set_tag(make_tag(version=5))
    assert tag_store.get_tag("myapp", "v1.0").version == 5


def test_delete_existing_tag(tag_store):
    tag_store.set_tag(make_tag())
    result = tag_store.delete_tag("myapp", "v1.0")
    assert result is True
    assert tag_store.get_tag("myapp", "v1.0") is None


def test_delete_nonexistent_tag_returns_false(tag_store):
    assert tag_store.delete_tag("myapp", "ghost") is False


# ---------------------------------------------------------------------------
# Persistence across instances
# ---------------------------------------------------------------------------

def test_tags_persist_across_instances(tmp_path):
    store1 = TagStore(str(tmp_path))
    store1.set_tag(make_tag(name="stable", version=7))

    store2 = TagStore(str(tmp_path))
    tag = store2.get_tag("myapp", "stable")
    assert tag is not None
    assert tag.version == 7


def test_multiple_projects_isolated(tag_store):
    tag_store.set_tag(make_tag(project="alpha", name="v1", version=1))
    tag_store.set_tag(make_tag(project="beta", name="v1", version=99))
    assert tag_store.get_tag("alpha", "v1").version == 1
    assert tag_store.get_tag("beta", "v1").version == 99
