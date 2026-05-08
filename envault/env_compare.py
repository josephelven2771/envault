"""Compare two projects' env entries or two versions within a project."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

from envault.store import LocalStore
from envault.crypto import decrypt
from envault.env_file import parse_env


@dataclass
class CompareResult:
    project_a: str
    project_b: str
    only_in_a: List[str] = field(default_factory=list)
    only_in_b: List[str] = field(default_factory=list)
    differing_keys: List[str] = field(default_factory=list)
    matching_keys: List[str] = field(default_factory=list)

    def has_differences(self) -> bool:
        return bool(self.only_in_a or self.only_in_b or self.differing_keys)

    def summary(self) -> str:
        lines = [
            f"Comparing '{self.project_a}' vs '{self.project_b}'",
            f"  Only in {self.project_a}: {self.only_in_a or '(none)'}",
            f"  Only in {self.project_b}: {self.only_in_b or '(none)'}",
            f"  Differing values:        {self.differing_keys or '(none)'}",
            f"  Matching keys:           {len(self.matching_keys)}",
        ]
        return "\n".join(lines)


def _decrypt_latest(store: LocalStore, project: str, password: str) -> Dict[str, str]:
    """Return the parsed env dict for the latest version of *project*."""
    entry = store.load(project)
    if entry is None:
        raise KeyError(f"Project '{project}' not found in store.")
    raw = decrypt(entry.ciphertext, password)
    return parse_env(raw)


def compare_projects(
    store: LocalStore,
    project_a: str,
    project_b: str,
    password_a: str,
    password_b: Optional[str] = None,
) -> CompareResult:
    """Compare the latest env of two projects.

    If *password_b* is omitted the same password is used for both.
    """
    if password_b is None:
        password_b = password_a

    env_a = _decrypt_latest(store, project_a, password_a)
    env_b = _decrypt_latest(store, project_b, password_b)

    keys_a = set(env_a)
    keys_b = set(env_b)

    result = CompareResult(project_a=project_a, project_b=project_b)
    result.only_in_a = sorted(keys_a - keys_b)
    result.only_in_b = sorted(keys_b - keys_a)

    for key in sorted(keys_a & keys_b):
        if env_a[key] == env_b[key]:
            result.matching_keys.append(key)
        else:
            result.differing_keys.append(key)

    return result
