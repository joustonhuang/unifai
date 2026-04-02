#!/usr/bin/env python3
"""Mr. Wilson MVP: read-only log-to-data transformation pipeline.

Wilson does not think, decide, or execute.
Wilson normalizes logs, compresses repeated events, summarizes agent/task state,
and emits structured data for UI consumption.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, asdict
from hashlib import sha256
from typing import Any, Dict, Iterable, List


@dataclass(frozen=True)
class WilsonEvent:
    event_id: str
    timestamp: str
    agent: str
    event_type: str
    message: str
    metadata: Dict[str, Any]
    count: int = 1


@dataclass(frozen=True)
class WilsonAgentState:
    agent: str
    current_state: str
    last_event: str
    activity_level: str


@dataclass(frozen=True)
class WilsonTaskState:
    task_id: str
    agent: str
    status: str
    model_used: str | None
    execution_source: str | None


SECRET_EVENT_TYPES = {"secret_requested", "secret_granted", "secret_returned"}
CRITICAL_EVENT_TYPES = {"fuse_triggered", "kill_signal", "repeated_failure", "abnormal_retry_loop"}


def anonymize_reference(value: str | None) -> str | None:
    if not value:
        return None
    return sha256(value.encode()).hexdigest()[:12]


def normalize_event(record: Dict[str, Any]) -> WilsonEvent:
    event_type = str(record.get("event_type", "unknown"))
    metadata = dict(record.get("metadata", {}))
    message = str(record.get("message", ""))

    if event_type in SECRET_EVENT_TYPES:
        metadata = {
            "reference_id": anonymize_reference(str(metadata.get("reference_id") or metadata.get("secret_id") or ""))
        }
        message = event_type

    event_id = str(record.get("event_id") or f"evt_{anonymize_reference(str(record))}")
    return WilsonEvent(
        event_id=event_id,
        timestamp=str(record.get("timestamp", "")),
        agent=str(record.get("agent", "unknown")),
        event_type=event_type,
        message=message,
        metadata=metadata,
        count=int(record.get("count", 1)),
    )


def compress_events(events: Iterable[WilsonEvent]) -> List[WilsonEvent]:
    grouped: Dict[tuple, WilsonEvent] = {}
    counts = defaultdict(int)

    for event in events:
        key = (event.agent, event.event_type, event.message)
        counts[key] += event.count
        if key not in grouped:
            grouped[key] = event

    out: List[WilsonEvent] = []
    for key, event in grouped.items():
        out.append(WilsonEvent(**{**asdict(event), "count": counts[key]}))
    return out


def summarize_agents(events: Iterable[WilsonEvent]) -> List[WilsonAgentState]:
    per_agent: Dict[str, List[WilsonEvent]] = defaultdict(list)
    for event in events:
        per_agent[event.agent].append(event)

    out = []
    for agent, agent_events in per_agent.items():
        last = agent_events[-1]
        if last.event_type in {"task_failed", "repeated_failure", "abnormal_retry_loop"}:
            state = "error"
        elif last.event_type in {"task_waiting", "awaiting_input", "awaiting_approval"}:
            state = "waiting"
        elif last.event_type in {"task_started", "task_running", "retry_attempt"}:
            state = "working"
        else:
            state = "idle"

        activity_count = sum(e.count for e in agent_events)
        activity = "high" if activity_count >= 20 else "medium" if activity_count >= 5 else "low"
        out.append(WilsonAgentState(agent=agent, current_state=state, last_event=last.event_type, activity_level=activity))
    return out


def summarize_tasks(records: Iterable[Dict[str, Any]]) -> List[WilsonTaskState]:
    out = []
    for r in records:
        if not r.get("task_id"):
            continue
        out.append(
            WilsonTaskState(
                task_id=str(r.get("task_id")),
                agent=str(r.get("agent", "unknown")),
                status=str(r.get("status", "unknown")),
                model_used=r.get("model_used"),
                execution_source=r.get("execution_source"),
            )
        )
    return out


def extract_critical_events(events: Iterable[WilsonEvent]) -> List[Dict[str, Any]]:
    critical = []
    for e in events:
        if e.event_type in CRITICAL_EVENT_TYPES:
            critical.append(asdict(e))
        elif e.event_type == "retry_attempt" and e.count >= 10:
            critical.append(asdict(WilsonEvent(**{**asdict(e), "event_type": "abnormal_retry_loop"})))
    return critical


def build_wilson_output(raw_records: Iterable[Dict[str, Any]]) -> Dict[str, Any]:
    normalized = [normalize_event(r) for r in raw_records]
    compressed = compress_events(normalized)
    return {
        "agents": [asdict(x) for x in summarize_agents(normalized)],
        "events": [asdict(x) for x in compressed],
        "tasks": [asdict(x) for x in summarize_tasks(raw_records)],
        "summaries": extract_critical_events(compressed),
    }
