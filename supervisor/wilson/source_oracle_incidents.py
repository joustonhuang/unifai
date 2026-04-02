#!/usr/bin/env python3
"""Wilson v1 truth source reader: oracle_incidents table.

Read-only adapter over supervisor-owned SQLite truth.
"""

from __future__ import annotations

import json
import sqlite3
from typing import Any, Dict, List


def read_oracle_incidents(db_path: str, limit: int = 100) -> List[Dict[str, Any]]:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        rows = conn.execute(
            """
            SELECT id, ts, trace_id, incident_class, severity, confidence,
                   probable_root_cause, degradation, should_notify_wilson,
                   wilson_message, payload_json
            FROM oracle_incidents
            ORDER BY id DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
        out = []
        for row in rows:
            item = dict(row)
            payload = item.get("payload_json")
            if payload:
                try:
                    item["payload_json"] = json.loads(payload)
                except json.JSONDecodeError:
                    pass
            out.append(item)
        return out
    finally:
        conn.close()
