#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPT = REPO_ROOT / "scripts" / "check_bootstrap_workflow_contract.py"


def fail(message: str) -> None:
    print(f"[FAIL] {message}")
    sys.exit(1)


def ok(message: str) -> None:
    print(f"[PASS] {message}")


text = SCRIPT.read_text(encoding="utf-8")

required = [
    ('import re', 'Bootstrap workflow contract checker imports regex support for workflow key extraction'),
    ('WORKFLOW = REPO_ROOT / ".github" / "workflows" / "bootstrap-preflight.yml"', 'Bootstrap workflow contract checker targets bootstrap-preflight.yml'),
    ('UNIFAI_CI_WORKFLOW = REPO_ROOT / ".github" / "workflows" / "unifai-ci.yml"', 'Bootstrap workflow contract checker also targets unifai-ci.yml'),
    ('LOCK_FILE = REPO_ROOT / "little7-installer" / "config" / "supervisor-secretvault.lock"', 'Bootstrap workflow contract checker reads the SecretVault lock file'),
    ('TASKFILE = REPO_ROOT / "Taskfile.yml"', 'Bootstrap workflow contract checker also targets Taskfile.yml'),
    ('workflow_text = WORKFLOW.read_text(encoding="utf-8")', 'Bootstrap workflow contract checker reads bootstrap-preflight.yml as plain text'),
    ('unifai_ci_text = UNIFAI_CI_WORKFLOW.read_text(encoding="utf-8")', 'Bootstrap workflow contract checker inspects unifai-ci.yml text directly'),
    ('taskfile_text = TASKFILE.read_text(encoding="utf-8")', 'Bootstrap workflow contract checker inspects Taskfile.yml text directly'),
    ('workflow_text.count(f"- name: {required_step}") != 1', 'Bootstrap workflow contract checker enforces exact bootstrap-preflight step counts textually'),
    ('"- name: Install Task\\n        run: sh -c \\"$(curl --location https://taskfile.dev/install.sh)\\" -- -d -b /usr/local/bin"', 'Bootstrap workflow contract checker requires the Task installer step snippet'),
    ('"- name: Run bootstrap Task entrypoint\\n        run: task verify"', 'Bootstrap workflow contract checker requires the bootstrap task entrypoint snippet'),
    ('("version: \'3\'", "Taskfile declares the Task schema version")', 'Bootstrap workflow contract checker validates Taskfile version textually'),
    ('("  verify:\\n", "Taskfile defines the shared verify entrypoint")', 'Bootstrap workflow contract checker validates the shared verify task textually'),
    ('("  smoke:gaia-ci:\\n", "Taskfile defines the Gaia CI entrypoint")', 'Bootstrap workflow contract checker validates the Gaia CI task textually'),
    ('("submodule-integrity-audit:", "UnifAI CI workflow preserves the submodule-integrity-audit job")', 'Bootstrap workflow contract checker requires the UnifAI CI submodule audit job'),
    ('("🔐 Step 2: SHA Pin Verification Against Lock Contract", "UnifAI CI workflow preserves the SHA pin verification step")', 'Bootstrap workflow contract checker requires the live SHA pin verification step'),
    ('\'grep "SUPERVISOR_SECRETVAULT_PIN="\'', 'Bootstrap workflow contract checker requires parsing SUPERVISOR_SECRETVAULT_PIN from the lock file'),
    ('pin_parse_match = re.search(r\'grep "([A-Z0-9_]+)="\', unifai_ci_text)', 'Bootstrap workflow contract checker extracts the workflow pin key from the grep command'),
    ('matching_lock_lines = [', 'Bootstrap workflow contract checker validates lock lines against the workflow pin key'),
    ('if len(matching_lock_lines) != 1:', 'Bootstrap workflow contract checker requires exactly one matching lock line'),
    ('parsed_pin = matching_lock_lines[0].split("=", 1)[1].strip()', 'Bootstrap workflow contract checker simulates the workflow pin parse from the lock file'),
    ('re.fullmatch(r"[0-9a-f]{40}", parsed_pin)', 'Bootstrap workflow contract checker validates the parsed pin as a commit SHA'),
    ('\'"${{ env.SECRETVAULT_LOCK_FILE }}"\'', 'Bootstrap workflow contract checker requires the configured lock-file env path'),
    ('\'if [ -z "$PINNED_COMMIT" ]; then\'', 'Bootstrap workflow contract checker requires fail-closed empty pinned-commit handling'),
    ('\'git rev-parse HEAD\'', 'Bootstrap workflow contract checker requires submodule HEAD verification'),
]

for needle, message in required:
    if needle not in text:
        fail(message)
    ok(message)

if 'import yaml' in text:
    fail('Bootstrap workflow contract checker should avoid a PyYAML dependency on GitHub runners')
ok('Bootstrap workflow contract checker avoids a PyYAML dependency on GitHub runners')

print('[PASS] Bootstrap workflow contract checker contract looks sane')
