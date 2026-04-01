import importlib.util
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SUPERVISOR_DIR = ROOT / "supervisor"
sys.path.insert(0, str(SUPERVISOR_DIR))

from oracle.oracle import IncidentInput, OracleIncidentInterpreter

spec = importlib.util.spec_from_file_location("unifai_supervisor_runtime", SUPERVISOR_DIR / "supervisor.py")
supervisor_runtime = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(supervisor_runtime)
supervisor_decision_hook = supervisor_runtime.supervisor_decision_hook


class OracleMVPTests(unittest.TestCase):
    def setUp(self):
        self.oracle = OracleIncidentInterpreter()

    def test_auth_refresh_failure_classification(self):
        result = self.oracle.interpret(
            IncidentInput(
                source="Neo",
                task_id=1,
                stage="execution",
                task_spec={"type": "llm", "provider": "example"},
                error="401 unauthorized during refresh_token exchange",
            )
        )
        self.assertEqual(result.incident_type, "auth_refresh_failure")
        self.assertEqual(result.severity, "high")

    def test_missing_fallback_classification(self):
        result = self.oracle.interpret(
            IncidentInput(
                source="Supervisor",
                task_id=2,
                stage="execution",
                task_spec={"provider": "alpha", "fallback": None},
                error="provider failed and no fallback configured",
            )
        )
        self.assertEqual(result.incident_type, "fallback_missing")
        self.assertEqual(result.severity, "medium")

    def test_gateway_restart_severity_escalates(self):
        result = self.oracle.interpret(
            IncidentInput(
                source="Supervisor",
                task_id=3,
                stage="execution",
                task_spec={"cmd": "gateway restart", "restart_count": 2},
                error="gateway restart requested after crashloop",
                metadata={"restart_count": 2},
            )
        )
        self.assertEqual(result.incident_type, "gateway_restart")
        self.assertEqual(result.severity, "critical")

    def test_supervisor_hook_guarantees_no_action(self):
        result = self.oracle.interpret(
            IncidentInput(
                source="Neo",
                task_id=4,
                stage="pre_execution",
                task_spec={"cmd": "provider_client", "args": ["--legacy"]},
                error="provider client incompatible with supported api version",
            )
        )
        decision = supervisor_decision_hook(result)
        self.assertFalse(result.execute_actions)
        self.assertEqual(result.proposed_actions, ())
        self.assertTrue(decision["no_action_taken"])
        self.assertFalse(decision["notify_wilson"])
        self.assertIn("TODO", decision["todo"])


if __name__ == "__main__":
    unittest.main()
