# World Physics Injection Pipeline — Verification Guide

**Version:** v0.1
**Date:** 2026-03-27

Validates that API keys flow correctly through SecretVault → Keyman → OpenClaw.
Run this in WSL shell. Takes about 2 minutes.

---

## Prerequisites

```bash
node --version   # must be 22+
openssl version  # must exist
curl --version   # must exist
```

---

## Run the Smoke Test

```bash
cd /mnt/d/Claude/unifai
bash scripts/smoke_test_openclaw_injection.sh
```

### What you will see

```
[INFO] Dev mode: using ephemeral master key (not persisted)
[INFO] Step 1: SecretVault init...
[PASS] SecretVault init OK
[INFO] Step 2: Seeding WRONG API key (alias: codex-oauth-smoketest)...
[PASS] Seed OK (alias=codex-oauth-smoketest)
[INFO] Step 3: Requesting grant (you will be prompted to approve)...
[INFO]   → Type 'y' to approve the grant request
```

**At the prompt, type `y` and press Enter.**

```
[PASS] Grant issued: /tmp/tmp.xxxxxxxx/grants/uuid.secret
[INFO] Step 4: Injecting key and calling Anthropic API...
[INFO] Step 5: Asserting result...
[PASS] Got HTTP 401 — injection pipeline works. Wrong key reached Anthropic API as expected.
[INFO] Grant cleaned up.

=== SMOKE TEST PASSED: World Physics injection pipeline validated ===
```

---

## What Each Step Proves

| Step | What it proves |
|---|---|
| Init OK | SecretVault AES-256-GCM initialises correctly |
| Seed OK | Encrypted secret storage works |
| Grant issued | Keyman authorisation flow works end-to-end |
| HTTP 401 | Key escaped SecretVault → injected into API call → reached Anthropic |

**HTTP 401 is the correct result.** The key is intentionally wrong.
If you see 200, the key somehow became valid — also acceptable.
If you see 000, curl has no network access.
Any other code is a failure.

---

## If the Test Fails

| Error | Cause | Fix |
|---|---|---|
| `supervisor-secretvault not found` | Repo not cloned | `cd /mnt/d/Claude && ls supervisor-secretvault/` |
| `ENOENT package.json` | npm deps missing | `cd /mnt/d/Claude/supervisor-secretvault && npm install` |
| `Grant request failed` | Keyman denied | Check `scripts/test_keyman_auto_approve.py` is executable: `chmod +x` |
| `HTTP 000` | No internet | Check network connectivity |

---

## Manual Step-by-Step (if you want to run each piece separately)

```bash
cd /mnt/d/Claude/unifai

# 1. Set up an ephemeral master key
export SECRETVAULT_MASTER_KEY=$(openssl rand -hex 32)

# 2. Create isolated vault root
export SECRETVAULT_ROOT=$(mktemp -d)
mkdir -p $SECRETVAULT_ROOT/config $SECRETVAULT_ROOT/secrets \
         $SECRETVAULT_ROOT/grants $SECRETVAULT_ROOT/audit $SECRETVAULT_ROOT/tmp
chmod 700 $SECRETVAULT_ROOT/secrets $SECRETVAULT_ROOT/grants

# 3. Write config pointing to auto-approve keyman
cat > $SECRETVAULT_ROOT/config/default.json <<'EOF'
{
  "vault": { "defaultTtlSeconds": 60, "maxTtlSeconds": 3600, "interactiveFallback": true },
  "keyman": { "command": "/mnt/d/Claude/unifai/scripts/test_keyman_auto_approve.py" }
}
EOF
chmod +x scripts/test_keyman_auto_approve.py

SV="node /mnt/d/Claude/supervisor-secretvault/src/cli.js"

# 4. Init
$SV init

# 5. Seed a fake key
$SV seed --alias codex-oauth --value "sk-ant-FAKE-KEY-FOR-TESTING"

# 6. Request grant (type 'y' if interactive prompt appears)
GRANT=$($SV request --alias codex-oauth --purpose "test" --agent oracle --ttl 60)
echo $GRANT

# 7. Read the key from grant file
GRANT_PATH=$(echo $GRANT | python3 -c "import sys,json; print(json.load(sys.stdin)['path'])")
API_KEY=$(cat $GRANT_PATH)
echo "Key extracted (first 20 chars): ${API_KEY:0:20}..."

# 8. Call Anthropic API — expect 401
curl -s -o /dev/null -w "HTTP %{http_code}\n" \
  -X POST https://api.anthropic.com/v1/messages \
  -H "x-api-key: $API_KEY" \
  -H "anthropic-version: 2023-06-01" \
  -H "content-type: application/json" \
  -d '{"model":"claude-haiku-4-5-20251001","max_tokens":1,"messages":[{"role":"user","content":"ping"}]}'

# 9. Cleanup
$SV cleanup
rm -rf $SECRETVAULT_ROOT
```

Expected output for step 8: `HTTP 401`

---

## Files Modified in This Session

| File | Change |
|---|---|
| `supervisor-secretvault/src/cli.js` | Bug #1: Keyman contract fields + `is_authorized` check; `SECRETVAULT_ROOT` / `SECRETVAULT_CONFIG_PATH` env override |
| `unifai/supervisor/supervisor.py` | Bug #2: DB/LOG paths use `__file__` instead of `~/supervisor/` |
| `unifai/supervisor/bin/enqueue` | Bug #2: DB path uses `SCRIPT_DIR` instead of `$HOME` |
| `unifai/supervisor/gaia.py` | Bug #3: WORKER_DUMMY_PATH multi-candidate fallback |
| `unifai/little7-installer/stages/40_local_llm.sh` | Bug #5: PROJECT_ROOT derived from script location |
| `unifai/little7-installer/stages/20_supervisor.sh` | Added SecretVault init + master key generation |
| `unifai/little7-installer/stages/50_openclaw.sh` | New: OpenClaw install + World Physics injection launcher |
| `unifai/scripts/smoke_test_openclaw_injection.sh` | New: end-to-end injection pipeline test |
| `unifai/scripts/test_keyman_auto_approve.py` | New: test-only auto-approve Keyman stub |
