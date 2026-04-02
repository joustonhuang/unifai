from __future__ import annotations

import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from supervisor.types.specs_ledger import SpecsLedger, TaskSpec


class SpecsLedgerTests(unittest.TestCase):
    def test_add_task_and_get_pending_tasks(self) -> None:
        ledger = SpecsLedger()
        spec = TaskSpec(
            task_id="keyman-rule9",
            description="Build immutable short-term mission memory",
            constraints=[
                "Never expose raw secrets",
                "Use deterministic task context",
            ],
            acceptance_criteria=[
                "Prompt context includes all constraints",
                "Prompt context includes all acceptance criteria",
            ],
        )

        ledger.add_task(spec)
        pending = ledger.get_pending_tasks()

        self.assertEqual(len(pending), 1)
        self.assertEqual(pending[0].task_id, "keyman-rule9")
        self.assertEqual(pending[0].status, "pending")
        self.assertEqual(
            pending[0].constraints,
            ["Never expose raw secrets", "Use deterministic task context"],
        )
        self.assertEqual(
            pending[0].acceptance_criteria,
            [
                "Prompt context includes all constraints",
                "Prompt context includes all acceptance criteria",
            ],
        )

    def test_mark_task_status_removes_task_from_pending_list(self) -> None:
        ledger = SpecsLedger()
        spec = TaskSpec(
            task_id="spec-2",
            description="Track immutable acceptance criteria",
            constraints=["No mutable global state"],
            acceptance_criteria=["Status transition is deterministic"],
        )
        ledger.add_task(spec)

        ledger.mark_task_status("spec-2", "done")

        self.assertEqual(ledger.get_pending_tasks(), [])

    def test_get_task_prompt_context_includes_all_mission_fields(self) -> None:
        ledger = SpecsLedger()
        spec = TaskSpec(
            task_id="spec-3",
            description="Inject mission-safe context into system prompt",
            constraints=["Never rely on volatile LLM memory", "Enforce Rule 9 ledger contract"],
            acceptance_criteria=["Mission objective appears in context", "Constraint list appears in context"],
        )
        ledger.add_task(spec)

        context = ledger.get_task_prompt_context("spec-3")

        self.assertIn("Task ID: spec-3", context)
        self.assertIn("Status: pending", context)
        self.assertIn("Inject mission-safe context into system prompt", context)
        self.assertIn("Never rely on volatile LLM memory", context)
        self.assertIn("Enforce Rule 9 ledger contract", context)
        self.assertIn("Mission objective appears in context", context)
        self.assertIn("Constraint list appears in context", context)

    def test_prompt_context_raises_for_unknown_task(self) -> None:
        ledger = SpecsLedger()

        with self.assertRaises(KeyError):
            ledger.get_task_prompt_context("missing-task")


if __name__ == "__main__":
    unittest.main()
