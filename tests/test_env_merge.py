"""Tests for envault.env_merge."""

import pytest

from envault.env_merge import MergeConflict, merge_envs


BASE = {"A": "1", "B": "2", "C": "3"}


def test_no_changes_returns_base():
    merged, conflicts = merge_envs(BASE, BASE.copy(), BASE.copy())
    assert merged == BASE
    assert conflicts == []


def test_only_ours_changed():
    ours = {**BASE, "A": "updated"}
    merged, conflicts = merge_envs(BASE, ours, BASE.copy())
    assert merged["A"] == "updated"
    assert conflicts == []


def test_only_theirs_changed():
    theirs = {**BASE, "B": "new_b"}
    merged, conflicts = merge_envs(BASE, BASE.copy(), theirs)
    assert merged["B"] == "new_b"
    assert conflicts == []


def test_conflict_strategy_ours():
    ours = {**BASE, "C": "ours_c"}
    theirs = {**BASE, "C": "theirs_c"}
    merged, conflicts = merge_envs(BASE, ours, theirs, strategy="ours")
    assert merged["C"] == "ours_c"
    assert "C" in conflicts


def test_conflict_strategy_theirs():
    ours = {**BASE, "C": "ours_c"}
    theirs = {**BASE, "C": "theirs_c"}
    merged, conflicts = merge_envs(BASE, ours, theirs, strategy="theirs")
    assert merged["C"] == "theirs_c"
    assert "C" in conflicts


def test_conflict_strategy_union_prefers_ours():
    ours = {**BASE, "C": "ours_c"}
    theirs = {**BASE, "C": "theirs_c"}
    merged, conflicts = merge_envs(BASE, ours, theirs, strategy="union")
    assert merged["C"] == "ours_c"
    assert "C" in conflicts


def test_conflict_strategy_ask_raises():
    ours = {**BASE, "A": "x"}
    theirs = {**BASE, "A": "y"}
    with pytest.raises(MergeConflict) as exc_info:
        merge_envs(BASE, ours, theirs, strategy="ask")
    assert exc_info.value.key == "A"
    assert exc_info.value.ours == "x"
    assert exc_info.value.theirs == "y"


def test_key_added_in_ours_only():
    ours = {**BASE, "NEW": "val"}
    merged, conflicts = merge_envs(BASE, ours, BASE.copy())
    assert merged["NEW"] == "val"
    assert conflicts == []


def test_key_added_in_theirs_only():
    theirs = {**BASE, "NEW": "val"}
    merged, conflicts = merge_envs(BASE, BASE.copy(), theirs)
    assert merged["NEW"] == "val"
    assert conflicts == []


def test_key_deleted_in_ours():
    ours = {k: v for k, v in BASE.items() if k != "B"}
    merged, conflicts = merge_envs(BASE, ours, BASE.copy())
    assert "B" not in merged
    assert conflicts == []


def test_key_deleted_in_theirs():
    theirs = {k: v for k, v in BASE.items() if k != "C"}
    merged, conflicts = merge_envs(BASE, BASE.copy(), theirs)
    assert "C" not in merged
    assert conflicts == []


def test_merge_conflict_str():
    exc = MergeConflict("KEY", "a", "b")
    assert "KEY" in str(exc)
    assert "a" in str(exc)
    assert "b" in str(exc)
