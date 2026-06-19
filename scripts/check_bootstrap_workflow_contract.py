#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
WORKFLOW = REPO_ROOT / ".github" / "workflows" / "bootstrap-preflight.yml"


def fail(message: str) -> None:
    print(f"[FAIL] {message}")
    sys.exit(1)


def ok(message: str) -> None:
    print(f"[PASS] {message}")


with WORKFLOW.open("r", encoding="utf-8") as f:
    data = yaml.safe_load(f)

on_block = data.get("on", data.get(True))
if not isinstance(on_block, dict):
    fail("Workflow missing usable 'on' block")

push = on_block.get("push")
if not isinstance(push, dict):
    fail("Workflow missing push trigger")

branches = push.get("branches")
if not isinstance(branches, list):
    fail("Workflow push trigger missing branch list")

for branch in ["main", "master", "feat/**", "fix/**", "claude/**"]:
    if branch not in branches:
        fail(f"Workflow push trigger missing branch pattern: {branch}")
ok("Workflow push trigger covers main/master/feat/fix/claude branches")

jobs = data.get("jobs", {})
preflight_job = jobs.get("bootstrap-preflight")
if not isinstance(preflight_job, dict):
    fail("Workflow missing bootstrap-preflight job")

steps = preflight_job.get("steps")
if not isinstance(steps, list):
    fail("bootstrap-preflight job missing steps list")

step_names = [step.get("name", "") for step in steps if isinstance(step, dict)]
for required_step in [
    "Enforce No Sandbox Doctrine",
    "Enforce Runtime Baseline",
    "Run bootstrap installer preflight",
]:
    if step_names.count(required_step) != 1:
        fail(f"Workflow must invoke '{required_step}' exactly once")
ok("Workflow invokes doctrine, runtime baseline, and bootstrap preflight exactly once")

expected_runs = {
    "Enforce No Sandbox Doctrine": "python scripts/check_no_sandbox_doctrine.py",
    "Enforce Runtime Baseline": "python scripts/check_runtime_baseline.py",
}
for step in steps:
    if not isinstance(step, dict):
        continue
    name = step.get("name")
    expected = expected_runs.get(name)
    if not expected:
        continue
    run = step.get("run")
    if run is None or expected not in run:
        fail(f"Workflow step '{name}' must run {expected!r}")
ok("Workflow preserves no-sandbox and runtime-baseline enforcement steps")

expected_actions = {
    "Checkout repository": "actions/checkout@v5",
    "Set up Python": "actions/setup-python@v6",
    "Upload bootstrap preflight report": "actions/upload-artifact@v5",
}
for step in steps:
    if not isinstance(step, dict):
        continue
    name = step.get("name")
    expected = expected_actions.get(name)
    if not expected:
        continue
    uses = step.get("uses")
    if uses != expected:
        fail(f"Workflow step '{name}' must use {expected}, found {uses!r}")
ok("Workflow pins Node24-safe GitHub Action majors for checkout/setup-python/upload-artifact")

for forbidden in [
    "Run VM verifier red-path smoke test",
    "Run VM verifier GitHub fallback smoke test",
]:
    if forbidden in step_names:
        fail(f"Workflow should not duplicate smoke tests outside bootstrap preflight: {forbidden}")
ok("Workflow does not duplicate VM verifier smoke tests")

print("[PASS] Bootstrap workflow contract looks sane")
