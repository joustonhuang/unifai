#!/usr/bin/env python3
"""Convert oracle_incidents rows into Wilson pipeline records."""

from __future__ import annotations

from typing import Any, Dict


def oracle_row_to_wilson_record(row: Dict[str, Any]) -> Dict[str, Any]:
    payload = row.get("payload_json")
    if not isinstance(payload, dict):
        payload = {}

    return {
        "event_id": f"oracle_incident_{row.get('id')}",
        "timestamp": row.get("ts", ""),
        "agent": "supervisor",
        "event_type": row.get("incident_class", "unknown_incident"),
        "message": row.get("wilson_message") or row.get("degradation") or "incident detected",
        "metadata": {
            "trace_id": row.get("trace_id"),
            "severity": row.get("severity"),
            "confidence": row.get("confidence"),
            "probable_root_cause": row.get("probable_root_cause"),
            "should_notify_wilson": row.get("should_notify_wilson"),
            "payload": payload,
        },
        "task_id": payload.get("task_id"),
        "status": "failed" if row.get("severity") in {"high", "critical"} else "degraded",
        "model_used": payload.get("component"),
        "execution_source": "cloud" if payload.get("component") else None,
    }
