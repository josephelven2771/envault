"""Tests for the audit log module."""

import os
import pytest
from envault.audit import AuditEvent, AuditLog


@pytest.fixture
def audit_log(tmp_path):
    log_path = str(tmp_path / "audit" / "log.json")
    return AuditLog(log_path)


def make_event(action="push", project="myapp", version=1, user="alice@host"):
    return AuditEvent(action=action, project=project, version=version, user=user)


def test_record_and_retrieve(audit_log):
    event = make_event()
    audit_log.record(event)
    events = audit_log.get_events()
    assert len(events) == 1
    assert events[0].action == "push"
    assert events[0].project == "myapp"
    assert events[0].user == "alice@host"


def test_filter_by_project(audit_log):
    audit_log.record(make_event(project="alpha"))
    audit_log.record(make_event(project="beta"))
    audit_log.record(make_event(project="alpha", version=2))

    alpha_events = audit_log.get_events(project="alpha")
    assert len(alpha_events) == 2
    beta_events = audit_log.get_events(project="beta")
    assert len(beta_events) == 1


def test_empty_log_returns_empty_list(audit_log):
    assert audit_log.get_events() == []


def test_multiple_records_preserve_order(audit_log):
    for i in range(1, 4):
        audit_log.record(make_event(version=i, action="push" if i % 2 else "pull"))
    events = audit_log.get_events()
    assert [e.version for e in events] == [1, 2, 3]


def test_clear_removes_log_file(audit_log):
    audit_log.record(make_event())
    audit_log.clear()
    assert not os.path.exists(audit_log.log_path)
    assert audit_log.get_events() == []


def test_event_roundtrip_dict():
    event = make_event(note="initial push")
    restored = AuditEvent.from_dict(event.to_dict())
    assert restored.action == event.action
    assert restored.note == "initial push"
    assert restored.timestamp == event.timestamp


def test_record_note(audit_log):
    event = make_event()
    event.note = "hotfix deploy"
    audit_log.record(event)
    events = audit_log.get_events()
    assert events[0].note == "hotfix deploy"
