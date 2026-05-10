from __future__ import annotations

import importlib.util
import json
import os
import sqlite3
import sys
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SUPERVISOR_DIR = ROOT / "supervisor"
sys.path.insert(0, str(SUPERVISOR_DIR))

spec = importlib.util.spec_from_file_location(
    "unifai_supervisor_runtime_escalation_order",
    SUPERVISOR_DIR / "supervisor.py",
)
supervisor_runtime = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(supervisor_runtime)


class RecordingKeymanGuardian:
    def __init__(self, events: list[str]):
        self.events = events
        self.calls: list[dict] = []

    def evaluate_capability_request(self, request: dict) -> dict:
        self.events.append("keyman")
        self.calls.append(dict(request))
        return {
            "approved": True,
            "is_authorized": True,
            "decision": "issue_grant",
            "reason": "approved-for-test",
            "ttl_seconds": int(request.get("ttl_seconds", 300)),
            "request_id": request.get("request_id", "test-request"),
        }


class RecordingBillGate(supervisor_runtime.BillGate):
    def __init__(self, config, events: list[str]):
        super().__init__(config)
        self.events = events

    def request_budget(self, estimated_tokens: int) -> bool:
        self.events.append("bill_request")
        return super().request_budget(estimated_tokens)

    def commit_usage(self, actual_tokens: int) -> None:
        self.events.append("bill_commit")
        return super().commit_usage(actual_tokens)


class EnvInspectingProvider(supervisor_runtime.ProviderAdapter):
    def __init__(self, events: list[str], env_key: str):
        self.events = events
        self.env_key = env_key
        self.seen_secret = None

    def stream_message(self, prompt: str):
        self.events.append("provider")
        self.seen_secret = os.environ.get(self.env_key)
        yield supervisor_runtime.MessageDelta(content="ok", finish_reason=None, usage=None)
        yield supervisor_runtime.MessageDelta(
            content="",
            finish_reason="stop",
            usage={"total_tokens": max(1, len(prompt) // 4)},
        )


class GovernedEscalationOrderTests(unittest.TestCase):
    def _queue_llm_task(self, runtime, db_path: str, *, prompt: str, provider_secrets: dict, secret_scope: str):
        conn = supervisor_runtime.db()
        now = datetime.now(timezone.utc).isoformat(timespec="seconds")
        cursor = conn.execute(
            "INSERT INTO tasks (created_at, status, spec) VALUES (?, ?, ?)",
            (
                now,
                "queued",
                json.dumps(
                    {
                        "type": "llm",
                        "prompt": prompt,
                        "trace_id": "trace-governed-escalation-order",
                        "architect_instruction": "approved-for-test",
                        "ledger_entry": {"incident_id": "ledger-escalation-order-001"},
                        "agent": "oracle",
                        "provider_secrets": provider_secrets,
                        "secret_scope": secret_scope,
                    },
                    ensure_ascii=False,
                ),
            ),
        )
        conn.commit()
        conn.close()
        return int(cursor.lastrowid)

    def test_bill_blocks_before_keyman_scope_validation(self):
        with tempfile.TemporaryDirectory(prefix="unifai-order-bill-first-") as tmp_dir:
            tmp_root = Path(tmp_dir)
            supervisor_runtime.DB = str(tmp_root / "supervisor.db")
            supervisor_runtime.LOG = str(tmp_root / "supervisor.log")
            session_dir = tmp_root / "sessions"

            events: list[str] = []
            keyman = RecordingKeymanGuardian(events)
            runtime = supervisor_runtime.SupervisorRuntime(
                neo_guardian=None,
                session_vault=supervisor_runtime.SessionVault(storage_dir=str(session_dir)),
                bill_gate=RecordingBillGate(
                    supervisor_runtime.BudgetConfig(max_tokens=10, max_usd=0.10),
                    events,
                ),
                keyman_authorizer=keyman,
            )

            task_id = self._queue_llm_task(
                runtime,
                supervisor_runtime.DB,
                prompt="x" * 120,
                provider_secrets={"OPENAI_API_KEY": "sk-test"},
                secret_scope="openai-oauth",
            )

            processed = runtime.tick()
            self.assertTrue(processed)
            self.assertEqual(events, ["bill_request"])
            self.assertEqual(keyman.calls, [])

            verify_conn = sqlite3.connect(supervisor_runtime.DB)
            verify_conn.row_factory = sqlite3.Row
            row = verify_conn.execute(
                "SELECT status, error FROM tasks WHERE id=?",
                (task_id,),
            ).fetchone()
            verify_conn.close()

            self.assertIsNotNone(row)
            self.assertEqual(row["status"], "failed")
            self.assertIn("Budget exceeded", row["error"] or "")

    def test_keyman_runs_after_bill_and_before_secret_injection(self):
        with tempfile.TemporaryDirectory(prefix="unifai-order-keyman-after-bill-") as tmp_dir:
            tmp_root = Path(tmp_dir)
            supervisor_runtime.DB = str(tmp_root / "supervisor.db")
            supervisor_runtime.LOG = str(tmp_root / "supervisor.log")
            session_dir = tmp_root / "sessions"

            events: list[str] = []
            keyman = RecordingKeymanGuardian(events)
            provider = EnvInspectingProvider(events, "OPENAI_API_KEY")
            runtime = supervisor_runtime.SupervisorRuntime(
                neo_guardian=None,
                session_vault=supervisor_runtime.SessionVault(storage_dir=str(session_dir)),
                bill_gate=RecordingBillGate(
                    supervisor_runtime.BudgetConfig(max_tokens=100_000, max_usd=5.0),
                    events,
                ),
                provider_adapter=provider,
                keyman_authorizer=keyman,
            )

            task_id = self._queue_llm_task(
                runtime,
                supervisor_runtime.DB,
                prompt="hello world",
                provider_secrets={"OPENAI_API_KEY": "sk-test-secret"},
                secret_scope="openai-oauth",
            )

            processed = runtime.tick()
            self.assertTrue(processed)
            self.assertEqual(events, ["bill_request", "keyman", "provider", "bill_commit"])
            self.assertEqual(provider.seen_secret, "sk-test-secret")
            self.assertEqual(len(keyman.calls), 1)
            self.assertEqual(keyman.calls[0]["secret_alias"], "openai-oauth")

            verify_conn = sqlite3.connect(supervisor_runtime.DB)
            verify_conn.row_factory = sqlite3.Row
            row = verify_conn.execute(
                "SELECT status, llm_calls, error FROM tasks WHERE id=?",
                (task_id,),
            ).fetchone()
            verify_conn.close()

            self.assertIsNotNone(row)
            self.assertEqual(row["status"], "done")
            self.assertEqual(row["llm_calls"], 1)
            self.assertIn(row["error"], (None, ""))


if __name__ == "__main__":
    unittest.main()
