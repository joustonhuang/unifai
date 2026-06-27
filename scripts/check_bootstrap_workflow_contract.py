#!/usr/bin/env python3
from __future__ import annotations

import re
import sys
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
WORKFLOW = REPO_ROOT / ".github" / "workflows" / "bootstrap-preflight.yml"
UNIFAI_CI_WORKFLOW = REPO_ROOT / ".github" / "workflows" / "unifai-ci.yml"
LOCK_FILE = REPO_ROOT / "little7-installer" / "config" / "supervisor-secretvault.lock"


def fail(message: str) -> None:
    print(f"[FAIL] {message}")
    sys.exit(1)


def ok(message: str) -> None:
    print(f"[PASS] {message}")


with WORKFLOW.open("r", encoding="utf-8") as f:
    data = yaml.safe_load(f)

unifai_ci_text = UNIFAI_CI_WORKFLOW.read_text(encoding="utf-8")
lock_text = LOCK_FILE.read_text(encoding="utf-8")

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

for required_snippet, label in [
    ("submodule-integrity-audit:", "UnifAI CI workflow preserves the submodule-integrity-audit job"),
    ("🔐 Step 2: SHA Pin Verification Against Lock Contract", "UnifAI CI workflow preserves the SHA pin verification step"),
    ('grep "SUPERVISOR_SECRETVAULT_PIN="', "UnifAI CI parses SUPERVISOR_SECRETVAULT_PIN from the lock file"),
    ('"${{ env.SECRETVAULT_LOCK_FILE }}"', "UnifAI CI reads the configured SecretVault lock file path"),
    ('if [ -z "$PINNED_COMMIT" ]; then', "UnifAI CI fails closed when the pinned commit parse is empty"),
    ('git rev-parse HEAD', "UnifAI CI compares the parsed pin against the actual submodule commit"),
]:
    if required_snippet not in unifai_ci_text:
        fail(label)
ok("UnifAI CI preserves the SHA pin verification path for the SecretVault lock contract")

pin_parse_match = re.search(r'grep "([A-Z0-9_]+)="', unifai_ci_text)
if not pin_parse_match:
    fail("UnifAI CI missing a grep-based SecretVault pin extraction key")
pin_key = pin_parse_match.group(1)
ok(f"UnifAI CI exposes the grep-based SecretVault pin key: {pin_key}")

matching_lock_lines = [
    line for line in lock_text.splitlines() if line.startswith(f"{pin_key}=")
]
if len(matching_lock_lines) != 1:
    fail(f"SecretVault lock file must expose exactly one {pin_key}= line for workflow parsing")
ok(f"SecretVault lock file exposes exactly one {pin_key}= line for workflow parsing")

parsed_pin = matching_lock_lines[0].split("=", 1)[1].strip()
if not re.fullmatch(r"[0-9a-f]{40}", parsed_pin):
    fail(f"Workflow-parsed {pin_key} value is not a 40-char git commit SHA")
ok(f"Workflow-parsed {pin_key} value is a 40-char git commit SHA")

print("[PASS] Bootstrap workflow contract looks sane")
