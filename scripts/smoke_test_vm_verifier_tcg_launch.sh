#!/usr/bin/env bash
set -euo pipefail

echo "=== UnifAI Smoke Test: VM verifier TCG launch path stays portable ==="

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VERIFY_SCRIPT="$REPO_ROOT/scripts/vm/verify_bootstrap_in_vm.sh"
REAL_BASH="$(command -v bash)"
TMP_DIR="$(mktemp -d -t unifai-vm-tcg-XXXXXX)"
trap 'rm -rf "$TMP_DIR"' EXIT

BIN_DIR="$TMP_DIR/bin"
WORK_DIR="$TMP_DIR/work"
mkdir -p "$BIN_DIR" "$WORK_DIR"

cat > "$BIN_DIR/curl" <<'EOF'
#!/usr/bin/env bash
case "$*" in
  *"/commits/"*"/check-runs"*)
    printf '{"check_runs":[{"name":"Bootstrap Installer Preflight","conclusion":"success"}]}
'
    ;;
  *"/commits/"*)
    printf '{"sha":"deadbeefdeadbeefdeadbeefdeadbeefdeadbeef"}
'
    ;;
  *"cloud-images.ubuntu.com"*)
    out=""
    while [ "$#" -gt 0 ]; do
      case "$1" in
        -o)
          out="$2"
          shift 2
          ;;
        *)
          shift
          ;;
      esac
    done
    : > "$out"
    ;;
  *)
    printf 'unexpected curl args: %s\n' "$*" >&2
    exit 1
    ;;
esac
EOF

cat > "$BIN_DIR/jq" <<'EOF'
#!/usr/bin/env python3
import json
import sys

args = sys.argv[1:]
raw = False
while args and args[0].startswith('-'):
    if args[0] == '-r':
        raw = True
        args = args[1:]
    elif args[0] == '--arg':
        args = args[3:]
    else:
        print(f"unsupported jq args: {' '.join(sys.argv[1:])}", file=sys.stderr)
        sys.exit(1)

if not args:
    print("missing jq filter", file=sys.stderr)
    sys.exit(1)

expr = args[0]
payload = json.load(sys.stdin)

if expr == '.sha':
    value = payload.get('sha')
elif '.check_runs[]?' in expr and '.conclusion' in expr:
    value = 'success'
elif '.check_runs[]?' in expr and '.status' in expr:
    value = 'completed'
else:
    print(f"unsupported jq filter: {expr}", file=sys.stderr)
    sys.exit(1)

if value is None:
    sys.exit(0)

if raw:
    print(value)
else:
    json.dump(value, sys.stdout)
    print()
EOF

cat > "$BIN_DIR/qemu-img" <<'EOF'
#!/usr/bin/env bash
args=("$@")
count="${#args[@]}"
if [ "$count" -lt 2 ]; then
  exit 1
fi
touch "${args[$((count-2))]}"
EOF

cat > "$BIN_DIR/cloud-localds" <<'EOF'
#!/usr/bin/env bash
touch "$1"
EOF

cat > "$BIN_DIR/ssh-keygen" <<'EOF'
#!/usr/bin/env bash
out=""
while [ "$#" -gt 0 ]; do
  case "$1" in
    -f)
      out="$2"
      shift 2
      ;;
    *)
      shift
      ;;
  esac
done
printf 'dummy-private-key\n' > "$out"
printf 'ssh-ed25519 AAAATESTKEY smoke@test\n' > "$out.pub"
EOF

cat > "$BIN_DIR/ssh" <<'EOF'
#!/usr/bin/env bash
if printf '%s\n' "$*" | grep -q 'echo ssh-ready'; then
  exit 0
fi
cat >/dev/null || true
exit 0
EOF

cat > "$BIN_DIR/qemu-system-x86_64" <<'EOF'
#!/usr/bin/env bash
printf '%s\n' "$@" > "$QEMU_ARGS_LOG"
trap 'exit 0' TERM INT
sleep 30 &
wait $!
EOF

cat > "$BIN_DIR/timeout" <<'EOF'
#!/usr/bin/env bash
shift
exec "$@"
EOF

chmod +x "$BIN_DIR"/*

STATUS=0
OUTPUT="$(PATH="$BIN_DIR:/usr/bin:/bin" \
  UNIFAI_VM_VERIFY_FORCE_NO_GH=1 \
  UNIFAI_VM_VERIFY_FORCE_TCG=1 \
  QEMU_ARGS_LOG="$TMP_DIR/qemu-args.log" \
  WORK_DIR="$WORK_DIR" \
  "$REAL_BASH" "$VERIFY_SCRIPT" main 2>&1)" || STATUS=$?
printf '%s\n' "$OUTPUT"

if [ "$STATUS" -ne 0 ]; then
  echo "[FAIL] Verifier unexpectedly failed in forced-TCG smoke path."
  exit 1
fi

if ! grep -q 'UNIFAI_VM_VERIFY_FORCE_TCG=1; forcing TCG emulation' <<<"$OUTPUT"; then
  echo "[FAIL] Expected forced TCG message missing."
  exit 1
fi

if ! [ -f "$WORK_DIR/qemu.log" ]; then
  echo "[FAIL] Expected qemu.log artifact missing."
  exit 1
fi

if ! grep -qx -- '-cpu' "$TMP_DIR/qemu-args.log"; then
  echo "[FAIL] Expected qemu invocation to include -cpu."
  exit 1
fi

if ! grep -qx -- 'max' "$TMP_DIR/qemu-args.log"; then
  echo "[FAIL] Expected qemu invocation to use portable cpu=max in TCG mode."
  exit 1
fi

if grep -qx -- '-enable-kvm' "$TMP_DIR/qemu-args.log"; then
  echo "[FAIL] qemu invocation should not enable KVM in forced TCG mode."
  exit 1
fi

echo "[PASS] Verifier forced-TCG launch path stayed portable."
