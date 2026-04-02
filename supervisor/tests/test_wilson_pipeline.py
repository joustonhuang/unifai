import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from wilson.pipeline import build_wilson_output, normalize_event


class WilsonPipelineTests(unittest.TestCase):
    def test_secret_event_is_safely_redacted(self):
        event = normalize_event({
            "timestamp": "2026-04-02T12:00:00Z",
            "agent": "keyman",
            "event_type": "secret_granted",
            "message": "secret returned with token abc123",
            "metadata": {"secret_id": "top-secret-token"},
        })
        self.assertEqual(event.message, "secret_granted")
        self.assertIn("reference_id", event.metadata)
        self.assertNotIn("abc123", str(event.metadata))
        self.assertNotIn("top-secret-token", str(event.metadata))

    def test_repeated_events_are_compressed(self):
        out = build_wilson_output([
            {"timestamp": "t1", "agent": "agent1", "event_type": "retry_attempt", "message": "retry attempt"},
            {"timestamp": "t2", "agent": "agent1", "event_type": "retry_attempt", "message": "retry attempt"},
            {"timestamp": "t3", "agent": "agent1", "event_type": "retry_attempt", "message": "retry attempt"},
        ])
        self.assertEqual(len(out["events"]), 1)
        self.assertEqual(out["events"][0]["count"], 3)

    def test_task_summary_present(self):
        out = build_wilson_output([
            {
                "timestamp": "t1",
                "agent": "oracle",
                "event_type": "task_running",
                "message": "running",
                "task_id": "task-1",
                "status": "running",
                "model_used": "gemma-3-4b",
                "execution_source": "local",
            }
        ])
        self.assertEqual(out["tasks"][0]["task_id"], "task-1")
        self.assertEqual(out["tasks"][0]["execution_source"], "local")


if __name__ == "__main__":
    unittest.main()
