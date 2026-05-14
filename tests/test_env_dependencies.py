"""Tests for envault.env_dependencies."""
from __future__ import annotations

import pytest

from envault.env_dependencies import (
    build_dependency_graph,
    find_cycles,
    format_dependency_report,
)


# ---------------------------------------------------------------------------
# build_dependency_graph
# ---------------------------------------------------------------------------

def test_no_references_gives_empty_edges():
    env = {"HOST": "localhost", "PORT": "5432"}
    graph = build_dependency_graph(env)
    assert graph.references("HOST") == []
    assert graph.references("PORT") == []


def test_dollar_brace_reference_detected():
    env = {"BASE_URL": "http://localhost", "API_URL": "${BASE_URL}/api"}
    graph = build_dependency_graph(env)
    assert "BASE_URL" in graph.references("API_URL")


def test_bare_dollar_reference_detected():
    env = {"HOST": "db", "DSN": "postgres://$HOST/mydb"}
    graph = build_dependency_graph(env)
    assert "HOST" in graph.references("DSN")


def test_reference_to_unknown_key_ignored():
    env = {"URL": "${UNDEFINED_VAR}/path"}
    graph = build_dependency_graph(env)
    assert graph.references("URL") == []


def test_self_reference_ignored():
    env = {"A": "${A}_suffix"}
    graph = build_dependency_graph(env)
    assert graph.references("A") == []


def test_dependents_found():
    env = {"HOST": "db", "DSN": "${HOST}/mydb", "URL": "${HOST}:5432"}
    graph = build_dependency_graph(env)
    deps = graph.dependents("HOST")
    assert "DSN" in deps
    assert "URL" in deps


def test_all_keys_present():
    env = {"A": "1", "B": "${A}", "C": "3"}
    graph = build_dependency_graph(env)
    assert set(graph.all_keys()) == {"A", "B", "C"}


# ---------------------------------------------------------------------------
# find_cycles
# ---------------------------------------------------------------------------

def test_no_cycles_in_simple_chain():
    env = {"A": "1", "B": "${A}", "C": "${B}"}
    graph = build_dependency_graph(env)
    assert find_cycles(graph) == []


def test_direct_cycle_detected():
    # Manually craft edges to simulate a cycle (parser strips self-refs)
    from envault.env_dependencies import DependencyGraph
    graph = DependencyGraph(edges={"A": ["B"], "B": ["A"]})
    cycles = find_cycles(graph)
    assert len(cycles) >= 1


def test_no_cycles_returns_empty_list():
    from envault.env_dependencies import DependencyGraph
    graph = DependencyGraph(edges={"X": ["Y"], "Y": [], "Z": ["X"]})
    assert find_cycles(graph) == []


# ---------------------------------------------------------------------------
# format_dependency_report
# ---------------------------------------------------------------------------

def test_format_no_deps():
    env = {"A": "1", "B": "2"}
    graph = build_dependency_graph(env)
    report = format_dependency_report(graph)
    assert "No inter-key dependencies" in report


def test_format_includes_key_and_ref():
    env = {"BASE": "http://x", "URL": "${BASE}/v1"}
    graph = build_dependency_graph(env)
    report = format_dependency_report(graph)
    assert "URL" in report
    assert "BASE" in report


def test_format_warns_on_cycle():
    from envault.env_dependencies import DependencyGraph
    graph = DependencyGraph(edges={"A": ["B"], "B": ["A"]})
    report = format_dependency_report(graph)
    assert "WARNING" in report
    assert "Circular" in report
