#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPT = REPO_ROOT / "scripts" / "check_gaia_workflow_contract.py"


def fail(message: str) -> None:
    print(f"[FAIL] {message}")
    sys.exit(1)


def ok(message: str) -> None:
    print(f"[PASS] {message}")


text = SCRIPT.read_text(encoding="utf-8")

required = [
    ('WORKFLOW = REPO_ROOT / ".github" / "workflows" / "gaia-smoke.yml"', "Gaia workflow contract checker targets gaia-smoke.yml"),
    ('TASKFILE = REPO_ROOT / "Taskfile.yml"', "Gaia workflow contract checker also targets Taskfile.yml"),
    ('workflow_text = WORKFLOW.read_text(encoding="utf-8")', "Gaia workflow contract checker reads the workflow as plain text"),
    ('taskfile_text = TASKFILE.read_text(encoding="utf-8")', "Gaia workflow contract checker reads the Taskfile as plain text"),
    ('workflow_text.count(f"- name: {required_step}") != 1', "Gaia workflow contract checker enforces exact step counts textually"),
    ('"- name: Checkout repository\\n        uses: actions/checkout@v5"', "Gaia workflow contract checker requires the checkout pin snippet"),
    ('"- name: Set up Python\\n        uses: actions/setup-python@v6\\n        with:\\n          python-version: \\"3.11\\""', "Gaia workflow contract checker requires the setup-python pin snippet"),
    ('"- name: Run Gaia smoke task entrypoint\\n        run: task smoke:gaia-ci"', "Gaia workflow contract checker requires the Gaia Task entrypoint snippet"),
    ('"run: bash ./scripts/smoke_test_gaia.sh"', "Gaia workflow contract checker guards against bypassing the Task entrypoint"),
    ('"pip install pyyaml"', "Gaia workflow contract checker guards against workflow-local PyYAML installs"),
    ('("  smoke:gaia-ci:\\n", "Taskfile defines the Gaia CI entrypoint")', "Gaia workflow contract checker validates the Gaia CI task textually"),
    ('pyyaml-ready', "Gaia workflow contract checker validates the shared PyYAML probe"),
]

for needle, message in required:
    if needle not in text:
        fail(message)
    ok(message)

print("[PASS] Gaia smoke workflow contract checker contract looks sane")
