#!/usr/bin/env python3
"""
Wilson: human-facing presenter for supervisor/oracle state.

This module is intentionally narrow.
Wilson formats already-produced system truth into human-readable summaries.
Wilson does not decide policy, execute actions, mutate system state, or read raw
world state beyond the structured inputs provided to it.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional


@dataclass(frozen=True)
class WilsonInput:
    """Structured input prepared by Supervisor for human-facing rendering."""

    trace_id: Optional[str]
    notify_level: str
    incident_type: str
    summary: str
    rationale: str
    recommended_actions: list[str]
    metadata: Dict[str, Any]


@dataclass(frozen=True)
class WilsonOutput:
    """Human-readable message package. Presentation only; no authority."""

    title: str
    body: str
    notify_level: str
    trace_id: Optional[str]


class WilsonPresenter:
    """Translate structured supervisor/oracle context into readable operator text."""

    def render(self, item: WilsonInput) -> WilsonOutput:
        title = self._title_for(item)
        body_lines = [
            item.summary.strip(),
            "",
            f"Reason: {item.rationale.strip()}",
        ]

        if item.recommended_actions:
            body_lines.extend([
                "",
                "Suggested actions:",
            ])
            for idx, action in enumerate(item.recommended_actions, start=1):
                body_lines.append(f"{idx}. {action}")

        if item.trace_id:
            body_lines.extend([
                "",
                f"Trace ID: {item.trace_id}",
            ])

        return WilsonOutput(
            title=title,
            body="\n".join(body_lines).strip(),
            notify_level=item.notify_level,
            trace_id=item.trace_id,
        )

    def _title_for(self, item: WilsonInput) -> str:
        if item.incident_type == "provider_client_incompatibility":
            return "⚠️ Advanced AI feature temporarily unavailable"
        if item.incident_type == "auth_refresh_failure":
            return "⚠️ Provider authentication failure"
        if item.incident_type == "fallback_missing":
            return "⚠️ Fallback model not configured"
        if item.incident_type == "gateway_restart":
            return "⚠️ Gateway instability detected"
        return "⚠️ Incident detected"
