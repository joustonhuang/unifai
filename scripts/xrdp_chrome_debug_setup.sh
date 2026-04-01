#!/usr/bin/env bash
set -euo pipefail

BILL_PROXY_PORT="${BILL_PROXY_PORT:-7701}"
CHROME_DEBUG_PORT="${CHROME_DEBUG_PORT:-9222}"
CHROME_DEBUG_ADDR="${CHROME_DEBUG_ADDR:-127.0.0.1}"
UNIFAI_BUDGET_FILE="${UNIFAI_BUDGET_FILE:-/tmp/unifai_budget.json}"
UNIFAI_CAGE_LOG_PATH="${UNIFAI_CAGE_LOG_PATH:-/tmp/unifai_xrdp_cage.log}"
UNIFAI_CAGE_POLL_SECONDS="${UNIFAI_CAGE_POLL_SECONDS:-2}"
UNIFAI_XRDP_CAGE_SKIP_INSTALL="${UNIFAI_XRDP_CAGE_SKIP_INSTALL:-0}"

UNIFAI_CHROME_USER_DATA_DIR="${UNIFAI_CHROME_USER_DATA_DIR:-$HOME/.config/google-chrome-remote}"
UNIFAI_CHROME_LOG_PATH="${UNIFAI_CHROME_LOG_PATH:-/tmp/chrome-remote.log}"
UNIFAI_CHROME_PID_FILE="${UNIFAI_CHROME_PID_FILE:-/tmp/unifai_chrome_remote.pid}"
UNIFAI_CAGE_WATCHDOG_PID_FILE="${UNIFAI_CAGE_WATCHDOG_PID_FILE:-/tmp/unifai_xrdp_cage_watchdog.pid}"

log_cage() {
  local msg="$1"
  printf '[%s] %s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "$msg" | tee -a "$UNIFAI_CAGE_LOG_PATH" >/dev/null
}

resolve_chrome_bin() {
  if [ -n "${UNIFAI_CHROME_BIN:-}" ]; then
    if [ ! -x "$UNIFAI_CHROME_BIN" ]; then
      echo "[FAIL] UNIFAI_CHROME_BIN is not executable: $UNIFAI_CHROME_BIN" >&2
      exit 1
    fi
    echo "$UNIFAI_CHROME_BIN"
    return
  fi

  if [ -x "/opt/google/chrome/chrome" ]; then
    echo "/opt/google/chrome/chrome"
    return
  fi

  if command -v google-chrome >/dev/null 2>&1; then
    command -v google-chrome
    return
  fi

  if command -v chromium-browser >/dev/null 2>&1; then
    command -v chromium-browser
    return
  fi

  if command -v chromium >/dev/null 2>&1; then
    command -v chromium
    return
  fi

  echo "[FAIL] Chrome binary not found. Install google-chrome or set UNIFAI_CHROME_BIN." >&2
  exit 1
}

setup_xrdp_stack() {
  if [ "$UNIFAI_XRDP_CAGE_SKIP_INSTALL" = "1" ]; then
    log_cage "xrdp_setup=skipped reason=test_mode"
    return
  fi

  sudo apt update
  sudo apt install -y xrdp xorgxrdp xfce4 xfce4-goodies policykit-1 ufw curl gnupg

  sudo systemctl enable xrdp xrdp-sesman

  cat > "$HOME/.xsession" <<'EOF'
startxfce4
EOF
  chmod +x "$HOME/.xsession"
  rm -f "$HOME/.Xauthority" "$HOME/.xsession-errors"

  if ! command -v google-chrome >/dev/null 2>&1 && [ ! -x "/opt/google/chrome/chrome" ]; then
    curl -fsSL https://dl.google.com/linux/linux_signing_key.pub | sudo gpg --dearmor -o /usr/share/keyrings/google-chrome.gpg
    echo 'deb [arch=amd64 signed-by=/usr/share/keyrings/google-chrome.gpg] http://dl.google.com/linux/chrome/deb/ stable main' | \
      sudo tee /etc/apt/sources.list.d/google-chrome.list >/dev/null
    sudo apt update
    sudo apt install -y google-chrome-stable
  fi

  sudo ufw allow OpenSSH || true
  sudo systemctl restart xrdp-sesman xrdp
}

read_budget_value() {
  python3 - "$UNIFAI_BUDGET_FILE" <<'PY'
import json
import sys

path = sys.argv[1]
try:
    with open(path, "r", encoding="utf-8") as handle:
        payload = json.load(handle)
    print(int(payload.get("budget", 0)))
except Exception:
    print(0)
PY
}

probe_bill_proxy_status() {
  curl -s -o /dev/null -w "%{http_code}" \
    -X POST "http://127.0.0.1:${BILL_PROXY_PORT}/v1/messages" \
    -H "x-api-key: cage-probe" \
    -H "anthropic-version: 2023-06-01" \
    -H "content-type: application/json" \
    -d '{"model":"claude-3-haiku","max_tokens":1,"messages":[{"role":"user","content":"cage-probe"}]}' || true
}

terminate_chrome_process() {
  local chrome_pid="$1"

  kill "$chrome_pid" >/dev/null 2>&1 || true
  sleep 1
  kill -9 "$chrome_pid" >/dev/null 2>&1 || true
}

watch_fuel_and_cut_browser() {
  local chrome_pid="$1"

  while kill -0 "$chrome_pid" >/dev/null 2>&1; do
    local budget
    budget="$(read_budget_value)"

    if [ "$budget" -le 0 ]; then
      local status
      status="$(probe_bill_proxy_status)"
      log_cage "fuel_probe budget=${budget} status=${status}"

      if [ "$status" = "429" ]; then
        log_cage "fuel_cut status=429 action=kill chrome_pid=${chrome_pid}"
        terminate_chrome_process "$chrome_pid"
        return 0
      fi
    fi

    sleep "$UNIFAI_CAGE_POLL_SECONDS"
  done
}

main() {
  local chrome_bin

  setup_xrdp_stack
  chrome_bin="$(resolve_chrome_bin)"

  pgrep -f "remote-debugging-port=${CHROME_DEBUG_PORT}" >/dev/null 2>&1 && \
    pkill -f "remote-debugging-port=${CHROME_DEBUG_PORT}" || true

  rm -rf "$UNIFAI_CHROME_USER_DATA_DIR/Singleton"* || true
  mkdir -p "$UNIFAI_CHROME_USER_DATA_DIR"

  nohup "$chrome_bin" \
    --remote-debugging-address="$CHROME_DEBUG_ADDR" \
    --remote-debugging-port="$CHROME_DEBUG_PORT" \
    --user-data-dir="$UNIFAI_CHROME_USER_DATA_DIR" \
    --proxy-server="http://127.0.0.1:${BILL_PROXY_PORT}" \
    --proxy-bypass-list="<-loopback>" \
    --no-first-run \
    --no-default-browser-check \
    >"$UNIFAI_CHROME_LOG_PATH" 2>&1 &

  local chrome_pid=$!
  echo "$chrome_pid" > "$UNIFAI_CHROME_PID_FILE"
  log_cage "chrome_started pid=${chrome_pid} bill_proxy_port=${BILL_PROXY_PORT} debug_port=${CHROME_DEBUG_PORT}"

  watch_fuel_and_cut_browser "$chrome_pid" &
  local watchdog_pid=$!
  echo "$watchdog_pid" > "$UNIFAI_CAGE_WATCHDOG_PID_FILE"
  log_cage "watchdog_started pid=${watchdog_pid}"

  cat <<EOF
Faraday cage active.
XRDP stack ready: $( [ "$UNIFAI_XRDP_CAGE_SKIP_INSTALL" = "1" ] && echo "skipped (test mode)" || echo "installed" )
Chrome PID: ${chrome_pid}
Cage watchdog PID: ${watchdog_pid}
Bill Proxy URL: http://127.0.0.1:${BILL_PROXY_PORT}
EOF
}

main "$@"
