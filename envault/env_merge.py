"""Merge two env dicts with configurable conflict resolution strategies."""

from typing import Dict, Literal, Tuple

EnvDict = Dict[str, str]
Strategy = Literal["ours", "theirs", "ask", "union"]


class MergeConflict(Exception):
    """Raised when a conflict cannot be auto-resolved."""

    def __init__(self, key: str, ours: str, theirs: str) -> None:
        self.key = key
        self.ours = ours
        self.theirs = theirs
        super().__init__(f"Conflict on key '{key}': ours={ours!r}, theirs={theirs!r}")


def merge_envs(
    base: EnvDict,
    ours: EnvDict,
    theirs: EnvDict,
    strategy: Strategy = "ours",
) -> Tuple[EnvDict, list]:
    """
    Three-way merge of env dicts.

    Returns (merged_dict, list_of_conflict_keys).
    Conflicts are keys changed in both ours and theirs relative to base.
    """
    merged: EnvDict = {}
    conflicts: list = []

    all_keys = set(base) | set(ours) | set(theirs)

    for key in sorted(all_keys):
        base_val = base.get(key)
        our_val = ours.get(key)
        their_val = theirs.get(key)

        our_changed = our_val != base_val
        their_changed = their_val != base_val

        if not our_changed and not their_changed:
            # Unchanged in both — keep base (or drop if deleted in both)
            if base_val is not None:
                merged[key] = base_val
        elif our_changed and not their_changed:
            if our_val is not None:
                merged[key] = our_val
        elif their_changed and not our_changed:
            if their_val is not None:
                merged[key] = their_val
        else:
            # Both changed — conflict
            conflicts.append(key)
            if strategy == "ours":
                if our_val is not None:
                    merged[key] = our_val
            elif strategy == "theirs":
                if their_val is not None:
                    merged[key] = their_val
            elif strategy == "union":
                # Keep both, prefer ours for the value
                val = our_val if our_val is not None else their_val
                if val is not None:
                    merged[key] = val
            elif strategy == "ask":
                raise MergeConflict(key, our_val or "", their_val or "")

    return merged, conflicts
