"""Detect and report inter-key dependencies within .env files."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional
import re


# Matches ${VAR} or $VAR style references inside values
_REF_PATTERN = re.compile(r"\$\{([A-Za-z_][A-Za-z0-9_]*)\}|\$([A-Za-z_][A-Za-z0-9_]*)")


@dataclass
class DependencyGraph:
    """Directed graph of key -> keys it references."""
    edges: Dict[str, List[str]] = field(default_factory=dict)

    def references(self, key: str) -> List[str]:
        """Return keys that *key* directly references."""
        return self.edges.get(key, [])

    def dependents(self, key: str) -> List[str]:
        """Return keys that reference *key*."""
        return [k for k, refs in self.edges.items() if key in refs]

    def all_keys(self) -> List[str]:
        return list(self.edges.keys())


def build_dependency_graph(env: Dict[str, str]) -> DependencyGraph:
    """Parse an env dict and build a dependency graph from variable references."""
    graph = DependencyGraph()
    for key, value in env.items():
        refs = [
            m.group(1) or m.group(2)
            for m in _REF_PATTERN.finditer(value)
        ]
        # Only include refs to keys that actually exist in this env
        graph.edges[key] = [r for r in refs if r in env and r != key]
    return graph


def find_cycles(graph: DependencyGraph) -> List[List[str]]:
    """Return all cycles in the dependency graph (list of cycles as key lists)."""
    visited: set = set()
    rec_stack: set = set()
    cycles: List[List[str]] = []

    def dfs(node: str, path: List[str]) -> None:
        visited.add(node)
        rec_stack.add(node)
        for neighbour in graph.references(node):
            if neighbour not in visited:
                dfs(neighbour, path + [neighbour])
            elif neighbour in rec_stack:
                cycle_start = path.index(neighbour)
                cycles.append(path[cycle_start:])
        rec_stack.discard(node)

    for key in graph.all_keys():
        if key not in visited:
            dfs(key, [key])

    return cycles


def format_dependency_report(graph: DependencyGraph) -> str:
    """Return a human-readable dependency report."""
    lines: List[str] = []
    for key in sorted(graph.all_keys()):
        refs = graph.references(key)
        if refs:
            lines.append(f"  {key} -> {', '.join(refs)}")
    if not lines:
        return "No inter-key dependencies found."
    cycles = find_cycles(graph)
    report = "Dependency graph:\n" + "\n".join(lines)
    if cycles:
        cycle_strs = ", ".join(" -> ".join(c) for c in cycles)
        report += f"\n\nWARNING: Circular references detected: {cycle_strs}"
    return report
