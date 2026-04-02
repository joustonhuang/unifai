import importlib.util
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SUPERVISOR_DIR = ROOT / "supervisor"
sys.path.insert(0, str(SUPERVISOR_DIR))

spec = importlib.util.spec_from_file_location("unifai_supervisor_runtime_fuse", SUPERVISOR_DIR / "supervisor.py")
supervisor_runtime = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(supervisor_runtime)


class RecordingRegistry:
    def __init__(self):
        self.events = []

    def register_process(self, task_id, pid, pgid, status="running"):
        self.events.append(("register", str(task_id), int(pid), int(pgid), status))
        return {"task_id": str(task_id), "pid": int(pid), "pgid": int(pgid), "status": status}

    def unregister(self, task_id):
        self.events.append(("unregister", str(task_id)))
        return {"task_id": str(task_id)}


class FusePassthrough:
    def trip_agent(self, task_id, reason, grace_seconds=2):
        return {"ok": True, "task_id": str(task_id), "reason": reason, "status": "killed"}


class SupervisorFuseIntegrationTests(unittest.TestCase):
    def test_run_allowlisted_registers_and_unregisters_process(self):
        registry = RecordingRegistry()
        fuse = FusePassthrough()

        result = supervisor_runtime.run_allowlisted(
            "echo",
            ["hello"],
            task_id="task-echo",
            kill_registry=registry,
            fuse_manager=fuse,
        )

        self.assertEqual(result["returncode"], 0)
        self.assertIn("hello", result["stdout"])

        self.assertEqual(registry.events[0][0], "register")
        self.assertEqual(registry.events[0][1], "task-echo")
        self.assertEqual(registry.events[-1], ("unregister", "task-echo"))


if __name__ == "__main__":
    unittest.main()