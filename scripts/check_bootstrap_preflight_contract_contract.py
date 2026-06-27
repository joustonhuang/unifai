#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPT = REPO_ROOT / "scripts" / "check_bootstrap_preflight_contract.py"


def fail(message: str) -> None:
    print(f"[FAIL] {message}")
    sys.exit(1)


def ok(message: str) -> None:
    print(f"[PASS] {message}")


text = SCRIPT.read_text(encoding="utf-8")

required = [
    ('PREFLIGHT = REPO_ROOT / "scripts" / "bootstrap_installer_preflight.sh"', 'Bootstrap preflight contract checker targets bootstrap_installer_preflight.sh'),
    ('require_file "$REPO_ROOT/scripts/check_bootstrap_preflight_contract.py"', 'Bootstrap preflight contract checker requires the preflight checker itself'),
    ('require_file "$REPO_ROOT/scripts/check_bootstrap_workflow_contract_contract.py"', 'Bootstrap preflight contract checker requires the workflow contract checker contract'),
    ('require_file "$REPO_ROOT/scripts/check_github_check_gate.py"', 'Bootstrap preflight contract checker requires the GitHub check-gate inspector'),
    ('require_file "$REPO_ROOT/scripts/check_vm_host_readiness.sh"', 'Bootstrap preflight contract checker requires the VM host readiness helper'),
    ('require_file "$REPO_ROOT/scripts/check_vm_verifier_contract.py"', 'Bootstrap preflight contract checker requires the VM verifier contract checker'),
    ('require_file "$REPO_ROOT/scripts/vm/verify_bootstrap_in_vm.sh"', 'Bootstrap preflight contract checker requires the VM verifier script path'),
    ('bash -n "$INSTALLER"', 'Bootstrap preflight contract checker requires installer.sh syntax coverage'),
    ('bash -n "$STAGE_INSTALLER"', 'Bootstrap preflight contract checker requires little7-installer/install.sh syntax coverage'),
    ('bash "$STAGE_INSTALLER" verify', 'Bootstrap preflight contract checker requires little7-installer/install.sh verify coverage'),
    ('python3 -m py_compile "$REPO_ROOT/scripts/check_bootstrap_preflight_contract.py"', 'Bootstrap preflight contract checker requires self py_compile coverage'),
    ('python3 "$REPO_ROOT/scripts/check_bootstrap_preflight_contract.py"', 'Bootstrap preflight contract checker requires runtime coverage for itself'),
    ('python3 "$REPO_ROOT/scripts/check_bootstrap_workflow_contract_contract.py"', 'Bootstrap preflight contract checker requires runtime coverage for the workflow contract checker contract'),
    ('python3 "$REPO_ROOT/scripts/check_vm_verifier_contract.py"', 'Bootstrap preflight contract checker requires runtime coverage for the VM verifier contract checker'),
    ('bash "$REPO_ROOT/scripts/smoke_test_vm_verifier_github_fallback.sh"', 'Bootstrap preflight contract checker requires the verifier GitHub fallback smoke test'),
    ('bash "$REPO_ROOT/scripts/smoke_test_vm_verifier_red_path.sh"', 'Bootstrap preflight contract checker requires the verifier red-path smoke test'),
    ('for service in unifai-secretvault unifai-keyman unifai-supervisor unifai-openclaw; do', 'Bootstrap preflight contract checker requires the installer service-boundary loop'),
    ('require_grep "$service" "$INSTALLER"', 'Bootstrap preflight contract checker requires per-service installer grep assertions'),
    ('\'require_grep \\\'curl -fsSL https://openclaw.ai/install.sh \\\\| bash\\\' "$REPO_ROOT/little7-installer/stages/50_openclaw.sh"\'', 'Bootstrap preflight contract checker requires the Stage 50 OpenClaw installer grep'),
]

for needle, message in required:
    if needle not in text:
        fail(message)
    ok(message)

print('[PASS] Bootstrap preflight contract checker contract looks sane')
