#!/usr/bin/env bash
# UnifAI Git Hooks Setup
# Installs hard enforcement pre-commit hooks

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
HOOKS_DIR="$REPO_ROOT/.git/hooks"
PRE_COMMIT_HOOK="$HOOKS_DIR/pre-commit"

echo "[INFO] Installing UnifAI pre-commit hooks..."

cat << 'HOOK' > "$PRE_COMMIT_HOOK"
#!/usr/bin/env bash
# UnifAI Pre-commit Hook (Hard Enforcement)
set -euo pipefail

echo "=== UnifAI Rule 0 Pre-commit Audit ==="

# 1. Anti-Leakage Scan
echo "[1/2] Scanning staged files for hardcoded secrets..."
if git diff --cached -S"sk-ant-" --name-only | grep -q .; then
  echo "[FATAL] Hardcoded Anthropic API Key (sk-ant-) detected in staged files!"
  echo "Regra 0 Violada: Segredos NUNCA devem ir para o disco ou código!"
  exit 1
fi
echo "[PASS] No hardcoded secrets found."

# 2. Smoke Test Execution
echo "[2/2] Running World Physics Injection Smoke Test..."
# Note: Ensure the smoke test is executable and paths are correct
SMOKE_TEST_SCRIPT="$(pwd)/scripts/smoke_test_openclaw_injection.sh"
if [ -x "$SMOKE_TEST_SCRIPT" ]; then
  if ! bash "$SMOKE_TEST_SCRIPT" > /dev/null 2>&1; then
    echo "[FATAL] Smoke test failed! Pipeline de injeção comprometido."
    echo "Rode scripts/smoke_test_openclaw_injection.sh localmente para debugar."
    exit 1
  fi
  echo "[PASS] Smoke test passed."
else
  echo "[WARN] Smoke test script not found or not executable. Skipping."
fi

echo "=== Audit Passed. Safe to commit. ==="
HOOK

chmod +x "$PRE_COMMIT_HOOK"
echo "[SUCCESS] Pre-commit hook installed at $PRE_COMMIT_HOOK"
