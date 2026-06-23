#!/usr/bin/env bash
set -euo pipefail

echo "=== UnifAI Smoke Test: VM verifier kvm fallback guidance stays actionable ==="

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SOURCE_VERIFY_SCRIPT="$REPO_ROOT/scripts/vm/verify_bootstrap_in_vm.sh"
REAL_BASH="$(command -v bash)"
TMP_DIR="$(mktemp -d -t unifai-vm-kvm-fallback-XXXXXX)"
trap 'rm -rf "$TMP_DIR"' EXIT

BIN_DIR="$TMP_DIR/bin"
WORK_DIR="$TMP_DIR/work"
VERIFY_SCRIPT="$TMP_DIR/verify_bootstrap_in_vm.sh"
mkdir -p "$BIN_DIR" "$WORK_DIR"

python3 - <<'PY' "$SOURCE_VERIFY_SCRIPT" "$VERIFY_SCRIPT"
from pathlib import Path
import sys

src = Path(sys.argv[1]).read_text(encoding="utf-8")
src = src.replace('elif [ -w /dev/kvm ]; then', 'elif false; then', 1)
Path(sys.argv[2]).write_text(src, encoding="utf-8")
PY
chmod +x "$VERIFY_SCRIPT"

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
joined="$*"
if printf '%s\n' "$joined" | grep -q 'echo ssh-ready'; then
  exit 0
fi
if printf '%s\n' "$joined" | grep -q 'bash -s'; then
  cat >/dev/null || true
  exit 0
fi
cat >/dev/null || true
exit 0
EOF

cat > "$BIN_DIR/scp" <<'EOF'
#!/usr/bin/env bash
dest="${@: -1}"
printf '== fake vm report ==\n[PASS] synthetic report copy\n' > "$dest"
EOF

cat > "$BIN_DIR/qemu-system-x86_64" <<'EOF'
#!/usr/bin/env bash
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
  WORK_DIR="$WORK_DIR" \
  "$REAL_BASH" "$VERIFY_SCRIPT" main 2>&1)" || STATUS=$?
printf '%s\n' "$OUTPUT"

if [ "$STATUS" -ne 0 ]; then
  echo "[FAIL] Verifier unexpectedly failed in simulated /dev/kvm fallback path."
  exit 1
fi

if ! grep -q '/dev/kvm is not writable; falling back to TCG emulation' <<<"$OUTPUT"; then
  echo "[FAIL] Expected /dev/kvm fallback message missing."
  exit 1
fi

if ! grep -q 'Likely fix path: ensure the operator user can access /dev/kvm' <<<"$OUTPUT"; then
  echo "[FAIL] Expected actionable /dev/kvm recovery hint missing."
  exit 1
fi

echo "[PASS] Verifier /dev/kvm fallback guidance stayed actionable."
