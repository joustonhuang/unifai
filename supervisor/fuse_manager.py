#!/usr/bin/env python3
"""Process-based kill switch primitives for Rule 5 enforcement."""

from __future__ import annotations

import os
import signal
import threading
import time
from datetime import datetime, timezone
from typing import Any, Dict, Optional


class KillSwitchRegistry:
    """Thread-safe registry mapping task identifiers to process metadata."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._entries: Dict[str, Dict[str, Any]] = {}

    def register_process(self, task_id: str, pid: int, pgid: Optional[int] = None, status: str = "running") -> Dict[str, Any]:
        if pgid is None:
            pgid = os.getpgid(pid)

        entry = {
            "task_id": str(task_id),
            "pid": int(pid),
            "pgid": int(pgid),
            "status": status,
            "reason": None,
            "updated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        }
        with self._lock:
            self._entries[str(task_id)] = entry
        return dict(entry)

    def get(self, task_id: str) -> Optional[Dict[str, Any]]:
        with self._lock:
            entry = self._entries.get(str(task_id))
            return dict(entry) if entry is not None else None

    def update_status(self, task_id: str, status: str, reason: Optional[str] = None) -> Optional[Dict[str, Any]]:
        with self._lock:
            key = str(task_id)
            entry = self._entries.get(key)
            if entry is None:
                return None
            entry["status"] = status
            entry["reason"] = reason
            entry["updated_at"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
            return dict(entry)

    def unregister(self, task_id: str) -> Optional[Dict[str, Any]]:
        with self._lock:
            removed = self._entries.pop(str(task_id), None)
            return dict(removed) if removed is not None else None


class FuseManager:
    """Kills compromised agent process groups immediately on demand."""

    def __init__(self, registry: KillSwitchRegistry) -> None:
        self.registry = registry

    def trip_agent(self, task_id: str, reason: str, grace_seconds: int = 2) -> Dict[str, Any]:
        entry = self.registry.get(task_id)
        if entry is None:
            return {
                "ok": False,
                "task_id": str(task_id),
                "status": "not_found",
                "reason": reason,
            }

        pgid = entry.get("pgid")
        if pgid is None:
            self.registry.update_status(task_id, "kill_error", reason="missing process group id")
            updated = self.registry.get(task_id) or {"task_id": str(task_id)}
            updated.update({"ok": False, "status": "kill_error"})
            return updated

        self.registry.update_status(task_id, "tripping", reason=reason)

        term_sent = False
        kill_sent = False
        errors = []

        try:
            os.killpg(int(pgid), signal.SIGTERM)
            term_sent = True
        except ProcessLookupError:
            pass
        except Exception as exc:
            errors.append(str(exc))

        deadline = time.monotonic() + max(0, int(grace_seconds))
        while time.monotonic() < deadline:
            if not self._is_process_group_alive(int(pgid)):
                break
            time.sleep(0.1)

        if self._is_process_group_alive(int(pgid)):
            try:
                os.killpg(int(pgid), signal.SIGKILL)
                kill_sent = True
            except ProcessLookupError:
                pass
            except Exception as exc:
                errors.append(str(exc))

        if kill_sent:
            # Give the kernel a brief moment to settle process-group teardown.
            settle_deadline = time.monotonic() + 0.5
            while time.monotonic() < settle_deadline:
                if not self._is_process_group_alive(int(pgid)):
                    break
                time.sleep(0.05)

        group_alive = self._is_process_group_alive(int(pgid))
        final_status = "killed" if (not group_alive or kill_sent) else "kill_error"
        self.registry.update_status(task_id, final_status, reason=reason)

        updated = self.registry.get(task_id) or {"task_id": str(task_id)}
        updated.update(
            {
                "ok": final_status == "killed",
                "term_sent": term_sent,
                "kill_sent": kill_sent,
                "status": final_status,
                "errors": errors,
            }
        )
        return updated

    def _is_process_group_alive(self, pgid: int) -> bool:
        try:
            os.killpg(int(pgid), 0)
            return True
        except ProcessLookupError:
            return False
        except PermissionError:
            return True
