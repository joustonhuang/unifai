#!/usr/bin/env bash
set -euo pipefail

echo "=== UnifAI Smoke Test: VM verifier fails closed when report copy-back is missing ==="

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VERIFY_SCRIPT="$REPO_ROOT/scripts/vm/verify_bootstrap_in_vm.sh"
REAL_BASH="$(command -v bash)"
TMP_DIR="$(mktemp -d -t unifai-vm-missing-report-XXXXXX)"
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
        -o) out="$2"; shift 2 ;;
        *) shift ;;
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
    sys.exit(1)

if value is None:
    sys.exit(0)
print(value if raw else json.dumps(value))
EOF

cat > "$BIN_DIR/qemu-img" <<'EOF'
#!/usr/bin/env bash
args=("$@")
count="${#args[@]}"
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
    -f) out="$2"; shift 2 ;;
    *) shift ;;
  esac
done
printf 'dummy-private-key\n' > "$out"
printf 'ssh-ed25519 AAAATESTKEY smoke@test\n' > "$out.pub"
EOF

cat > "$BIN_DIR/ssh" <<'EOF'
#!/usr/bin/env bash
joined="$*"
if grep -Fq 'echo ssh-ready' <<<"$joined"; then
  exit 0
fi
if grep -Fq 'installer.sh' <<<"$joined"; then
  printf 'fake installer output line\n'
  exit 0
fi
if grep -Fq 'bash -s' <<<"$joined"; then
  cat >/dev/null || true
  exit 0
fi
exit 0
EOF

cat > "$BIN_DIR/scp" <<'EOF'
#!/usr/bin/env bash
exit 1
EOF

cat > "$BIN_DIR/qemu-system-x86_64" <<'EOF'
#!/usr/bin/env bash
serial_path=""
while [ "$#" -gt 0 ]; do
  case "$1" in
    -serial) serial_path="$2"; shift 2 ;;
    *) shift ;;
  esac
done
serial_path="${serial_path#file:}"
printf 'fake serial for missing report\n' > "$serial_path"
printf 'fake qemu for missing report\n' >&2
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
  WORK_DIR="$WORK_DIR" \
  "$REAL_BASH" "$VERIFY_SCRIPT" main 2>&1)" || STATUS=$?
printf '%s\n' "$OUTPUT"

if [ "$STATUS" -eq 0 ]; then
  echo "[FAIL] Verifier unexpectedly succeeded when report copy-back was missing."
  exit 1
fi

for needle in \
  '[FAIL] VM verification passed remotely but the report could not be copied back; evidence bundle:' \
  '[INFO] installer output tail (' \
  'fake installer output line' \
  '[INFO] vm report missing:' \
  '[INFO] serial log tail (' \
  'fake serial for missing report' \
  '[INFO] qemu log tail (' \
  'fake qemu for missing report'
do
  if ! grep -Fq "$needle" <<<"$OUTPUT"; then
    echo "[FAIL] Expected missing-report fail-closed output missing: $needle"
    exit 1
  fi
done

echo "[PASS] Verifier fails closed when report copy-back is missing after a green remote run."
