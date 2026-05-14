"""Quota enforcement: limit number of versions and projects stored."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from envault.store import LocalStore


DEFAULT_MAX_VERSIONS = 50
DEFAULT_MAX_PROJECTS = 20


@dataclass
class QuotaConfig:
    max_versions_per_project: int = DEFAULT_MAX_VERSIONS
    max_projects: int = DEFAULT_MAX_PROJECTS

    def to_dict(self) -> dict:
        return {
            "max_versions_per_project": self.max_versions_per_project,
            "max_projects": self.max_projects,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "QuotaConfig":
        return cls(
            max_versions_per_project=data.get("max_versions_per_project", DEFAULT_MAX_VERSIONS),
            max_projects=data.get("max_projects", DEFAULT_MAX_PROJECTS),
        )


@dataclass
class QuotaStatus:
    project: str
    version_count: int
    max_versions: int
    project_count: int
    max_projects: int

    @property
    def versions_exceeded(self) -> bool:
        return self.version_count >= self.max_versions

    @property
    def projects_exceeded(self) -> bool:
        return self.project_count >= self.max_projects

    def summary(self) -> str:
        lines = [
            f"Project '{self.project}': {self.version_count}/{self.max_versions} versions",
            f"Total projects: {self.project_count}/{self.max_projects}",
        ]
        if self.versions_exceeded:
            lines.append("WARNING: version quota reached for this project.")
        if self.projects_exceeded:
            lines.append("WARNING: project quota reached.")
        return "\n".join(lines)


class QuotaExceededError(Exception):
    pass


def check_quota(store: LocalStore, project: str, config: Optional[QuotaConfig] = None) -> QuotaStatus:
    """Return quota status for the given project without raising."""
    if config is None:
        config = QuotaConfig()
    all_projects = store.list_projects()
    versions = store.list_versions(project)
    return QuotaStatus(
        project=project,
        version_count=len(versions),
        max_versions=config.max_versions_per_project,
        project_count=len(all_projects),
        max_projects=config.max_projects,
    )


def enforce_quota(store: LocalStore, project: str, config: Optional[QuotaConfig] = None) -> QuotaStatus:
    """Check quota and raise QuotaExceededError if any limit is breached."""
    status = check_quota(store, project, config)
    if status.versions_exceeded:
        raise QuotaExceededError(
            f"Version quota exceeded for project '{project}': "
            f"{status.version_count}/{status.max_versions}."
        )
    if status.projects_exceeded and project not in store.list_projects():
        raise QuotaExceededError(
            f"Project quota exceeded: {status.project_count}/{status.max_projects} projects."
        )
    return status
