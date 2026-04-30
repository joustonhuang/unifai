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
QEMU_ACCEL="${QEMU_ACCEL:-auto}"
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
QEMU_LOG="$WORK_DIR/qemu.log"
REPORT="$WORK_DIR/report.txt"

resolve_qemu_accel() {
  case "$QEMU_ACCEL" in
    auto)
      if [ -r /dev/kvm ] && [ -w /dev/kvm ]; then
        echo kvm
      else
        echo tcg
      fi
      ;;
    kvm|tcg)
      echo "$QEMU_ACCEL"
      ;;
    *)
      echo "[FAIL] Unsupported QEMU_ACCEL: $QEMU_ACCEL (expected auto|kvm|tcg)" >&2
      exit 1
      ;;
  esac
}

ACCEL_MODE="$(resolve_qemu_accel)"
echo "QEMU accel mode: $ACCEL_MODE"
if [ "$ACCEL_MODE" = "tcg" ]; then
  echo "[INFO] /dev/kvm is not accessible; falling back to software emulation (slower)."
fi

if [ ! -f "$BASE_IMG" ]; then
  curl -L "$IMAGE_URL" -o "$BASE_IMG"
fi

rm -f "$VM_IMG" "$SEED_ISO" "$SERIAL_LOG" "$QEMU_LOG" "$REPORT"
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

QEMU_ARGS=(
  -m "$RAM_MB"
  -smp "$VCPUS"
  -name "$VM_NAME"
  -nographic
  -serial "file:$SERIAL_LOG"
  -drive "file=$VM_IMG,if=virtio"
  -drive "file=$SEED_ISO,if=virtio,media=cdrom"
  -netdev "user,id=net0,hostfwd=tcp::${SSH_PORT}-:22"
  -device virtio-net-pci,netdev=net0
)

if [ "$ACCEL_MODE" = "kvm" ]; then
  QEMU_ARGS=(-enable-kvm -cpu host "${QEMU_ARGS[@]}")
else
  QEMU_ARGS=(-accel tcg,thread=multi -cpu max "${QEMU_ARGS[@]}")
fi

qemu-system-x86_64 \
  "${QEMU_ARGS[@]}" \
  >"$QEMU_LOG" 2>&1 &
QEMU_PID=$!

echo "Started VM PID $QEMU_PID, waiting for SSH..."
SSH_READY=0
for _ in $(seq 1 90); do
  if ! kill -0 "$QEMU_PID" 2>/dev/null; then
    echo "[FAIL] QEMU exited before SSH became ready; see $QEMU_LOG and $SERIAL_LOG" >&2
    exit 1
  fi
  if ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -o ConnectTimeout=5 -i "$SSH_KEY" -p "$SSH_PORT" unifai@127.0.0.1 'echo ssh-ready' >/dev/null 2>&1; then
    echo "[PASS] SSH is ready"
    SSH_READY=1
    break
  fi
  sleep 5
done

if [ "$SSH_READY" -ne 1 ]; then
  echo "[FAIL] SSH never became ready; see $QEMU_LOG and $SERIAL_LOG" >&2
  exit 1
fi

echo "Waiting for cloud-init to finish before starting installer..."
ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -i "$SSH_KEY" -p "$SSH_PORT" unifai@127.0.0.1 '
  if command -v cloud-init >/dev/null 2>&1; then
    sudo cloud-init status --wait
  else
    echo "[INFO] cloud-init not present; skipping wait"
  fi
'

ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -i "$SSH_KEY" -p "$SSH_PORT" unifai@127.0.0.1 "git clone https://github.com/$REPO_SLUG.git ~/unifai && cd ~/unifai && git checkout $SHA && sudo bash installer.sh" | tee "$WORK_DIR/installer-output.log"

ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -i "$SSH_KEY" -p "$SSH_PORT" unifai@127.0.0.1 'bash -s' <<'EOF'
set -e
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
      echo "[FAIL] $svc inactive"
    fi
  done
  echo
  echo "== endpoint probe =="
  curl -fsS http://127.0.0.1:5000/health || echo "Supervisor health probe unavailable"
} | tee ~/vm-bootstrap-report.txt
EOF

scp -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -i "$SSH_KEY" -P "$SSH_PORT" unifai@127.0.0.1:~/vm-bootstrap-report.txt "$REPORT" >/dev/null

echo "VM verification complete. Evidence bundle: $WORK_DIR"
