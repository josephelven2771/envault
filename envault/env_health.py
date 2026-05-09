"""Health check module: reports overall status of a project's env store."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from envault.store import LocalStore
from envault.crypto import decrypt
from envault.env_lint import lint_env, LintIssue
from envault.secrets_scan import scan_env, ScanFinding


@dataclass
class HealthReport:
    project: str
    version: int
    has_entry: bool
    decrypt_ok: bool
    lint_issues: List[LintIssue] = field(default_factory=list)
    scan_findings: List[ScanFinding] = field(default_factory=list)
    error: Optional[str] = None

    @property
    def healthy(self) -> bool:
        if not self.has_entry or not self.decrypt_ok:
            return False
        errors = [i for i in self.lint_issues if i.level == "error"]
        return len(errors) == 0 and len(self.scan_findings) == 0

    def summary(self) -> str:
        status = "OK" if self.healthy else "DEGRADED"
        lines = [f"[{status}] {self.project} (version {self.version})"]
        if self.error:
            lines.append(f"  ERROR: {self.error}")
        for issue in self.lint_issues:
            lines.append(f"  LINT [{issue.level.upper()}] {issue.key}: {issue.message}")
        for finding in self.scan_findings:
            lines.append(f"  SCAN [{finding.severity.upper()}] {finding.key}: {finding.reason}")
        if self.healthy:
            lines.append("  No issues found.")
        return "\n".join(lines)


def check_health(store: LocalStore, project: str, password: str) -> HealthReport:
    """Run a full health check on the latest version of a project."""
    entry = store.load(project)
    if entry is None:
        return HealthReport(
            project=project,
            version=0,
            has_entry=False,
            decrypt_ok=False,
            error="No entry found for project.",
        )

    try:
        plaintext = decrypt(entry.ciphertext, password)
        env_vars = dict(
            line.split("=", 1)
            for line in plaintext.splitlines()
            if "=" in line and not line.startswith("#")
        )
        decrypt_ok = True
    except Exception as exc:  # noqa: BLE001
        return HealthReport(
            project=project,
            version=entry.version,
            has_entry=True,
            decrypt_ok=False,
            error=f"Decryption failed: {exc}",
        )

    lint_issues = lint_env(env_vars)
    scan_findings = scan_env(env_vars)

    return HealthReport(
        project=project,
        version=entry.version,
        has_entry=True,
        decrypt_ok=decrypt_ok,
        lint_issues=lint_issues,
        scan_findings=scan_findings,
    )
