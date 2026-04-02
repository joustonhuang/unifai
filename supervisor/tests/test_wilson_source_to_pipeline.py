import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from wilson.source_to_pipeline import oracle_row_to_wilson_record


class WilsonSourceToPipelineTests(unittest.TestCase):
    def test_oracle_row_maps_to_wilson_record(self):
        row = {
            "id": 7,
            "ts": "2026-04-03T00:00:00Z",
            "trace_id": "trace-7",
            "incident_class": "identity_control_plane_failure",
            "severity": "high",
            "confidence": 0.9,
            "probable_root_cause": "expired_or_invalid_oauth_token",
            "degradation": "codex_lane_unavailable",
            "should_notify_wilson": 1,
            "wilson_message": "Codex lane unavailable due to auth failure",
            "payload_json": {"component": "openai-codex", "task_id": "task-7"},
        }
        out = oracle_row_to_wilson_record(row)
        self.assertEqual(out["event_id"], "oracle_incident_7")
        self.assertEqual(out["event_type"], "identity_control_plane_failure")
        self.assertEqual(out["task_id"], "task-7")
        self.assertEqual(out["model_used"], "openai-codex")
        self.assertEqual(out["execution_source"], "cloud")


if __name__ == "__main__":
    unittest.main()
