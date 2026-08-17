from __future__ import annotations

import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from agents.wilson.wilson import RuntimeTruthBrief, WilsonAgent
from supervisor.plugins.keyman_guardian.session_vault import SessionVault
from supervisor.types.signal_dto import SignalDeriver, TaskSignal


class SignalDtoTests(unittest.TestCase):
    def test_task_signal_uses_redacted_summary(self):
        raw_truth = {
            "task_id": 42,
            "status": "failed",
            "error": "MOCK_SECRET_KEY_FOR_TEST",
            "stdout": "raw logs should never be used as summary",
        }

        signal = SignalDeriver.derive_task_signal(raw_truth)

        self.assertEqual(signal.task_id, "42")
        self.assertEqual(signal.status, "failed")
        self.assertIn(SessionVault.REDACTION_TOKEN, signal.summary)
        self.assertNotIn("MOCK_SECRET_KEY_FOR_TEST", signal.summary)
        self.assertNotIn("raw logs should never be used as summary", signal.summary)

    def test_agent_activity_signal_does_not_expose_payload(self):
        raw_truth = {
            "agent_name": "wilson",
            "tool_name": "read_file",
            "payload": "MOCK_SECRET_KEY_FOR_TEST",
        }

        signal = SignalDeriver.derive_agent_activity_signal(raw_truth)

        self.assertEqual(signal.agent_name, "wilson")
        self.assertEqual(signal.action_intent, "Using tool read_file")
        self.assertNotIn("MOCK_SECRET_KEY_FOR_TEST", signal.action_intent)

    def test_wilson_renders_only_task_signal_contract(self):
        signal = TaskSignal(task_id="task-77", status="done", summary="Sanitized summary")

        report = WilsonAgent.render_report(signal)

        self.assertIn("# Wilson Signal Report", report)
        self.assertIn("- Task ID: task-77", report)
        self.assertIn("- Status: done", report)
        self.assertIn("Sanitized summary", report)

    def test_wilson_rejects_non_signal_payload(self):
        with self.assertRaises(TypeError):
            WilsonAgent.render_report({"task_id": "x"})  # type: ignore[arg-type]

    def test_wilson_summarizes_runtime_truth_snapshot(self):
        snapshot = {
            "ok": True,
            "tasks": [
                {
                    "id": "task-77",
                    "status": "done",
                    "summary": "Sanitized summary",
                    "session_persisted": True,
                }
            ],
            "incidents": [
                {
                    "severity": "high",
                    "stage": "pre_execution",
                    "summary": "Authentication refresh failure detected.",
                }
            ],
            "events": [
                {
                    "event_type": "gaia_plan_received",
                    "actor": "Gaia",
                    "task_id": "task-77",
                    "target": "worker-1",
                }
            ],
        }

        brief = WilsonAgent.summarize_runtime_truth(snapshot)

        self.assertIsInstance(brief, RuntimeTruthBrief)
        self.assertEqual(brief.headline, "Oracle has a high incident in pre_execution.")
        self.assertIn(
            "Latest task task-77 is done: Sanitized summary Session persisted.",
            brief.details,
        )
        self.assertEqual(
            brief.as_dict(),
            {
                "headline": "Oracle has a high incident in pre_execution.",
                "details": brief.details,
            },
        )

    def test_wilson_summarizes_empty_runtime_truth_snapshot(self):
        brief = WilsonAgent.summarize_runtime_truth(
            {"ok": True, "tasks": [], "incidents": [], "events": []}
        )

        self.assertEqual(brief.headline, "Runtime truth is quiet.")
        self.assertEqual(
            brief.details,
            ["No recent Supervisor, Oracle, or Gaia rows were available."],
        )

    def test_wilson_rejects_non_dict_runtime_truth_snapshot(self):
        with self.assertRaises(TypeError):
            WilsonAgent.summarize_runtime_truth([])  # type: ignore[arg-type]


if __name__ == "__main__":
    unittest.main()
