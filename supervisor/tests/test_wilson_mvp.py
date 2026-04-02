import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from wilson.wilson import WilsonInput, WilsonPresenter


class WilsonMVPTests(unittest.TestCase):
    def setUp(self):
        self.wilson = WilsonPresenter()

    def test_render_auth_failure_message(self):
        out = self.wilson.render(
            WilsonInput(
                trace_id="abc-123",
                notify_level="warning",
                incident_type="auth_refresh_failure",
                summary="Provider token refresh failed and lane is degraded.",
                rationale="Received repeated 401 refresh failures from provider.",
                recommended_actions=["reauthenticate_provider", "configure_fallback_model"],
                metadata={},
            )
        )
        self.assertEqual(out.notify_level, "warning")
        self.assertIn("Provider authentication failure", out.title)
        self.assertIn("reauthenticate_provider", out.body)
        self.assertIn("Trace ID: abc-123", out.body)

    def test_render_provider_client_incompatibility_title(self):
        out = self.wilson.render(
            WilsonInput(
                trace_id=None,
                notify_level="warning",
                incident_type="provider_client_incompatibility",
                summary="Codex client version mismatch detected.",
                rationale="Client drift requires update/restart.",
                recommended_actions=["restart_codex_client", "verify_client_version"],
                metadata={},
            )
        )
        self.assertIn("Advanced AI feature temporarily unavailable", out.title)
        self.assertIn("restart_codex_client", out.body)


if __name__ == "__main__":
    unittest.main()
