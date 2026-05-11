"""Notification system for envault events.

Supports sending notifications via multiple channels (stdout, webhook, email stub)
when significant events occur (push, pull, rotate, rollback, etc.).
"""

from __future__ import annotations

import json
import urllib.request
import urllib.error
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any


VALID_CHANNELS = {"stdout", "webhook"}
VALID_EVENTS = {"push", "pull", "rotate", "rollback", "import", "promote", "backup"}


@dataclass
class NotificationEvent:
    """Represents a notification event to be dispatched."""

    event_type: str          # e.g. 'push', 'pull', 'rotate'
    project: str
    actor: str
    message: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    occurred_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_type": self.event_type,
            "project": self.project,
            "actor": self.actor,
            "message": self.message,
            "metadata": self.metadata,
            "occurred_at": self.occurred_at,
        }


@dataclass
class NotificationConfig:
    """Configuration for a notification channel."""

    channel: str                    # 'stdout' or 'webhook'
    events: List[str]               # which event types trigger this config
    webhook_url: Optional[str] = None
    # Future: smtp_host, smtp_to, etc.

    def __post_init__(self) -> None:
        if self.channel not in VALID_CHANNELS:
            raise ValueError(f"Unknown channel '{self.channel}'. Valid: {VALID_CHANNELS}")
        for evt in self.events:
            if evt not in VALID_EVENTS:
                raise ValueError(f"Unknown event type '{evt}'. Valid: {VALID_EVENTS}")
        if self.channel == "webhook" and not self.webhook_url:
            raise ValueError("webhook channel requires a webhook_url")


def _dispatch_stdout(event: NotificationEvent) -> None:
    """Print a formatted notification to stdout."""
    ts = event.occurred_at
    print(f"[envault notify] [{ts}] {event.event_type.upper()} | project={event.project} "
          f"actor={event.actor} | {event.message}")


def _dispatch_webhook(event: NotificationEvent, url: str, timeout: int = 5) -> None:
    """POST the event payload as JSON to a webhook URL."""
    payload = json.dumps(event.to_dict()).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=payload,
        headers={"Content-Type": "application/json", "User-Agent": "envault/1.0"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            status = resp.status
            if status not in (200, 201, 202, 204):
                raise RuntimeError(f"Webhook returned unexpected status {status}")
    except urllib.error.URLError as exc:
        raise RuntimeError(f"Webhook delivery failed: {exc}") from exc


def notify(event: NotificationEvent, configs: List[NotificationConfig]) -> List[str]:
    """Dispatch an event to all matching notification configs.

    Returns a list of error messages for any failed dispatches
    (non-fatal — callers may log or surface these).
    """
    errors: List[str] = []

    for cfg in configs:
        if event.event_type not in cfg.events:
            continue

        try:
            if cfg.channel == "stdout":
                _dispatch_stdout(event)
            elif cfg.channel == "webhook":
                assert cfg.webhook_url  # validated in __post_init__
                _dispatch_webhook(event, cfg.webhook_url)
        except Exception as exc:  # noqa: BLE001
            errors.append(f"[{cfg.channel}] {exc}")

    return errors
