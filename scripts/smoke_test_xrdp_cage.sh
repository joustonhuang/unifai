#!/usr/bin/env bash
# UnifAI XRDP Faraday Cage Smoke Test
# Proves that an empty fuel tank triggers Bill Proxy HTTP 429 and kills the browser process.

set -euo pipefail

echo "=== UnifAI XRDP Faraday Cage Smoke Test ==="

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

BILL_PROXY="$REPO_ROOT/supervisor/plugins/bill_guardian/bill_proxy.py"
XRDP_CAGE_SCRIPT="$REPO_ROOT/scripts/xrdp_chrome_debug_setup.sh"
STATE_FILE="/tmp/unifai_budget.json"

BILL_PROXY_PORT="${BILL_PROXY_PORT:-7711}"
BILL_PROXY_URL="http://127.0.0.1:${BILL_PROXY_PORT}"

TEST_ROOT="$(mktemp -d -t unifai-xrdp-cage-XXXXXX)"
FAKE_CHROME="$TEST_ROOT/fake-chrome.sh"
CAGE_LOG="$TEST_ROOT/cage.log"
CHROME_LOG="$TEST_ROOT/chrome.log"
CHROME_PID_FILE="$TEST_ROOT/chrome.pid"
WATCHDOG_PID_FILE="$TEST_ROOT/watchdog.pid"

PROXY_PID=""

cleanup() {
  if [ -f "$WATCHDOG_PID_FILE" ]; then
    kill "$(cat "$WATCHDOG_PID_FILE")" >/dev/null 2>&1 || true
  fi

  if [ -f "$CHROME_PID_FILE" ]; then
    kill "$(cat "$CHROME_PID_FILE")" >/dev/null 2>&1 || true
    kill -9 "$(cat "$CHROME_PID_FILE")" >/dev/null 2>&1 || true
  fi

  if [ -n "$PROXY_PID" ]; then
    kill "$PROXY_PID" >/dev/null 2>&1 || true
    kill -9 "$PROXY_PID" >/dev/null 2>&1 || true
  fi

  pkill -f "bill_proxy.py" >/dev/null 2>&1 || true
  rm -rf "$TEST_ROOT"
}

trap cleanup EXIT

if [ ! -x "$XRDP_CAGE_SCRIPT" ]; then
  echo "[FAIL] XRDP cage script missing or not executable: $XRDP_CAGE_SCRIPT"
  exit 1
fi

cat > "$FAKE_CHROME" <<'FAKE'
#!/usr/bin/env bash
set -euo pipefail
trap 'exit 0' TERM INT
while true; do
  sleep 1
done
FAKE
chmod +x "$FAKE_CHROME"

pkill -f "bill_proxy.py" >/dev/null 2>&1 || true

echo '{"budget": 0, "key_status": "VALID"}' > "$STATE_FILE"

echo "[INFO] Starting Bill Proxy on port ${BILL_PROXY_PORT}..."
BILL_PROXY_PORT="$BILL_PROXY_PORT" UNIFAI_PROXY_TEST_MODE=1 python3 "$BILL_PROXY" &
PROXY_PID=$!
sleep 2

echo "[INFO] Validating Bill Proxy returns 429 with empty budget..."
HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" \
  -X POST "${BILL_PROXY_URL}/v1/messages" \
  -H "x-api-key: smoke-xrdp-cage" \
  -H "anthropic-version: 2023-06-01" \
  -H "content-type: application/json" \
  -d '{"model":"claude-3-haiku","max_tokens":1,"messages":[{"role":"user","content":"ping"}]}')

if [ "$HTTP_STATUS" != "429" ]; then
  echo "[FAIL] Expected proxy status 429 with empty budget, got $HTTP_STATUS"
  exit 1
fi
echo "[PASS] Bill Proxy 429 throttle confirmed."

echo "[INFO] Launching XRDP Faraday cage with fake Chrome process..."
UNIFAI_XRDP_CAGE_SKIP_INSTALL=1 \
UNIFAI_CHROME_BIN="$FAKE_CHROME" \
UNIFAI_CHROME_USER_DATA_DIR="$TEST_ROOT/profile" \
UNIFAI_CHROME_LOG_PATH="$CHROME_LOG" \
UNIFAI_CAGE_LOG_PATH="$CAGE_LOG" \
UNIFAI_CHROME_PID_FILE="$CHROME_PID_FILE" \
UNIFAI_CAGE_WATCHDOG_PID_FILE="$WATCHDOG_PID_FILE" \
UNIFAI_CAGE_POLL_SECONDS=1 \
UNIFAI_BUDGET_FILE="$STATE_FILE" \
BILL_PROXY_PORT="$BILL_PROXY_PORT" \
"$XRDP_CAGE_SCRIPT"

for _ in $(seq 1 10); do
  if [ -f "$CHROME_PID_FILE" ]; then
    break
  fi
  sleep 1
done

if [ ! -f "$CHROME_PID_FILE" ]; then
  echo "[FAIL] Cage did not produce Chrome PID file."
  exit 1
fi

CHROME_PID="$(cat "$CHROME_PID_FILE")"
if [ -z "$CHROME_PID" ]; then
  echo "[FAIL] Chrome PID file is empty."
  exit 1
fi

echo "[INFO] Waiting watchdog kill after 429..."
for _ in $(seq 1 12); do
  if ! kill -0 "$CHROME_PID" >/dev/null 2>&1; then
    break
  fi
  sleep 1
done

if kill -0 "$CHROME_PID" >/dev/null 2>&1; then
  echo "[FAIL] Chrome process still alive after expected 429 cut (pid=$CHROME_PID)."
  exit 1
fi
echo "[PASS] Chrome process terminated by cage watchdog."

if [ ! -f "$CAGE_LOG" ]; then
  echo "[FAIL] Cage log missing at $CAGE_LOG"
  exit 1
fi

if grep -q "fuel_probe .*status=429" "$CAGE_LOG" && grep -q "fuel_cut status=429 action=kill" "$CAGE_LOG"; then
  echo "[PASS] Cage audit confirms 429 observation and kill action."
else
  echo "[FAIL] Cage log missing 429->kill trace."
  cat "$CAGE_LOG"
  exit 1
fi

echo "=== SMOKE TEST PASSED: XRDP cage enforces 429 -> browser kill ==="
