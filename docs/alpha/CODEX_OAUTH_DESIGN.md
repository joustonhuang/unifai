# Codex OAuth → SecretVault Integration Design

**Version:** v0.1
**Date:** 2026-03-27
**Status:** Design (pre-implementation)

---

## Problem

Current Stage 15 (`15_cloud_secrets.sh`) stores the LLM API key using GPG at
`/etc/little7/secrets/openai_api_key.gpg`. This bypasses SecretVault entirely.

Alpha Test Plan requires:
> Credentials go directly into SecretVault, never visible to agents or Keyman.

The credential in question for OpenClaw is **Codex OAuth** — the API token used by
Oracle (OpenClaw's cloud LLM caller) to authenticate with the Claude API (Anthropic).

---

## Credential Flow

```
┌─────────────────────────────────────────────────────────────────────────┐
│  ONBOARDING (one-time)                                                  │
│                                                                         │
│  Tester                                                                 │
│    │                                                                    │
│    ▼                                                                    │
│  Encrypted WebUI  ──POST /api/seed──►  SecretVault CLI                 │
│  (HTTPS, localhost)                        │                            │
│                                            ▼                           │
│                                  secrets/codex-oauth.json              │
│                                  (AES-256-GCM, master key env)         │
└─────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────┐
│  RUNTIME (every task)                                                   │
│                                                                         │
│  Oracle (OpenClaw agent)                                                │
│    │                                                                    │
│    │  secretvault request                                               │
│    │    --alias  codex-oauth                                            │
│    │    --purpose "call-claude-api"                                     │
│    │    --agent  oracle                                                 │
│    │    --ttl    300                                                    │
│    │                                                                    │
│    ▼                                                                    │
│  SecretVault ──stdin JSON──► Keyman (keyman_authorize.py)              │
│                                   │                                     │
│                          ┌────────┴────────┐                           │
│                          ▼                 ▼                           │
│                     AUTHORIZED         DENIED                          │
│                          │                 │                           │
│                          ▼                 ▼                           │
│                  grants/uuid.secret   exit code 4                      │
│                  (plaintext, TTL 300s) (Oracle blocked)                │
│                          │                                              │
│                          ▼                                              │
│                  Oracle reads file path                                 │
│                  → calls Claude API                                     │
│                  → grant auto-expires                                   │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## SecretVault Alias Convention

| Alias | Capability | Used by |
|---|---|---|
| `codex-oauth` | Claude API (Anthropic) call | Oracle |
| `gmail-smtp` | Email delivery for reports | Wilson / Supervisor |
| `telegram-bot-token` | Telegram bot messaging | Telegram gateway |

Aliases are **capability names**, not secret names. Keyman evaluates the role's
permission to use the capability — it never sees the raw secret value.

---

## Keyman RBAC for Codex OAuth

Add to `keyman_authorize.py` role permissions:

```python
self.role_permissions = {
    "oracle":          ["codex-oauth"],
    "research_agent":  ["codex-oauth", "web-search"],
    "admin_agent":     ["codex-oauth", "web-search", "gmail-smtp", "telegram-bot-token"],
}
```

Oracle is the only agent allowed to call the Claude API directly.
All other agents must route through Oracle.

---

## Gap vs. Current State

| Item | Current | Required |
|---|---|---|
| Storage | GPG at `/etc/little7/secrets/` | AES-256-GCM in SecretVault |
| Input method | TTY prompt in Stage 15 | Encrypted WebUI |
| Secret name | `OPENAI_API_KEY` | alias `codex-oauth` |
| Provider | OpenAI | Anthropic (Claude) |
| Access control | None (file permission only) | Keyman RBAC |
| Audit trail | None | SecretVault audit log |

---

## Stage 15 Migration Plan

Stage 15 needs to be rewritten or replaced:

1. Remove GPG storage path entirely
2. Prompt user for Anthropic API key (Claude, not OpenAI)
3. Call: `secretvault seed --alias codex-oauth --value "$API_KEY"`
4. Stage 16 becomes: `secretvault request --alias codex-oauth --agent installer-verify --purpose "verify-connectivity" --ttl 30` → live API ping

Alternatively, Stage 15 is removed from the CLI installer and replaced by the
encrypted WebUI seeding flow (preferred for Alpha).

---

## Encrypted WebUI (Minimal Spec)

The WebUI is a **World Physics primitive** — a locked-down local page that:

- Runs on `localhost:7700` (bound to loopback only)
- Served over HTTPS (self-signed cert, HSTS enforced)
- Single-page form: alias + secret value + submit
- On submit: shells out to `secretvault seed --alias <a> --value <v>`
- No JavaScript frameworks — plain HTML form, minimal attack surface
- Sessions are ephemeral (no cookies, no state)
- Access log written to SecretVault audit trail

The URL is given to the tester during onboarding. They visit it once to enter credentials,
then it is no longer needed (though it remains accessible for updates).

---

## Telegram Credential Safety

As stated in the Alpha Test Plan:

> If a user attempts to send credentials via Telegram, the message is refused,
> deleted, and the user is warned to change the secret immediately.

Implementation hook (Telegram gateway layer):
- Pattern-match incoming messages for strings that look like API keys
  (e.g. `sk-ant-`, `Bearer `, 40+ char hex/base64 strings)
- If matched: delete message, reply with warning, log to audit trail
- Regex is conservative (false positives are acceptable; false negatives are not)
