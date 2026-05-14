"""Search across encrypted env entries for keys or values matching a pattern."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import List, Optional

from envault.store import LocalStore
from envault.crypto import decrypt


@dataclass
class SearchMatch:
    project: str
    version: int
    key: str
    value: str
    match_on: str  # 'key' | 'value'

    def to_dict(self) -> dict:
        return {
            "project": self.project,
            "version": self.version,
            "key": self.key,
            "value": self.value,
            "match_on": self.match_on,
        }


@dataclass
class SearchResult:
    pattern: str
    matches: List[SearchMatch] = field(default_factory=list)

    @property
    def found(self) -> bool:
        return len(self.matches) > 0

    def summary(self) -> str:
        if not self.found:
            return f"No matches found for pattern '{self.pattern}'."
        lines = [f"Found {len(self.matches)} match(es) for pattern '{self.pattern}':"]
        for m in self.matches:
            lines.append(
                f"  [{m.project}] v{m.version}  {m.key}={m.value!r}  (matched on {m.match_on})"
            )
        return "\n".join(lines)


def search_envs(
    store: LocalStore,
    password: str,
    pattern: str,
    *,
    projects: Optional[List[str]] = None,
    search_keys: bool = True,
    search_values: bool = False,
    latest_only: bool = True,
) -> SearchResult:
    """Search encrypted env entries across one or more projects."""
    regex = re.compile(pattern, re.IGNORECASE)
    result = SearchResult(pattern=pattern)

    target_projects = projects if projects else store.list_projects()

    for project in target_projects:
        versions = store.list_versions(project)
        if not versions:
            continue
        if latest_only:
            versions = [max(versions)]

        for version in versions:
            entry = store.load(project, version)
            if entry is None:
                continue
            try:
                plaintext = decrypt(entry.ciphertext, password, entry.salt)
            except Exception:
                continue

            from envault.env_file import parse_env
            env = parse_env(plaintext)

            for key, value in env.items():
                matched_on = None
                if search_keys and regex.search(key):
                    matched_on = "key"
                elif search_values and regex.search(value):
                    matched_on = "value"
                if matched_on:
                    result.matches.append(
                        SearchMatch(
                            project=project,
                            version=version,
                            key=key,
                            value=value,
                            match_on=matched_on,
                        )
                    )
    return result
