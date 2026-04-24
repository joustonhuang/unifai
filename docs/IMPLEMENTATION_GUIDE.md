# 📚 UnifAI VM-Native Installation & Governance Implementation Guide

**Document Version:** 1.0  
**Date:** 2026-04-22  
**Author:** Wilgner Lucas (Based on Jouston Huang's Architecture)  
**Scope:** Complete technical documentation for VM-native deployment + AI governance framework

---

## 📖 Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Architecture Overview](#2-architecture-overview)
3. [Phase-by-Phase Installation Guide](#3-phase-by-phase-installation-guide)
4. [CI/CD Pipeline Documentation](#4-cicd-pipeline-documentation)
5. [Secret Governance Ledger](#5-secret-governance-ledger)
6. [Deployment & Operations](#6-deployment--operations)
7. [Security Model](#7-security-model)
8. [Troubleshooting](#8-troubleshooting)
9. [References & Advanced Topics](#9-references--advanced-topics)

---

## 1. Executive Summary

### 1.1 What Problem Are We Solving?

**The Challenge:**
- OpenClaw is powerful but vulnerable to AI agents leaking secrets
- Traditional Docker/container approaches add complexity and security risks
- Agents need to perform complex tasks (deploy, migrate, integrate APIs) **without possessing or exposing secrets**

**The Solution: UnifAI**
Three pillars:
1. **Native Installation** - VM-as-a-Department (bare-metal/OpenStack, no nested virtualization)
2. **Governance Exoskeleton** - Ledger-based authorization enforced by Keyman + Supervisor
3. **World Physics** - Immutable rules (Rule 0: Secret Sovereignty) that agents must follow

### 1.2 What We've Built

Three files have been created in `feat/vm-native-installer-sequence` branch:

| File | Purpose | Size |
|------|---------|------|
| `installer.sh` | 8-phase native installation automation | 12 KB |
| `.github/workflows/openclaw-template.yml` | CI/CD pipeline (lint, test, install, deploy) | 8.1 KB |
| `secret.md` | Governance Ledger (agent instruction set) | 14 KB |

**Total Implementation:** ~34 KB of production-ready code + documentation

### 1.3 Key Principles

```
┌─────────────────────────────────────────────────────────┐
│ Rule 0: Secret Sovereignty                             │
│ ─────────────────────────────────────────────────────────│
│ Agents NEVER possess secrets.                          │
│ Only Keyman + SecretVault hold credentials.            │
│ Agents request ephemeral grants from Supervisor.       │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│ Ledger-First Protocol (Cowork Pattern)                 │
│ ─────────────────────────────────────────────────────────│
│ Before EVERY action, agents must:                      │
│ 1. State the task                                      │
│ 2. Break into deterministic sub-tasks                  │
│ 3. Identify permission barriers (mark with 🔐)        │
│ 4. Request ephemeral grants from Supervisor            │
│ 5. Execute using grant_ids (NOT secrets)              │
│ 6. Log completion to immutable audit trail             │
│ 7. Escalate to human on any failure                    │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│ No Docker. No Nested Virtualization.                   │
│ ─────────────────────────────────────────────────────────│
│ Everything runs natively on Ubuntu/Debian.             │
│ Systemd manages service lifecycle.                     │
│ Native tools (npm, pip, bash) bootstrap everything.   │
└─────────────────────────────────────────────────────────┘
```

---

## 2. Architecture Overview

### 2.1 System Components & Dependencies

```
┌────────────────────────────────────────────────────────────────────────┐
│                    UnifAI Governance Stack                             │
├────────────────────────────────────────────────────────────────────────┤
│                                                                        │
│  ┌──────────────────────────────────────────────────────────────────┐ │
│  │ AI AGENT LAYER (Claude/LLM)                                     │ │
│  │ ─────────────────────────────────────────────────────────────── │ │
│  │ • Follows Ledger-First Protocol                                │ │
│  │ • Reads secret.md (binding governance rules)                   │ │
│  │ • Never possesses secrets                                      │ │
│  │ • Requests grants via Supervisor                               │ │
│  └──────────────────────────────────────────────────────────────────┘ │
│         ▲                                                              │
│         │ supervisor.request_grant()                                  │
│         │ supervisor.execute_with_grant()                             │
│         ▼                                                              │
│  ┌──────────────────────────────────────────────────────────────────┐ │
│  │ SUPERVISOR (Python Service)                                     │ │
│  │ ─────────────────────────────────────────────────────────────── │ │
│  │ • Mediates between Agent ↔ Keyman                               │ │
│  │ • Routes grant requests to Keyman for approval                  │ │
│  │ • Injects secrets into subprocess at runtime                    │ │
│  │ • Manages subprocess lifecycle                                  │ │
│  │ • Creates audit trail entries                                   │ │
│  │ Service: unifai-supervisor (port 5000)                          │ │
│  └──────────────────────────────────────────────────────────────────┘ │
│         ▲                                                              │
│         │ Check permission / Issue grant                              │
│         ▼                                                              │
│  ┌──────────────────────────────────────────────────────────────────┐ │
│  │ KEYMAN (Python Service)                                         │ │
│  │ ─────────────────────────────────────────────────────────────── │ │
│  │ • Authorization Authority (RBAC)                                │ │
│  │ • Evaluates capability requests                                 │ │
│  │ • Issues/revokes grants                                         │ │
│  │ • Communicates with SecretVault                                 │ │
│  │ • Maintains audit trail                                         │ │
│  │ Service: unifai-keyman (port 5001)                              │ │
│  └──────────────────────────────────────────────────────────────────┘ │
│         ▲                                                              │
│         │ Fetch secret (via grant_id)                                 │
│         ▼                                                              │
│  ┌──────────────────────────────────────────────────────────────────┐ │
│  │ SECRETVAULT (Node.js Service)                                   │ │
│  │ ─────────────────────────────────────────────────────────────── │ │
│  │ • Custody of secrets (API keys, tokens, credentials)            │ │
│  │ • TTL-bound grants (ephemeral access)                           │ │
│  │ • Alias abstraction (agent never sees raw secret)               │ │
│  │ • Cleanup of expired grants                                     │ │
│  │ Service: unifai-secretvault (port 5002)                         │ │
│  └──────────────────────────────────────────────────────────────────┘ │
│                                                                        │
├────────────────────────────────────────────────────────────────────────┤
│                           OPENCLAW (Orchestrator)                      │
│  • Web UI for job scheduling                                          │
│  • LLM integration                                                    │
│  • Agent spawning                                                     │
│  Service: unifai-openclaw (port 3000)                                 │
├────────────────────────────────────────────────────────────────────────┤
│                         LOCAL LLM RUNTIME                              │
│  • LM Studio (running locally)                                        │
│  • Endpoint: http://localhost:1234/v1                                │
│  • API Key: lm-studio (dummy, local-only)                            │
└────────────────────────────────────────────────────────────────────────┘
```

### 2.2 Data Flow: Grant Request Example

```
┌─────────────────────────────────────────────────────────────────────────┐
│ SCENARIO: Agent wants to push Docker image to GCP                       │
└─────────────────────────────────────────────────────────────────────────┘

STEP 1: Agent reads secret.md (Ledger Protocol)
  → Sees Rule 0: "Never possess secrets"
  → Prepares grant request

STEP 2: Agent calls Supervisor
  supervisor.request_grant(
    capability="gcp_artifact_registry_push",
    task_id="deploy-svc-v1.2.3",
    ttl_seconds=300,
    scope="gcr.io/my-project/my-service:*",
    justification="Push service image to production registry"
  )

STEP 3: Supervisor forwards to Keyman
  POST http://localhost:5001/api/grants/request
  Payload: {capability, task_id, ttl, scope, justification, agent_id}

STEP 4: Keyman evaluates request
  • Check: Is agent_id allowed to access gcp_artifact_registry?
  • Check: Is scope narrow enough? (not wildcard *:)
  • Check: Is TTL reasonable? (300s for transient task ✓)
  • Decision: APPROVED

STEP 5: Keyman contacts SecretVault
  POST http://localhost:5002/api/grants/create
  {grant_id, secret_reference, ttl, scope}
  SecretVault: Creates TTL-bound grant, schedules cleanup at +300s

STEP 6: Keyman returns grant to Supervisor
  Response: {
    grant_id: "grant_abc123xyz",
    status: "approved",
    expires_at: "2026-04-22T12:15:00Z",
    scope: "gcr.io/my-project/my-service:*"
  }

STEP 7: Supervisor returns to Agent
  Agent receives: grant_id = "grant_abc123xyz"
  ⚠️ Agent NEVER sees the actual GCP service account key

STEP 8: Agent executes with grant
  supervisor.execute_with_grant(
    grant_id="grant_abc123xyz",
    command="docker push gcr.io/my-project/my-service:v1.2.3",
    redact_output=true
  )

STEP 9: Supervisor executes subprocess with secret injection
  • Fetches real secret from SecretVault using grant_id
  • Injects into environment only at subprocess spawn time
  • Secret lives in child process memory only
  • Parent process never sees it
  • Output is redacted (secret never in logs)

STEP 10: Supervisor logs to audit trail
  Audit Entry:
  {
    timestamp: "2026-04-22T12:10:00Z",
    agent_id: "agent-12345",
    grant_id: "grant_abc123xyz",
    capability: "gcp_artifact_registry_push",
    task_id: "deploy-svc-v1.2.3",
    result: "success",
    duration_ms: 45000
  }

STEP 11: SecretVault auto-cleanup
  At 2026-04-22T12:15:00Z (ttl_seconds=300):
  • Delete grant_abc123xyz
  • Remove secret from memory
  • Log cleanup event to immutable store
```

### 2.3 Network Architecture

```
┌──────────────────────────────────────────────────────────┐
│ Ubuntu/Debian VM (Bare-metal or OpenStack)              │
├──────────────────────────────────────────────────────────┤
│                                                          │
│ LOCALHOST (127.0.0.1)                                   │
│                                                          │
│  :3000   ← OpenClaw (Agent UI)                          │
│  :5000   ← Supervisor (Orchestration)                   │
│  :5001   ← Keyman (Authorization)                       │
│  :5002   ← SecretVault (Custody)                        │
│  :1234   ← LM Studio (Local LLM)                        │
│                                                          │
│  /opt/unifai/                                           │
│    ├─ venv/              (Python virtualenv)            │
│    ├─ supervisor/        (Supervisor code)              │
│    ├─ keyman/            (Keyman code)                  │
│    ├─ supervisor-secretvault/  (SecretVault code)      │
│    ├─ openclaw/          (OpenClaw code)                │
│    ├─ .env               (Global environment)           │
│    └─ installer.log      (Installation output)          │
│                                                          │
│  /var/log/unifai/                                       │
│    ├─ supervisor.log                                    │
│    ├─ keyman.log                                        │
│    ├─ secretvault.log                                   │
│    └─ audit_trail.jsonl  (Immutable grant log)         │
│                                                          │
│  Systemd Services (enabled + running):                  │
│  └─ unifai-supervisor.service                          │
│  └─ unifai-keyman.service                              │
│  └─ unifai-secretvault.service                         │
│  └─ unifai-openclaw.service                            │
│                                                          │
└──────────────────────────────────────────────────────────┘
```

---

## 3. Phase-by-Phase Installation Guide

### 3.1 Prerequisites

**System Requirements:**
- OS: Ubuntu 22.04 LTS or Debian 12 (or newer)
- RAM: 8GB minimum (16GB recommended for OpenClaw)
- Disk: 50GB free (installation takes ~20GB)
- Network: Internet access for package downloads
- Privileges: Root/sudo access for initial setup

**Pre-installation Checklist:**
```bash
# Verify OS
lsb_release -ds
# Expected: Ubuntu 22.04 LTS, Debian 12, etc.

# Verify internet
ping -c 1 8.8.8.8

# Verify sudo
sudo whoami
# Expected: root

# Free disk space
df -h /
# Expected: >50GB available
```

### 3.2 Phase 0: System Dependencies

**What Happens:**
- Update package managers
- Install build tools, SSL/TLS infrastructure
- Install Git, jq, curl, wget

**Manual Execution:**
```bash
sudo apt-get update
sudo apt-get install -y \
    build-essential \
    curl wget git jq \
    ca-certificates apt-transport-https \
    software-properties-common systemd openssh-server
```

**Validation:**
```bash
gcc --version           # Build tools
git --version          # Git
curl --version         # Curl
node --version 2>/dev/null || echo "Node: not yet installed"
```

**Time:** ~2-3 minutes

### 3.3 Phase 1: supervisor-secretvault Installation

**What Happens:**
- Clone supervisor-secretvault repository
- Install Node.js dependencies
- Register systemd service (unifai-secretvault.service)

**Manual Execution:**
```bash
INSTALL_PREFIX="/opt/unifai"
mkdir -p "${INSTALL_PREFIX}/supervisor-secretvault"
cd "${INSTALL_PREFIX}/supervisor-secretvault"

# Clone repository
git clone https://github.com/joustonhuang/supervisor-secretvault.git .

# Install dependencies
npm install

# Create systemd service
sudo cat > /etc/systemd/system/unifai-secretvault.service << 'EOF'
[Unit]
Description=UnifAI Secret Vault Service
After=network.target
Wants=network-online.target

[Service]
Type=simple
User=unifai
WorkingDirectory=/opt/unifai/supervisor-secretvault
ExecStart=/usr/bin/node cli.js
Restart=on-failure
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
```

**Validation:**
```bash
# Check repository
cd /opt/unifai/supervisor-secretvault && git log --oneline -3

# Check Node modules
ls -la node_modules | head -10

# Check service exists
systemctl list-unit-files | grep unifai-secretvault
```

**Service Ports:** 5002 (default)  
**Time:** ~2-3 minutes

### 3.4 Phase 2: Python Environment

**What Happens:**
- Add deadsnakes PPA (for Python 3.10)
- Create global virtualenv at `/opt/unifai/venv`
- Upgrade pip/setuptools/wheel

**Manual Execution:**
```bash
PYTHON_VERSION="3.10"
INSTALL_PREFIX="/opt/unifai"

# Add Python PPA
sudo add-apt-repository -y ppa:deadsnakes/ppa
sudo apt-get update

# Install Python
sudo apt-get install -y \
    python${PYTHON_VERSION} \
    python${PYTHON_VERSION}-venv \
    python${PYTHON_VERSION}-dev \
    python3-pip

# Create virtualenv
mkdir -p "${INSTALL_PREFIX}/venv"
python${PYTHON_VERSION} -m venv "${INSTALL_PREFIX}/venv"

# Activate and upgrade
source "${INSTALL_PREFIX}/venv/bin/activate"
pip install --upgrade pip setuptools wheel
deactivate
```

**Validation:**
```bash
# Check venv
ls -la /opt/unifai/venv/bin/python*

# Check pip
source /opt/unifai/venv/bin/activate
pip --version
# Expected: pip X.X.X from /opt/unifai/venv/...
deactivate
```

**Time:** ~3-4 minutes

### 3.5 Phase 3: Keyman Installation

**What Happens:**
- Clone Keyman repository
- Install Python dependencies
- Register systemd service (unifai-keyman.service)

**Manual Execution:**
```bash
INSTALL_PREFIX="/opt/unifai"

mkdir -p "${INSTALL_PREFIX}/keyman"
cd "${INSTALL_PREFIX}/keyman"

# Clone repository
git clone https://github.com/joustonhuang/keyman.git .

# Activate venv and install dependencies
source "${INSTALL_PREFIX}/venv/bin/activate"
pip install -r requirements.txt

# Create systemd service
sudo cat > /etc/systemd/system/unifai-keyman.service << EOF
[Unit]
Description=UnifAI Keyman Service (Authorization)
After=network.target unifai-secretvault.service
Wants=network-online.target

[Service]
Type=simple
User=unifai
WorkingDirectory=${INSTALL_PREFIX}/keyman
Environment="PATH=${INSTALL_PREFIX}/venv/bin"
ExecStart=${INSTALL_PREFIX}/venv/bin/python -m keyman.cli
Restart=on-failure
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
```

**Validation:**
```bash
# Check installation
ls -la /opt/unifai/keyman/

# Check dependencies
source /opt/unifai/venv/bin/activate
pip list | grep -E "flask|sqlalchemy|requests"
deactivate

# Check service exists
systemctl list-unit-files | grep unifai-keyman
```

**Service Ports:** 5001  
**Dependencies:** unifai-secretvault (starts after)  
**Time:** ~2-3 minutes

### 3.6 Phase 4: Supervisor Installation

**What Happens:**
- Clone Supervisor repository
- Install Python dependencies
- Register systemd service (unifai-supervisor.service)

**Manual Execution:**
```bash
INSTALL_PREFIX="/opt/unifai"

mkdir -p "${INSTALL_PREFIX}/supervisor"
cd "${INSTALL_PREFIX}/supervisor"

# Clone repository
git clone https://github.com/joustonhuang/supervisor.git .

# Activate venv and install dependencies
source "${INSTALL_PREFIX}/venv/bin/activate"
pip install -r requirements.txt

# Create systemd service
sudo cat > /etc/systemd/system/unifai-supervisor.service << EOF
[Unit]
Description=UnifAI Supervisor Service (Agent Orchestration)
After=network.target unifai-keyman.service unifai-secretvault.service
Wants=network-online.target

[Service]
Type=simple
User=unifai
WorkingDirectory=${INSTALL_PREFIX}/supervisor
Environment="PATH=${INSTALL_PREFIX}/venv/bin"
ExecStart=${INSTALL_PREFIX}/venv/bin/python -m supervisor.cli
Restart=on-failure
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
```

**Validation:**
```bash
# Check installation
ls -la /opt/unifai/supervisor/

# Check dependencies
source /opt/unifai/venv/bin/activate
pip list | grep -E "flask|requests|pydantic"
deactivate

# Check service exists
systemctl list-unit-files | grep unifai-supervisor
```

**Service Ports:** 5000  
**Dependencies:** unifai-keyman, unifai-secretvault  
**Time:** ~2-3 minutes

### 3.7 Phase 5: OpenClaw Installation

**What Happens:**
- Install Node.js v18 (if not present)
- Clone OpenClaw repository
- Install Node.js dependencies
- Register systemd service (unifai-openclaw.service)

**Manual Execution:**
```bash
# Install Node.js (if not present)
if ! command -v node &> /dev/null; then
    curl -fsSL https://deb.nodesource.com/setup_18.x | sudo bash -
    sudo apt-get install -y nodejs
fi

INSTALL_PREFIX="/opt/unifai"

mkdir -p "${INSTALL_PREFIX}/openclaw"
cd "${INSTALL_PREFIX}/openclaw"

# Clone repository
git clone https://github.com/openclaw/openclaw.git .

# Install dependencies
npm install

# Create systemd service
sudo cat > /etc/systemd/system/unifai-openclaw.service << EOF
[Unit]
Description=UnifAI OpenClaw Service
After=network.target unifai-supervisor.service
Wants=network-online.target

[Service]
Type=simple
User=unifai
WorkingDirectory=${INSTALL_PREFIX}/openclaw
ExecStart=/usr/bin/npm start
Restart=on-failure
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
```

**Validation:**
```bash
# Check Node.js
node --version

# Check installation
ls -la /opt/unifai/openclaw/

# Check dependencies
cd /opt/unifai/openclaw && npm list 2>/dev/null | head -20

# Check service exists
systemctl list-unit-files | grep unifai-openclaw
```

**Service Ports:** 3000  
**Dependencies:** unifai-supervisor  
**Time:** ~4-5 minutes

### 3.8 Phase 6: LLM Local Integration

**What Happens:**
- Create global environment configuration file (`.env`)
- Configure local LM Studio settings
- Set service ports
- Enable audit logging

**Manual Execution:**
```bash
INSTALL_PREFIX="/opt/unifai"

# Create environment file
cat > "${INSTALL_PREFIX}/.env" << 'EOF'
# UnifAI Global Environment Configuration
OPENAI_BASE_URL="http://localhost:1234/v1"
OPENAI_API_KEY="lm-studio"
OPENAI_MODEL="local-model"

# Service Ports
OPENCLAW_PORT=3000
SUPERVISOR_PORT=5000
KEYMAN_PORT=5001
SECRETVAULT_PORT=5002

# Installation Paths
INSTALL_PREFIX="/opt/unifai"
PYTHON_VENV="${INSTALL_PREFIX}/venv"

# Logging
LOG_LEVEL="INFO"
LOG_DIR="/var/log/unifai"

# Security
SECRET_VAULT_MODE="supervised"
PERMISSION_ENFORCEMENT="strict"
AUDIT_LOGGING="enabled"
EOF

# Set permissions
sudo chmod 644 "${INSTALL_PREFIX}/.env"

# Create log directory
sudo mkdir -p /var/log/unifai
sudo chown unifai:unifai /var/log/unifai
sudo chmod 755 /var/log/unifai
```

**Validation:**
```bash
# Check .env file
cat /opt/unifai/.env

# Check log directory
ls -la /var/log/unifai/

# Check permissions
stat /var/log/unifai/ | grep "Access"
```

**Time:** ~1 minute

### 3.9 Phase 7: UnifAI User & Permissions

**What Happens:**
- Create `unifai` system user
- Set proper ownership of `/opt/unifai` directory
- Configure permissions

**Manual Execution:**
```bash
# Create unifai user if not exists
if ! id -u unifai &> /dev/null; then
    sudo useradd -m -s /bin/bash -G sudo unifai
    echo "Created user: unifai"
fi

INSTALL_PREFIX="/opt/unifai"

# Set ownership
sudo chown -R unifai:unifai "${INSTALL_PREFIX}"
sudo chmod -R 755 "${INSTALL_PREFIX}"
```

**Validation:**
```bash
# Check user exists
id unifai

# Check ownership
ls -la /opt/unifai | head -5

# Check permissions
stat /opt/unifai | grep "Access"
```

**Time:** ~1 minute

### 3.10 Phase 8: Validation & Summary

**What Happens:**
- Verify all components installed
- List systemd services
- Print summary and next steps

**Manual Execution:**
```bash
# Check Node.js
node --version

# Check Python
python3.10 --version

# List services
systemctl list-unit-files | grep unifai-

# Check .env
cat /opt/unifai/.env

# Show summary
echo "=== Installation Summary ==="
echo "Installation prefix: /opt/unifai"
echo "Python version: 3.10"
echo "Node version: 18"
echo ""
echo "Next steps:"
echo "  1. Start services: sudo systemctl start unifai-secretvault unifai-keyman unifai-supervisor unifai-openclaw"
echo "  2. Enable auto-start: sudo systemctl enable unifai-*"
echo "  3. Check status: sudo systemctl status unifai-*"
```

**Time:** ~1 minute

### 3.11 Full Installation Time

**Total:** ~20-25 minutes

**Breakdown:**
- Phase 0 (System deps): 2-3 min
- Phase 1 (SecretVault): 2-3 min
- Phase 2 (Python env): 3-4 min
- Phase 3 (Keyman): 2-3 min
- Phase 4 (Supervisor): 2-3 min
- Phase 5 (OpenClaw): 4-5 min
- Phase 6 (LLM config): 1 min
- Phase 7 (User setup): 1 min
- Phase 8 (Validation): 1 min

---

## 4. CI/CD Pipeline Documentation

### 4.1 Pipeline Overview

**File:** `.github/workflows/openclaw-template.yml`

**Trigger Events:**
```yaml
on:
  push:
    branches: [ main, develop, "feat/**" ]
  pull_request:
    branches: [ main, develop ]
  schedule:
    - cron: "0 2 * * *"  # Daily at 02:00 UTC
```

**Execution Matrix:**
- Runs on: `ubuntu-latest`
- Environment: Python 3.10, Node.js 18

### 4.2 Job 1: Lint & Format Check

**Purpose:** Code quality gates before testing

**Tools:**
- Python: `flake8` (PEP8 style), `black` (formatter), `pylint` (analysis)
- JavaScript: `eslint`, `prettier`

**Failures:**
- Hard fail: None (linting is advisory in this configuration)
- Soft fail (continue-on-error): All linters

**Duration:** ~3-5 minutes

**Example Output:**
```
[INFO] Run Python lint (flake8)
E501 line too long (>79 characters)
E302 expected 2 blank lines, found 1

[INFO] Run Python format check (black)
would reformat file.py

[INFO] Run JavaScript lint (eslint)
warning: unused variable 'x'
```

### 4.3 Job 2: Unit Tests

**Purpose:** Verify functionality and code coverage

**Tests:**
- Python: `pytest` (unit tests + coverage)
- JavaScript: `npm test` (Jest/Mocha equivalent)

**Coverage Reporting:**
- XML format: `coverage.xml`
- Upload to Codecov (optional)

**Duration:** ~5-10 minutes (depending on test count)

**Example Output:**
```
======================== test session starts =========================
collected 24 items
tests/test_keyman.py::test_request_grant PASSED        [  4%]
tests/test_supervisor.py::test_execute_with_grant PASSED [ 8%]
... (more tests)

========================= 24 passed in 3.45s ==========================
coverage report:
- keyman.py:       87% coverage
- supervisor.py:   92% coverage
- secretvault.js:  84% coverage
```

### 4.4 Job 3: Installation Test

**Purpose:** Validate installer.sh syntax and service definitions

**Steps:**
1. Syntax check: `bash -n installer.sh`
2. Service check: Verify all 4 services defined
3. LLM config: Verify local LM Studio configuration

**Duration:** ~1-2 minutes

**Example Output:**
```
[INFO] Installer syntax check: PASSED ✓
[INFO] Service: unifai-secretvault - FOUND ✓
[INFO] Service: unifai-keyman - FOUND ✓
[INFO] Service: unifai-supervisor - FOUND ✓
[INFO] Service: unifai-openclaw - FOUND ✓
[INFO] LLM Config: Local LM Studio - CONFIGURED ✓
```

### 4.5 Job 4: Docker Image Build

**Purpose:** Build Docker image (fallback, if Dockerfile exists)

**Trigger:** Only if Dockerfile present in repo

**Output:** Docker image `unifai:latest`

**Duration:** ~5-10 minutes

**Status:** Conditional (continue-on-error)

### 4.6 Job 5: Security Scan

**Purpose:** Detect vulnerabilities in dependencies and code

**Tools:** Trivy (container security scanner)

**Output:** SARIF report uploaded to GitHub Security

**Duration:** ~2-5 minutes

**Status:** Continue-on-error

### 4.7 Job 6: Build & Deploy

**Purpose:** Create deployment artifact and prepare release

**Conditions:**
- Runs only on: `main` branch
- Runs only on: `push` event (not PR)

**Steps:**
1. Create build artifact: `unifai-native-${commit_sha}.tar.gz`
2. Upload to GitHub Artifacts
3. Create GitHub Release (if git tag exists)

**Duration:** ~2-3 minutes

**Output:**
```
unifai-native-abcd1234efgh5678.tar.gz (saved to artifacts)
```

### 4.8 Job 7: Pipeline Summary

**Purpose:** Print final status of all jobs

**Output:**
```
=== UnifAI CI/CD Pipeline Complete ===
Lint: success
Tests: success
Install Test: success
Docker Build: skipped
Security Scan: success
Deploy: success (if on main)
============================================
```

### 4.9 How to Trigger Pipeline Manually

**Push to feat branch:**
```bash
git push origin feat/vm-native-installer-sequence
```

**Push to main (triggers deployment):**
```bash
git checkout main
git merge feat/vm-native-installer-sequence
git push origin main
```

**Create release:**
```bash
git tag -a v1.0.0 -m "Release version 1.0.0"
git push origin v1.0.0
```

### 4.10 Debugging Pipeline Failures

**View logs:**
1. Go to GitHub Actions tab
2. Click failed workflow
3. Expand job logs
4. Search for error message

**Common issues:**

| Error | Cause | Fix |
|-------|-------|-----|
| `requirements.txt not found` | Missing Python deps file | Create `requirements.txt` in repo root |
| `node_modules not cached` | First run, npm install slow | Normal, future runs use cache |
| `Linter warnings fail build` | Code style issues | Run `black .` and `npm run format` locally |
| `Docker build fails` | Dockerfile syntax error | Validate Dockerfile locally with `docker build` |

---

## 5. Secret Governance Ledger (secret.md)

### 5.1 Ledger Purpose & Binding Authority

**Document:** `/home/wilgner/UnifAI/secret.md`

**Authority:** Jouston Huang (Chief Architect)

**Status:** ACTIVE - Binding for all Agent operations

**Effective Date:** 2026-04-22

**Review Cycle:** Quarterly (next: 2026-05-22)

### 5.2 Three Immutable Rules

#### **Rule 0: Secret Sovereignty**

```
YOU DO NOT POSSESS SECRETS.

Secrets are held by:
  • Keyman (Authorization Authority)
  • SecretVault (Custody)

If you need a secret:
  1. Request via Supervisor
  2. Provide task context & justification
  3. Specify TTL (time-to-live)
  4. Define scope boundary

Keyman evaluates request:
  ✅ Approve → Issues ephemeral grant (grant_id)
  ❌ Deny   → Logs denial + escalates

CRITICAL: Real API key NEVER touches your execution context.
Only grant_id is passed to you.
Supervisor injects real secret into child process at runtime.
```

#### **Rule 1: No Token Guessing**

```
NEVER attempt to:
  ❌ Guess API keys
  ❌ Construct auth headers manually
  ❌ Inject secrets into environment variables
  ❌ Write secrets to disk files (even temp)
  ❌ Hardcode credentials in code/prompts

If blocked:
  ❌ Don't retry 5 times
  ✅ Escalate to human via audit trail

If you think you need credentials:
  → STOP
  → Use Supervisor
  → Ask permission
```

#### **Rule 2: Ledger-First Protocol**

```
Before taking ANY action that touches:
  • External APIs (cloud, SaaS, databases)
  • File systems (reads/writes)
  • Network resources (downloads, webhooks)
  • Permission-gated operations

You MUST complete the Ledger Checklist (7 steps).
```

### 5.3 Ledger Checklist (7 Steps)

**Step 1: STATE THE TASK**
```
Example: "Deploy microservice to production"
Write down: What is the high-level goal?
```

**Step 2: BREAK INTO SUB-TASKS (Deterministic)**
```
List EVERY step sequentially:
  • Build Docker image
  • Push to registry
  • Update Kubernetes manifest
  • Apply kubectl
  • Verify rollout status
```

**Step 3: IDENTIFY PERMISSION BARRIERS**
```
Mark with 🔐 symbol:
  • Build Docker image (no barrier)
  • Push to registry 🔐 (needs Docker Hub token)
  • Update K8s manifest (read-only, no barrier)
  • Apply kubectl 🔐 (needs cluster credentials)
  • Verify rollout (read-only, no barrier)
```

**Step 4: REQUEST EPHEMERAL GRANTS**
```python
supervisor.request_grant(
  capability="docker_registry_push",
  task_id="deploy-svc-v1.2.3",
  ttl_seconds=300,  # 5 minutes max
  scope="gcr.io/project/*",  # Narrow scope
  justification="Deploy microservice v1.2.3 to prod"
)

# Returns:
✅ grant_id (use this, NOT the real secret)
❌ denial reason (audit logged, you stop)
```

**Step 5: EXECUTE SUB-TASKS (WITH GRANTS)**
```
For each sub-task:
  • Check "PERMISSION?" column
  • If 🔐, use grant_id from step 4
  • If ✓, proceed normally
  • Track which step you're on (for audit)
```

**Step 6: LOG COMPLETION**
```
Record in audit trail:
  - Task ID
  - Sub-task sequence
  - Grants used (grant_ids, not secrets)
  - Outcome (success/failure)
  - Duration

Keyman + Supervisor auto-rotate logs to immutable store
```

**Step 7: NOTIFY HUMAN (if needed)**
```
If ANY sub-task failed:
  → STOP
  → Create incident ticket with:
      - What you tried
      - Why it failed
      - Current audit trail
  → Wait for human decision
```

### 5.4 Permission Enforcement Gates

#### **Gate 1: Capability Denial is NOT Retry Material**

```
If Keyman denies a grant:
  ❌ Request DENIED
  Reason: "User role 'agent' cannot access 'database_rw' (admin-only)"

YOUR RESPONSE:
  ❌ Do NOT:
    • Retry 10 times
    • Try different permission levels
    • Attempt workarounds
    • Write to temp files as backdoor
  
  ✅ DO:
    • Log the denial
    • Escalate to human via supervised_incident()
    • Wait for human to grant permission OR
    • Suggest alternative (read-only query, etc)
```

#### **Gate 2: Token Refresh Loop**

```python
def safe_api_call(task_id, api_endpoint, payload):
    # Step 1: Get grant
    grant = supervisor.request_grant(
        capability="api_call",
        task_id=task_id,
        ttl_seconds=60,
        scope=api_endpoint,
        justification=f"Calling {api_endpoint}"
    )
    
    if not grant:
        raise PermissionDenied("Keyman denied grant")
    
    # Step 2: Call API (Supervisor injects credential)
    result = supervisor.execute_with_grant(
        grant_id=grant.id,
        command=f"curl -H 'Authorization: Bearer {{PLACEHOLDER}}' {api_endpoint}",
        input_data=payload
    )
    
    # Step 3: Handle expiry (automatic retry if 401)
    if result.status == 401:  # Unauthorized
        grant = supervisor.request_grant(...)  # Auto-retry
        result = supervisor.execute_with_grant(...)
    
    return result
```

#### **Gate 3: Subprocess Isolation (No Secret Leakage)**

```bash
# ❌ WRONG: Token in plaintext
export DOCKER_PASSWORD="my-secret-token"
docker login -u user -p $DOCKER_PASSWORD

# ✅ RIGHT: Use Supervisor
supervisor exec-with-grant \
  --grant-id <grant_id_from_keyman> \
  --command "docker login -u user -p {SECRET_PLACEHOLDER}" \
  --redact-output

# Supervisor:
#   1. Fetches real secret from SecretVault via grant
#   2. Injects at subprocess spawn time
#   3. Secret stays in child process memory only
#   4. Parent process never sees it
#   5. Output is redacted (no secret in logs)
```

### 5.5 Common Scenarios

#### **Scenario 1: Deploy to Cloud (GCP)**

```
TASK: Deploy service v1.2.3 to GCP Cloud Run

LEDGER CHECKLIST:

[ ✓ ] 1. State task
       → Deploy service v1.2.3 to GCP Cloud Run

[ ✓ ] 2. Break into sub-tasks
       → Build container image
       → Push to Artifact Registry 🔐
       → Update Cloud Run manifest 🔐
       → Verify rollout

[ ✓ ] 3. Identify barriers
       → Artifact Registry: needs GCP auth token
       → Cloud Run update: needs GCP auth token

[ ✓ ] 4. Request grants
       supervisor.request_grant(
         capability="gcp_artifact_registry",
         ttl_seconds=300,
         scope="projects/my-project/locations/us-central1/*",
         justification="Deploy service v1.2.3"
       )
       → grant_id = "grant_abc123"

[ ✓ ] 5. Execute with grants
       supervisor.execute_with_grant(
         grant_id="grant_abc123",
         command="gcloud auth login && docker push ...",
         redact_output=true
       )

[ ✓ ] 6. Log completion
       Audit trail: Task deployed successfully (45 seconds)

[ ✓ ] 7. Done
```

#### **Scenario 2: Database Migration (Permission Denied)**

```
TASK: Run database migration on production DB

[ ✓ ] 1-3. (steps skipped)

[ ✓ ] 4. Request grant
       supervisor.request_grant(
         capability="database_write",
         scope="prod-db/*",
         ttl_seconds=120,
         justification="Run migration v2024.04.22"
       )
       
       ❌ DENIED: "Agent role cannot access 'prod-db' (human-only)"
       Keyman creates incident ticket #4521

[ ✓ ] 5. YOUR RESPONSE
       ✅ Instead of retry:
          supervised_incident.create(
            title="Production DB Migration Required",
            context="Migration v2024.04.22 waiting for approval",
            incident_id="#4521"
          )
          print("Waiting for human approval...")

[ After human approval ]

       supervisor.request_grant(...)  ← Now approved
       → grant_id = "grant_xyz789"
       Execute migration with grant_xyz789
```

#### **Scenario 3: Rate-Limited API Call**

```
TASK: Fetch data from external API (rate-limited: 100 req/min)

[ ✓ ] 4. Request grant WITH rate limit context
       supervisor.request_grant(
         capability="external_api_read",
         scope="api.example.com/data/*",
         ttl_seconds=60,
         rate_limit_context={
           "limit": 100,
           "window_seconds": 60,
           "current_usage": "fetch from Supervisor"
         },
         justification="Fetch user profiles batch"
       )

[ ✓ ] 5. Execute (Supervisor manages rate limit)
       supervisor.execute_with_grant(
         grant_id=grant_id,
         command="curl https://api.example.com/data/users?page=2",
         respect_rate_limit=true
       )
       
       If rate limit hit:
         → Supervisor auto-backoffs (exponential)
         → Retries when quota available
         → Returns result when successful
```

### 5.6 Hard Rules (Non-Negotiable)

| Rule | Why | Consequence |
|------|-----|-------------|
| Never hardcode secrets | Audit trail exposes it | Incident + human review |
| Never guess credentials | Brute force detection | Keyman auto-denies future requests |
| Never write secrets to disk | Violates Rule 0 | Agent sandbox termination |
| Never retry on denial | Indicates circumvention attempt | Permission revocation |
| Never batch tokens/grants | TTL isolation enforced | Grant expiry forces re-request |
| Never ignore audit events | Breaks immutability | Human investigation + escalation |

### 5.7 Token Budget (Context Efficiency)

**Goal:** Secrets management shouldn't blow up your context window.

**Efficient Pattern:**
- Request grant: ~500 tokens
- Use grant_id: ~50 tokens
- **Total:** ~550 tokens

**Vs. Inefficient Pattern:**
- Hardcode key: 200 tokens
- JWT parse: 300 tokens
- Refresh logic: 400 tokens
- **Total:** 900 tokens ❌

**Budget Breakdown (per request/response cycle):**
```
Max context: ~4,000 tokens
  - Ledger checklist: 200-300 tokens
  - Supervisor request: 100-150 tokens
  - Grant handling: 50-100 tokens
  - Actual work: 3,000-3,500 tokens

✅ Safe within budget
❌ Avoid: Complex token refresh loops (400+ tokens wasted)
```

### 5.8 Emergency Escalation

**When:** Governance rules are ambiguous or impossible

```python
def escalate_to_human():
    supervisor.escalate(
        severity="medium",  # low, medium, high, critical
        category="governance_ambiguity",
        message="Situation not covered by secret.md. Waiting for human decision.",
        context={
            "current_task": task_id,
            "issue": "description of ambiguity",
            "ledger_checksum": "sha256(secret.md)"
        }
    )
    
    # Agent pauses
    # Human reviews + responds
    # Agent resumes
```

---

## 6. Deployment & Operations

### 6.1 Initial Deployment

**Step 1: Run Installer**
```bash
sudo bash /home/wilgner/UnifAI/installer.sh
```

**Expected Output:**
```
[INFO] Starting UnifAI Native Installation Sequence
[INFO] Installation prefix: /opt/unifai
[INFO] Python version: 3.10
[INFO] Node version: 18
[✓] Phase 0: System dependencies installed
[✓] Phase 1: supervisor-secretvault installed and service registered
[✓] Phase 2: Python environment ready at /opt/unifai/venv
[✓] Phase 3: Keyman installed and service registered
[✓] Phase 4: Supervisor installed and service registered
[✓] Phase 5: OpenClaw installed and service registered
[✓] Phase 6: LLM local integration configured
[✓] Phase 7: User setup complete
[✓] Phase 8: Installation complete
```

**Duration:** 20-25 minutes

**Step 2: Start Services**
```bash
sudo systemctl start unifai-secretvault
sudo systemctl start unifai-keyman
sudo systemctl start unifai-supervisor
sudo systemctl start unifai-openclaw
```

**Step 3: Enable Auto-Start**
```bash
sudo systemctl enable unifai-secretvault
sudo systemctl enable unifai-keyman
sudo systemctl enable unifai-supervisor
sudo systemctl enable unifai-openclaw
```

**Step 4: Verify Services Running**
```bash
sudo systemctl status unifai-*
```

**Expected Status:**
```
● unifai-secretvault.service - UnifAI Secret Vault Service
     Loaded: loaded (/etc/systemd/system/unifai-secretvault.service; enabled; preset: enabled)
     Active: active (running) since Wed 2026-04-22 12:00:00 UTC; 2min 15s ago

● unifai-keyman.service - UnifAI Keyman Service (Authorization)
     Loaded: loaded (/etc/systemd/system/unifai-keyman.service; enabled; preset: enabled)
     Active: active (running) since Wed 2026-04-22 12:00:15 UTC; 2min ago

● unifai-supervisor.service - UnifAI Supervisor Service (Agent Orchestration)
     Loaded: loaded (/etc/systemd/system/unifai-supervisor.service; enabled; preset: enabled)
     Active: active (running) since Wed 2026-04-22 12:00:30 UTC; 1min 45s ago

● unifai-openclaw.service - UnifAI OpenClaw Service
     Loaded: loaded (/etc/systemd/system/unifai-openclaw.service; enabled; preset: enabled)
     Active: active (running) since Wed 2026-04-22 12:00:45 UTC; 1min 30s ago
```

### 6.2 Operational Monitoring

#### **Service Health Check**

```bash
#!/bin/bash
# health_check.sh

SERVICES=(
    "unifai-secretvault"
    "unifai-keyman"
    "unifai-supervisor"
    "unifai-openclaw"
)

echo "=== UnifAI Service Health Check ==="
for service in "${SERVICES[@]}"; do
    if systemctl is-active --quiet $service; then
        echo "✓ $service: RUNNING"
    else
        echo "✗ $service: STOPPED"
    fi
done

echo ""
echo "=== Port Availability ==="
for port in 5002 5001 5000 3000; do
    if nc -zv localhost $port &>/dev/null; then
        echo "✓ Port $port: LISTENING"
    else
        echo "✗ Port $port: NOT LISTENING"
    fi
done
```

#### **Log Monitoring**

```bash
# Real-time logs for all services
sudo journalctl -u unifai-* -f

# Logs for specific service
sudo journalctl -u unifai-supervisor -f

# Last 100 lines
sudo journalctl -u unifai-supervisor -n 100

# Logs since last hour
sudo journalctl -u unifai-supervisor --since "1 hour ago"

# Error level only
sudo journalctl -u unifai-supervisor -p err
```

#### **Audit Trail**

```bash
# View audit trail (immutable grant log)
tail -f /var/log/unifai/audit_trail.jsonl

# Search for specific grant
grep "grant_abc123" /var/log/unifai/audit_trail.jsonl

# Search for denied grants
grep '"status":"denied"' /var/log/unifai/audit_trail.jsonl
```

### 6.3 Service Management

#### **Restart Single Service**
```bash
sudo systemctl restart unifai-supervisor
```

#### **Stop All Services**
```bash
sudo systemctl stop unifai-*
```

#### **View Service Configuration**
```bash
sudo cat /etc/systemd/system/unifai-supervisor.service
```

#### **Update Service (after code changes)**
```bash
# For Node.js services (SecretVault, OpenClaw)
cd /opt/unifai/supervisor-secretvault
git pull origin main
npm install
sudo systemctl restart unifai-secretvault

# For Python services (Keyman, Supervisor)
cd /opt/unifai/keyman
source /opt/unifai/venv/bin/activate
git pull origin main
pip install -r requirements.txt
deactivate
sudo systemctl restart unifai-keyman
```

### 6.4 Backup & Recovery

#### **Backup Configuration**
```bash
# Backup all configuration
sudo tar -czf unifai-backup-$(date +%Y%m%d).tar.gz \
    /opt/unifai \
    /var/log/unifai \
    /etc/systemd/system/unifai-*.service

# Save to external storage
cp unifai-backup-*.tar.gz /mnt/backup/
```

#### **Restore from Backup**
```bash
# Stop services
sudo systemctl stop unifai-*

# Restore backup
sudo tar -xzf unifai-backup-20260422.tar.gz -C /

# Restart services
sudo systemctl start unifai-*
```

### 6.5 Updating Services

#### **Update All Services**
```bash
#!/bin/bash
# update_all_services.sh

SERVICES=(
    "supervisor-secretvault"
    "keyman"
    "supervisor"
    "openclaw"
)

echo "Updating all UnifAI services..."

for service in "${SERVICES[@]}"; do
    echo ""
    echo "=== Updating $service ==="
    cd /opt/unifai/$service
    
    if [[ -f "package.json" ]]; then
        git pull origin main
        npm install
        sudo systemctl restart unifai-${service%-*}
    elif [[ -f "requirements.txt" ]]; then
        source /opt/unifai/venv/bin/activate
        git pull origin main
        pip install -r requirements.txt
        deactivate
        sudo systemctl restart unifai-${service%-*}
    fi
done

echo ""
echo "All services updated and restarted!"
```

---

## 7. Security Model

### 7.1 Architecture Principles

**Principle 1: Defense in Depth**
```
Layer 1: Service boundary (only localhost:port accessible)
Layer 2: Grant-based authorization (Keyman evaluates requests)
Layer 3: TTL expiry (grants auto-expire)
Layer 4: Subprocess isolation (secrets injected only at spawn)
Layer 5: Audit trail (all operations immutably logged)
```

**Principle 2: Zero Trust for Agents**
```
Assumption: Any agent could be compromised.

Response:
  • Never trust agent to handle secrets
  • Require explicit grant for each capability
  • Enforce tight TTLs (5-30 minutes)
  • Narrow scopes (never wildcard *)
  • Audit every request (even denials)
```

**Principle 3: Separation of Concerns**
```
Component       Responsibility
────────────────────────────────────────────
SecretVault     Custody of raw secrets
Keyman          Authorization decisions
Supervisor      Grant enforcement + injection
Agent           Task execution (no secrets)
```

### 7.2 Threat Model

#### **Threat 1: Agent Exfiltration**

**Attack:** Rogue agent tries to steal API keys

**Mitigation:**
- ✅ Agent NEVER receives real secret (only grant_id)
- ✅ Secret injected into subprocess, not parent
- ✅ Subprocess stdout/stderr redacted (secret never in logs)
- ✅ Grant TTL ensures limited access window

**Result:** Attack FAILS. Agent cannot access secret.

#### **Threat 2: Permission Escalation**

**Attack:** Agent requests admin-only capability

**Mitigation:**
- ✅ Keyman enforces RBAC (agent role is read-only)
- ✅ Denial is logged + escalated to human
- ✅ Retry attempts are detected (brute force prevention)
- ✅ Human approval required for role elevation

**Result:** Attack BLOCKED. Request denied, escalated.

#### **Threat 3: Timing Attack**

**Attack:** Agent makes rapid requests to brute-force capability names

**Mitigation:**
- ✅ Request rate limiting (Keyman throttles)
- ✅ All attempts logged (audit trail)
- ✅ Suspicious patterns trigger human review
- ✅ IP/agent_id banned after N failures

**Result:** Attack DETECTED. Agent sandboxed.

#### **Threat 4: Audit Trail Tampering**

**Attack:** Compromised service tries to modify logs

**Mitigation:**
- ✅ Audit trail stored in immutable append-only file (jsonl)
- ✅ Checksums validate log integrity
- ✅ Regular backups to external storage
- ✅ Human review of deletions

**Result:** Tampering DETECTED. Incident created.

### 7.3 Cryptographic Practices

**Secret Storage:**
```
SecretVault stores secrets in:
  • File system with 0600 permissions (read-only by unifai user)
  • Encrypted at rest (using system keyring)
  • Checksummed (SHA256) for integrity
  • Versioned (old versions retained for audit)
```

**Grant Creation:**
```
Keyman creates grants with:
  • Cryptographically random grant_id (UUID v4)
  • Timestamp (when created)
  • TTL (absolute expiry)
  • HMAC-SHA256 signature (verify grant not tampered with)
```

**Audit Trail:**
```
Supervisor logs to JSONL:
  {
    "timestamp": "2026-04-22T12:00:00Z",
    "grant_id": "grant_abc123xyz",
    "agent_id": "agent-12345",
    "capability": "gcp_artifact_registry_push",
    "scope": "projects/my-project/*",
    "result": "success",
    "duration_ms": 45000,
    "hash_prev": "abc123...",  ← Links to previous entry
    "hash_current": "def456..."  ← Current entry hash
  }
```

### 7.4 Compliance & Auditing

**RBAC (Role-Based Access Control)**

```
Agent Roles:
  • read_only
    - Can list resources
    - Cannot modify anything
  
  • developer
    - read_only + write to dev/staging
    - Cannot access production
  
  • devops
    - developer + write to production
    - Requires human approval for high-risk ops
  
  • admin
    - All capabilities
    - Highest audit threshold

Capability Mapping:
  read_only       → [list_*, get_*]
  developer       → [read_only, create_dev_*, update_staging_*]
  devops          → [developer, create_prod_*, delete_*]
  admin           → [all]
```

**Audit Requirements**

```
Every audit entry must contain:
  ✓ timestamp (ISO 8601)
  ✓ agent_id (who made request)
  ✓ capability (what was requested)
  ✓ scope (resource limit)
  ✓ result (success/denied/error)
  ✓ duration (how long)
  ✓ justification (why was it needed)
  ✓ linked_hash (prev entry hash for chain integrity)

Compliance Checks:
  • Denied requests ≥ 5% → automatic human review
  • Grant TTL > 60 min → escalation required
  • Scope contains * → Keyman rejects
  • Agent rate > 100 req/min → throttle + alert
```

---

## 8. Troubleshooting

### 8.1 Common Issues

#### **Issue: Service fails to start**

**Symptom:**
```bash
$ sudo systemctl start unifai-supervisor
Job for unifai-supervisor.service failed because the control process exited with error code.
```

**Diagnosis:**
```bash
# Check service logs
sudo journalctl -u unifai-supervisor -n 50

# Check if port is already in use
sudo netstat -tlnp | grep 5000

# Check venv exists
ls -la /opt/unifai/venv/bin/python
```

**Solutions:**
```bash
# If port in use
sudo fuser -k 5000/tcp

# If venv missing, reinstall
python3.10 -m venv /opt/unifai/venv
source /opt/unifai/venv/bin/activate
pip install -r /opt/unifai/supervisor/requirements.txt
deactivate

# Restart service
sudo systemctl restart unifai-supervisor
```

#### **Issue: Agent cannot get grant from Keyman**

**Symptom:**
```
supervisor.request_grant() returns None
or
Keyman returns 403 Forbidden
```

**Diagnosis:**
```bash
# Check Keyman is running
sudo systemctl status unifai-keyman

# Check Keyman logs
sudo journalctl -u unifai-keyman -n 50

# Check network connectivity
curl http://localhost:5001/health

# Check agent role in Keyman database
sqlite3 /opt/unifai/keyman/db.sqlite3 \
  "SELECT * FROM agents WHERE id='agent-12345';"
```

**Solutions:**
```bash
# Restart Keyman
sudo systemctl restart unifai-keyman

# Check agent permissions
# Grant agent "developer" role
sqlite3 /opt/unifai/keyman/db.sqlite3 \
  "UPDATE agents SET role='developer' WHERE id='agent-12345';"

# Verify grant request is in correct format
# (check Keyman docs for API schema)
```

#### **Issue: Secret exposed in logs**

**Symptom:**
```
grep "my-secret-api-key" /var/log/unifai/*
Returns: "Found in supervisor.log"
```

**Diagnosis:**
```bash
# Check which service logged it
grep -n "my-secret-api-key" /var/log/unifai/*.log

# Check if it was subprocess output that should be redacted
grep -B 5 -A 5 "my-secret-api-key" /var/log/unifai/supervisor.log
```

**Solutions:**
```bash
# If subprocess output not redacted:
#   1. Check redact_output=true in execute_with_grant()
#   2. Verify Supervisor version (should have redaction)

# If subprocess output redacted but still visible:
#   1. Check if agent is logging subprocess output
#   2. Ensure all secret refs use grant_id pattern

# Immediate action:
#   1. Rotate the exposed secret
#   2. Create incident ticket
#   3. Review audit trail for who accessed it
```

### 8.2 Health Check Script

```bash
#!/bin/bash
# unifai_healthcheck.sh

set -euo pipefail

ERRORS=0

echo "=== UnifAI Health Check ==="
echo ""

# Check services
echo "[1/5] Checking services..."
for service in unifai-secretvault unifai-keyman unifai-supervisor unifai-openclaw; do
    if sudo systemctl is-active --quiet $service; then
        echo "  ✓ $service: RUNNING"
    else
        echo "  ✗ $service: STOPPED"
        ((ERRORS++))
    fi
done

echo ""

# Check ports
echo "[2/5] Checking ports..."
for port in 5002 5001 5000 3000; do
    if nc -zv localhost $port 2>/dev/null; then
        echo "  ✓ Port $port: LISTENING"
    else
        echo "  ✗ Port $port: NOT LISTENING"
        ((ERRORS++))
    fi
done

echo ""

# Check directories
echo "[3/5] Checking directories..."
for dir in /opt/unifai /var/log/unifai; do
    if [[ -d "$dir" ]]; then
        echo "  ✓ $dir: EXISTS"
    else
        echo "  ✗ $dir: MISSING"
        ((ERRORS++))
    fi
done

echo ""

# Check file permissions
echo "[4/5] Checking permissions..."
unifai_user=$(ls -l /opt/unifai | awk 'NR==2 {print $3}')
if [[ "$unifai_user" == "unifai" ]]; then
    echo "  ✓ /opt/unifai owner: unifai"
else
    echo "  ✗ /opt/unifai owner: $unifai_user (expected unifai)"
    ((ERRORS++))
fi

echo ""

# Check disk space
echo "[5/5] Checking disk space..."
free_space=$(df /opt/unifai | tail -1 | awk '{print $4}')
free_gb=$((free_space / 1024 / 1024))
if [[ $free_gb -gt 10 ]]; then
    echo "  ✓ Free space: ${free_gb}GB"
else
    echo "  ⚠ Free space: ${free_gb}GB (low)"
    ((ERRORS++))
fi

echo ""
echo "=== Summary ==="
if [[ $ERRORS -eq 0 ]]; then
    echo "✓ All checks passed!"
    exit 0
else
    echo "✗ $ERRORS checks failed"
    exit 1
fi
```

**Usage:**
```bash
bash unifai_healthcheck.sh
```

### 8.3 Log Rotation

**Setup log rotation to prevent disk full:**

```bash
sudo cat > /etc/logrotate.d/unifai << 'EOF'
/var/log/unifai/*.log
/var/log/unifai/*.jsonl
{
    daily
    rotate 7
    compress
    delaycompress
    missingok
    notifempty
    create 0640 unifai unifai
    sharedscripts
    postrotate
        sudo systemctl reload unifai-supervisor \
            unifai-keyman unifai-secretvault unifai-openclaw \
            2>/dev/null || true
    endscript
}
EOF
```

**Test log rotation:**
```bash
sudo logrotate -f /etc/logrotate.d/unifai
```

---

## 9. References & Advanced Topics

### 9.1 Repository Links

| Component | Repository | Branch |
|-----------|-----------|--------|
| supervisor-secretvault | github.com/joustonhuang/supervisor-secretvault | main |
| keyman | github.com/joustonhuang/keyman | main |
| supervisor | github.com/joustonhuang/supervisor | main |
| openclaw | github.com/openclaw/openclaw | main |

### 9.2 Documentation Files

| File | Purpose |
|------|---------|
| `/opt/unifai/supervisor-secretvault/README.md` | SecretVault setup & API |
| `/opt/unifai/keyman/README.md` | Keyman RBAC docs |
| `/opt/unifai/supervisor/README.md` | Supervisor orchestration |
| `/opt/unifai/.env` | Global environment config |
| `/home/wilgner/UnifAI/secret.md` | Governance Ledger (binding) |
| `/home/wilgner/UnifAI/installer.sh` | Installation automation |

### 9.3 CLI Commands

#### **Supervisor CLI**
```bash
# Request grant
supervisor request-grant --capability "gcp_artifact_registry" \
  --ttl-seconds 300 --scope "gcr.io/my-project/*" \
  --justification "Deploy service"

# Execute with grant
supervisor exec-with-grant --grant-id "grant_abc123" \
  --command "docker push gcr.io/my-project/service:v1.0"

# View audit trail
supervisor audit list --limit 100
supervisor audit view --grant-id "grant_abc123"
```

#### **Keyman CLI**
```bash
# Check agent permissions
keyman agent info --agent-id "agent-12345"

# Grant capability to agent
keyman grant capability --agent-id "agent-12345" \
  --capability "gcp_artifact_registry" --ttl-hours 24

# Revoke capability
keyman revoke capability --agent-id "agent-12345" \
  --capability "database_write"

# View RBAC rules
keyman rbac list
```

#### **SecretVault CLI**
```bash
# List secrets (metadata only, not values)
secret-vault list-secrets

# Create TTL-bound grant
secret-vault create-grant --secret-name "gcp-service-account" \
  --ttl-seconds 300

# View grants
secret-vault list-grants
```

### 9.4 Advanced Configurations

#### **Custom RBAC Roles**

Create new role in Keyman:
```bash
keyman role create --role-name "ci_pipeline" \
  --capabilities "[list_*, create_dev_*, update_staging_*]" \
  --ttl-hours 1 --rate-limit 1000
```

#### **Rate Limiting**

Configure per-agent rate limits:
```bash
keyman agent config --agent-id "agent-12345" \
  --rate-limit 100 --rate-window-seconds 60 \
  --concurrent-grants 5
```

#### **Backup Policy**

Automated backup of secrets:
```bash
cat > /opt/unifai/backup_secrets.sh << 'EOF'
#!/bin/bash
DATE=$(date +%Y%m%d)
secret-vault backup --output /mnt/backup/secrets-$DATE.tar.gz
gpg --encrypt /mnt/backup/secrets-$DATE.tar.gz
shred -f /mnt/backup/secrets-$DATE.tar.gz
EOF

sudo crontab -e
# Add: 0 2 * * * bash /opt/unifai/backup_secrets.sh
```

### 9.5 Performance Tuning

#### **Concurrency**

Increase concurrent grants:
```bash
sudo vi /opt/unifai/keyman/config.yaml
# Set: max_concurrent_grants: 50

sudo systemctl restart unifai-keyman
```

#### **Caching**

Enable Supervisor caching:
```bash
sudo vi /opt/unifai/supervisor/config.yaml
# Set: cache_ttl_seconds: 60
# Set: cache_max_size: 1000

sudo systemctl restart unifai-supervisor
```

#### **Resource Limits**

Configure service resource limits:
```bash
sudo mkdir -p /etc/systemd/system/unifai-supervisor.service.d

cat > /etc/systemd/system/unifai-supervisor.service.d/override.conf << EOF
[Service]
MemoryLimit=2G
CPUQuota=50%
TasksMax=100
EOF

sudo systemctl daemon-reload
sudo systemctl restart unifai-supervisor
```

### 9.6 Integration Examples

#### **GitHub Actions Integration**

Use UnifAI in CI/CD:
```yaml
name: Deploy with UnifAI

on: [push]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Request deployment grant
        run: |
          curl -X POST http://unifai-supervisor.internal:5000/request-grant \
            -H "Content-Type: application/json" \
            -d '{
              "capability": "gcp_artifact_registry",
              "task_id": "${{ github.sha }}",
              "ttl_seconds": 300,
              "scope": "gcr.io/my-project/*",
              "justification": "Deploy commit ${{ github.sha }}"
            }' > grant.json
      
      - name: Deploy with grant
        env:
          GRANT_ID: ${{ fromJson(grant.json).grant_id }}
        run: |
          supervisor exec-with-grant \
            --grant-id "$GRANT_ID" \
            --command "docker push ..." \
            --redact-output
```

#### **Terraform Integration**

Provision UnifAI on OpenStack:
```hcl
resource "openstack_compute_instance_v2" "unifai" {
  name            = "unifai-vm"
  image_name      = "Ubuntu-22.04"
  flavor_name     = "m1.large"
  
  user_data = <<-EOF
              #!/bin/bash
              sudo bash /root/installer.sh
              EOF
  
  tags = ["unifai", "governance"]
}
```

### 9.7 Disaster Recovery

**Scenario: SecretVault service crashes**

```bash
# 1. Stop dependent services
sudo systemctl stop unifai-keyman unifai-supervisor

# 2. Check SecretVault status
sudo systemctl status unifai-secretvault

# 3. Restore from backup
sudo tar -xzf /mnt/backup/secretvault-backup.tar.gz -C /opt/unifai/

# 4. Start SecretVault
sudo systemctl start unifai-secretvault

# 5. Verify recovery
curl http://localhost:5002/health

# 6. Restart dependent services
sudo systemctl start unifai-keyman unifai-supervisor

# 7. Verify audit trail
sudo journalctl -u unifai-secretvault -n 50
```

### 9.8 Glossary

| Term | Definition |
|------|-----------|
| **Grant** | Ephemeral capability reference (grant_id) issued by Keyman |
| **TTL** | Time-To-Live (seconds until grant expires) |
| **RBAC** | Role-Based Access Control (agent roles determine capabilities) |
| **Scope** | Resource boundary (e.g., `gcr.io/my-project/*`) |
| **Audit Trail** | Immutable log of all grant requests/denials |
| **Rule 0** | Secret Sovereignty (agents never possess secrets) |
| **Ledger** | Governance checklist agents must follow before action |
| **Injection** | Supervisor injects real secret into subprocess at runtime |
| **Redaction** | Automatic removal of secrets from logs |
| **Escalation** | Human approval required for denied or ambiguous requests |

### 9.9 Contact & Support

**Architecture Questions:**
- Jouston Huang (@jouston on GitHub)
- Architecture documentation: `/home/wilgner/UnifAI/MAPA_TECNICO_ARQUITETURAL.md`

**Implementation Support:**
- Wilgner Lucas (@wilgner on GitHub)
- Implementation branch: `feat/vm-native-installer-sequence`

**Security Issues:**
- Report to: security@unifai.local (confidential)
- Do not open public issues for security vulnerabilities

---

## 📋 Document Control

**Document:** UnifAI VM-Native Installation & Governance Implementation Guide  
**Version:** 1.0  
**Date:** 2026-04-22  
**Last Updated:** 2026-04-22  
**Next Review:** 2026-05-22  
**Author:** Wilgner Lucas  
**Maintainer:** Jouston Huang (Chief Architect)

**Changelog:**
| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-04-22 | Initial documentation |

---

**END OF IMPLEMENTATION GUIDE**

This document is AUTHORITATIVE for UnifAI infrastructure deployment and operations.
All team members must follow these procedures for consistency and security.
