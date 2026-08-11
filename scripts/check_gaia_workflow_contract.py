#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
WORKFLOW = REPO_ROOT / ".github" / "workflows" / "gaia-smoke.yml"
TASKFILE = REPO_ROOT / "Taskfile.yml"


def fail(message: str) -> None:
    print(f"[FAIL] {message}")
    sys.exit(1)


def ok(message: str) -> None:
    print(f"[PASS] {message}")


workflow_text = WORKFLOW.read_text(encoding="utf-8")
taskfile_text = TASKFILE.read_text(encoding="utf-8")

for branch in ["main"]:
    if f"- '{branch}'" not in workflow_text and f"- {branch}" not in workflow_text:
        fail(f"Gaia smoke workflow missing branch trigger: {branch}")
ok("Gaia smoke workflow keeps the main branch trigger")

for required_step in [
    "Checkout repository",
    "Set up Python",
    "Install Task",
    "Run Gaia smoke task entrypoint",
]:
    if workflow_text.count(f"- name: {required_step}") != 1:
        fail(f"Gaia smoke workflow must invoke '{required_step}' exactly once")
ok("Gaia smoke workflow keeps the expected Task-driven step layout exactly once")

for required_snippet in [
    "name: gaia-smoke-test",
    "group: gaia-smoke-${{ github.ref }}",
    "cancel-in-progress: true",
    "- name: Checkout repository\n        uses: actions/checkout@v5",
    "- name: Set up Python\n        uses: actions/setup-python@v6\n        with:\n          python-version: \"3.11\"",
    "- name: Install Task\n        run: sh -c \"$(curl --location https://taskfile.dev/install.sh)\" -- -d -b /usr/local/bin",
    "- name: Run Gaia smoke task entrypoint\n        run: task smoke:gaia-ci",
]:
    if required_snippet not in workflow_text:
        fail(f"Gaia smoke workflow missing exact snippet: {required_snippet!r}")
ok("Gaia smoke workflow pins Node24-safe actions and dispatches the Task entrypoint")

for forbidden in [
    "run: bash ./scripts/smoke_test_gaia.sh",
    "pip install pyyaml",
]:
    if forbidden in workflow_text:
        fail(f"Gaia smoke workflow should not bypass the shared Task/PyYAML contract: {forbidden}")
ok("Gaia smoke workflow avoids bypassing the shared Task/PyYAML contract")

for required_snippet, label in [
    ("version: '3'", "Taskfile declares the Task schema version"),
    ("  smoke:gaia:\n", "Taskfile defines the Gaia smoke script task"),
    ("      - bash ./scripts/smoke_test_gaia.sh", "Gaia smoke task still dispatches the shell smoke test"),
    ("  smoke:gaia-ci:\n", "Taskfile defines the Gaia CI entrypoint"),
    ("      - check:no-sandbox", "Gaia CI task keeps the no-sandbox gate"),
    ("      - check:runtime-baseline", "Gaia CI task keeps the runtime-baseline gate"),
    ("      - smoke:gaia", "Gaia CI task still depends on the smoke script task"),
    ('{{.PYTHON}} -c "import yaml; print(\\"pyyaml-ready\\")"', "Gaia CI task still verifies the PyYAML dependency"),
]:
    if required_snippet not in taskfile_text:
        fail(label)
ok("Taskfile preserves the Gaia smoke workflow entrypoints and local gates")

print("[PASS] Gaia smoke workflow contract looks sane")
