#!/usr/bin/env bash
set -euo pipefail

REPO_SLUG="${REPO_SLUG:-joustonhuang/unifai}"
REF="${1:-main}"
VM_NAME="${VM_NAME:-unifai-bootstrap-check}"
if [ -n "${WORK_DIR:-}" ]; then
  WORK_DIR="$WORK_DIR"
elif [ -d /srv ] && [ -w /srv ]; then
  WORK_DIR="/srv/unifai-vm-checks/$VM_NAME"
else
  WORK_DIR="${XDG_CACHE_HOME:-$HOME/.cache}/unifai-vm-checks/$VM_NAME"
fi
IMAGE_URL="${IMAGE_URL:-https://cloud-images.ubuntu.com/jammy/current/jammy-server-cloudimg-amd64.img}"
SSH_PORT="${SSH_PORT:-22222}"
RAM_MB="${RAM_MB:-6144}"
VCPUS="${VCPUS:-2}"
DISK_GB="${DISK_GB:-40}"
SUPERVISOR_PORT="${SUPERVISOR_PORT:-5000}"
OPENCLAW_PORT="${OPENCLAW_PORT:-3000}"
REQUIRED_CHECKS=(
  "Bootstrap Installer Preflight"
)
REQUIRE_IF_PRESENT=(
  "Core Modules & Exoskeleton E2E"
  "smoke-test"
)

need_bin() {
  command -v "$1" >/dev/null 2>&1 || {
    echo "[FAIL] Missing required binary: $1" >&2
    exit 1
  }
}

for bin in gh jq curl qemu-system-x86_64 qemu-img cloud-localds ssh ssh-keygen timeout; do
  need_bin "$bin"
done

mkdir -p "$WORK_DIR"
cd "$WORK_DIR"

SHA="$(gh api "repos/$REPO_SLUG/commits/$REF" --jq '.sha')"
echo "Target ref: $REF"
echo "Resolved SHA: $SHA"

echo "Checking required GitHub checks before VM boot..."
checks_json="$(gh api "repos/$REPO_SLUG/commits/$SHA/check-runs")"
for check in "${REQUIRED_CHECKS[@]}"; do
  conclusion="$(printf '%s' "$checks_json" | jq -r --arg name "$check" '.check_runs[]? | select(.name == $name) | .conclusion' | tail -n1)"
  if [ "$conclusion" != "success" ]; then
    echo "[FAIL] Required check '$check' is not green for $SHA (got: ${conclusion:-missing})" >&2
    exit 1
  fi
  echo "[PASS] $check = success"
done
for check in "${REQUIRE_IF_PRESENT[@]}"; do
  status="$(printf '%s' "$checks_json" | jq -r --arg name "$check" '.check_runs[]? | select(.name == $name) | .status' | tail -n1)"
  if [ -z "$status" ]; then
    echo "[INFO] $check not present for $SHA, skipping"
    continue
  fi
  conclusion="$(printf '%s' "$checks_json" | jq -r --arg name "$check" '.check_runs[]? | select(.name == $name) | .conclusion' | tail -n1)"
  if [ "$conclusion" != "success" ]; then
    echo "[FAIL] Conditional required check '$check' is not green for $SHA (got: ${conclusion:-missing})" >&2
    exit 1
  fi
  echo "[PASS] $check = success"
done

BASE_IMG="$WORK_DIR/base.img"
VM_IMG="$WORK_DIR/${VM_NAME}.qcow2"
SEED_ISO="$WORK_DIR/seed.iso"
SSH_KEY="$WORK_DIR/id_ed25519"
CLOUD_INIT_USER_DATA="$WORK_DIR/user-data"
CLOUD_INIT_META_DATA="$WORK_DIR/meta-data"
SERIAL_LOG="$WORK_DIR/serial.log"
REPORT="$WORK_DIR/report.txt"

if [ ! -f "$BASE_IMG" ]; then
  curl -L "$IMAGE_URL" -o "$BASE_IMG"
fi

rm -f "$VM_IMG" "$SEED_ISO" "$SERIAL_LOG" "$REPORT"
qemu-img create -f qcow2 -b "$BASE_IMG" -F qcow2 "$VM_IMG" "${DISK_GB}G" >/dev/null

if [ ! -f "$SSH_KEY" ]; then
  ssh-keygen -t ed25519 -N '' -f "$SSH_KEY" >/dev/null
fi

PUBKEY="$(cat "$SSH_KEY.pub")"
cat > "$CLOUD_INIT_USER_DATA" <<EOF
#cloud-config
users:
  - name: unifai
    groups: [sudo]
    shell: /bin/bash
    sudo: ALL=(ALL) NOPASSWD:ALL
    ssh_authorized_keys:
      - $PUBKEY
package_update: true
packages:
  - git
  - curl
  - jq
  - ca-certificates
  - openssh-server
runcmd:
  - systemctl enable ssh
  - systemctl restart ssh
EOF

cat > "$CLOUD_INIT_META_DATA" <<EOF
instance-id: $VM_NAME
local-hostname: $VM_NAME
EOF

cloud-localds "$SEED_ISO" "$CLOUD_INIT_USER_DATA" "$CLOUD_INIT_META_DATA"

cleanup() {
  if [ -n "${QEMU_PID:-}" ] && kill -0 "$QEMU_PID" 2>/dev/null; then
    kill "$QEMU_PID" || true
    wait "$QEMU_PID" || true
  fi
}
trap cleanup EXIT

qemu-system-x86_64 \
  -enable-kvm \
  -m "$RAM_MB" \
  -smp "$VCPUS" \
  -cpu host \
  -name "$VM_NAME" \
  -nographic \
  -serial file:"$SERIAL_LOG" \
  -drive file="$VM_IMG",if=virtio \
  -drive file="$SEED_ISO",if=virtio,media=cdrom \
  -netdev user,id=net0,hostfwd=tcp::${SSH_PORT}-:22 \
  -device virtio-net-pci,netdev=net0 >/dev/null 2>&1 &
QEMU_PID=$!

echo "Started VM PID $QEMU_PID, waiting for SSH..."
SSH_READY=0
for _ in $(seq 1 90); do
  if ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -o ConnectTimeout=5 -i "$SSH_KEY" -p "$SSH_PORT" unifai@127.0.0.1 'echo ssh-ready' >/dev/null 2>&1; then
    echo "[PASS] SSH is ready"
    SSH_READY=1
    break
  fi
  sleep 5
done

if [ "$SSH_READY" -ne 1 ]; then
  echo "[FAIL] SSH never became ready; see $SERIAL_LOG" >&2
  exit 1
fi

ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -i "$SSH_KEY" -p "$SSH_PORT" unifai@127.0.0.1 "git clone https://github.com/$REPO_SLUG.git ~/unifai && cd ~/unifai && git checkout $SHA && sudo bash installer.sh" | tee "$WORK_DIR/installer-output.log"

ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -i "$SSH_KEY" -p "$SSH_PORT" unifai@127.0.0.1 'bash -s' <<'EOF'
set -e
OPENCLAW_PORT="${OPENCLAW_PORT:-3000}"
SUPERVISOR_PORT="${SUPERVISOR_PORT:-5000}"
FAILURES=0

mark_fail() {
  echo "[FAIL] $1"
  FAILURES=$((FAILURES + 1))
}

wait_for_service_active() {
  local service="$1"
  local retries="${2:-12}"
  local sleep_seconds="${3:-5}"
  for _ in $(seq 1 "$retries"); do
    if sudo systemctl is-active --quiet "$service"; then
      return 0
    fi
    sleep "$sleep_seconds"
  done
  return 1
}

wait_for_tcp_listener() {
  local port="$1"
  local retries="${2:-12}"
  local sleep_seconds="${3:-5}"
  for _ in $(seq 1 "$retries"); do
    if ss -lnt | awk '{print $4}' | grep -Eq "(^|:)${port}$"; then
      return 0
    fi
    sleep "$sleep_seconds"
  done
  return 1
}

if wait_for_service_active unifai-openclaw 18 5; then
  echo "[PASS] unifai-openclaw reached active state"
else
  mark_fail "unifai-openclaw never reached active state after installer run"
fi

if wait_for_tcp_listener "$OPENCLAW_PORT" 18 5; then
  echo "[PASS] OpenClaw port ${OPENCLAW_PORT} is listening"
else
  mark_fail "OpenClaw port ${OPENCLAW_PORT} never opened"
fi

{
  echo "== systemd service status =="
  sudo systemctl status unifai-secretvault --no-pager || true
  sudo systemctl status unifai-keyman --no-pager || true
  sudo systemctl status unifai-supervisor --no-pager || true
  sudo systemctl status unifai-openclaw --no-pager || true
  echo
  echo "== active check =="
  for svc in unifai-secretvault unifai-keyman unifai-supervisor unifai-openclaw; do
    if sudo systemctl is-active --quiet "$svc"; then
      echo "[PASS] $svc active"
    else
      mark_fail "$svc inactive"
    fi
  done
  echo
  echo "== endpoint probe =="
  if curl -fsS "http://127.0.0.1:${SUPERVISOR_PORT}/health"; then
    echo
    echo "[PASS] Supervisor health probe responded"
  else
    mark_fail "Supervisor health probe unavailable on port ${SUPERVISOR_PORT}"
  fi
  if curl -fsS -o /tmp/openclaw-home.html "http://127.0.0.1:${OPENCLAW_PORT}/"; then
    echo "[PASS] OpenClaw HTTP probe responded on port ${OPENCLAW_PORT}"
    head -n 20 /tmp/openclaw-home.html || true
  else
    mark_fail "OpenClaw HTTP probe unavailable on port ${OPENCLAW_PORT}"
  fi
  echo
  echo "== socket evidence =="
  ss -lntp | grep -E ":(${SUPERVISOR_PORT}|${OPENCLAW_PORT})\\b" || true
  echo
  echo "== openclaw logs (last 5 minutes) =="
  sudo journalctl -u unifai-openclaw --since "5 minutes ago" --no-pager || true
  echo
  echo "== secret leakage smoke =="
  cd ~/unifai
  if python3 scripts/smoke_test_secret_leakage.py; then
    echo "[PASS] Secret leakage smoke succeeded inside VM"
  else
    mark_fail "Secret leakage smoke failed inside VM"
  fi
  echo
  if [ "$FAILURES" -ne 0 ]; then
    echo "[FAIL] VM verification found ${FAILURES} failing checks"
    exit 1
  fi
  echo "[PASS] VM verification checks passed"
} | tee ~/vm-bootstrap-report.txt
EOF

scp -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -i "$SSH_KEY" -P "$SSH_PORT" unifai@127.0.0.1:~/vm-bootstrap-report.txt "$REPORT" >/dev/null

echo "VM verification complete. Evidence bundle: $WORK_DIR"
