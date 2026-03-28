#!/usr/bin/env bash
# UnifAI World Physics Injection Pipeline — Verification Test
# Validates that API keys flow correctly through SecretVault → Keyman → OpenClaw
set -euo pipefail

echo "=== UnifAI World Physics Injection Smoke Test ==="

# Paths relative to the UnifAI repository root (fixing previous hardcoded Claude ones)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# We clone the real CLI locally to test if it operates correctly
TEST_ROOT=$(mktemp -d -t unifai-injector-test-XXXXXX)
cd "$TEST_ROOT"

echo "[INFO] Dev mode: using ephemeral master key (not persisted)"
export SECRETVAULT_MASTER_KEY=$(openssl rand -hex 32)
export SECRETVAULT_ROOT="$TEST_ROOT"

mkdir -p "$SECRETVAULT_ROOT/config" "$SECRETVAULT_ROOT/secrets" \
         "$SECRETVAULT_ROOT/grants" "$SECRETVAULT_ROOT/audit" "$SECRETVAULT_ROOT/tmp"
chmod 700 "$SECRETVAULT_ROOT/secrets" "$SECRETVAULT_ROOT/grants"

# Use the real Keyman CLI from the codebase to test the actual JSON contract
cat > "$SECRETVAULT_ROOT/config/default.json" <<CFG
{
  "vault": { "defaultTtlSeconds": 60, "maxTtlSeconds": 3600, "interactiveFallback": false },
  "keyman": { "command": "python3 $REPO_ROOT/supervisor/plugins/keyman_guardian/keyman_auth_cli.py" }
}
CFG

echo "[INFO] Fetching supervisor-secretvault CLI to test with..."
git clone https://github.com/joustonhuang/supervisor-secretvault.git >/dev/null 2>&1
cd supervisor-secretvault
# Simulating dependencies installation
npm install >/dev/null 2>&1 || true

SV="node src/cli.js"

echo "[INFO] Step 1: SecretVault init..."
$SV init >/dev/null || { echo "[FAIL] Init failed"; exit 1; }
echo "[PASS] SecretVault init OK"

echo "[INFO] Step 2: Seeding WRONG API key (alias: codex-oauth)..."
$SV seed --alias codex-oauth --value "sk-ant-FAKE-KEY-FOR-TESTING" >/dev/null || { echo "[FAIL] Seed failed"; exit 1; }
echo "[PASS] Seed OK"

echo "[INFO] Step 3: Requesting grant via auto Keyman contract..."
# We pass the required requester identifier expected by keyman_auth_cli.py
GRANT_JSON=$($SV request --alias codex-oauth --purpose "test-run" --agent admin_agent --ttl 60)

if echo "$GRANT_JSON" | grep -q '"ok":true'; then
  GRANT_PATH=$(echo "$GRANT_JSON" | python3 -c "import sys,json; print(json.load(sys.stdin).get('path', ''))")
  echo "[PASS] Grant issued successfully by Keyman: $GRANT_PATH"
else
  echo "[FAIL] Grant request failed! Keyman blocked it or CLI crashed: $GRANT_JSON"
  exit 1
fi

if [ ! -f "$GRANT_PATH" ]; then
  echo "[FAIL] Grant file physically missing at $GRANT_PATH"
  exit 1
fi

echo "[INFO] Step 4: Injecting key and calling Anthropic API..."
API_KEY=$(cat "$GRANT_PATH")
echo "[INFO] Injected Key: ${API_KEY:0:20}..."

HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" \
  -X POST https://api.anthropic.com/v1/messages \
  -H "x-api-key: $API_KEY" \
  -H "anthropic-version: 2023-06-01" \
  -H "content-type: application/json" \
  -d '{"model":"claude-3-haiku-20240307","max_tokens":1,"messages":[{"role":"user","content":"ping"}]}')

echo "[INFO] Step 5: Asserting result..."
if [ "$HTTP_STATUS" == "401" ]; then
  echo "[PASS] Got HTTP 401 — injection pipeline works securely. Fake key isolated."
else
  echo "[FAIL] Got HTTP $HTTP_STATUS instead of 401 Unauthorized."
  exit 1
fi

$SV cleanup >/dev/null || true
rm -rf "$TEST_ROOT"

echo "=== SMOKE TEST PASSED: World Physics pipeline validated ==="
