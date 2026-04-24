# Bootstrap VM Verification

This repo now uses a two-layer verification approach for the bootstrap installer path.

## Layer 1: GitHub Actions preflight

Workflow:
- `.github/workflows/bootstrap-preflight.yml`

Purpose:
- fail fast on obvious installer/bootstrap regressions
- validate installer syntax and stage syntax
- validate the existing `little7-installer/install.sh verify` contract
- verify that the PoC bootstrap installer still declares the expected service boundary

This layer is cheap and repeatable.
It is not proof that a fresh VM really boots the stack.

## Layer 2: Local fresh-VM verification

Script:
- `scripts/vm/verify_bootstrap_in_vm.sh <git-ref-or-sha>`

Purpose:
- boot a fresh VM
- clone the target commit from GitHub
- run `sudo bash installer.sh`
- capture service status and basic endpoint evidence

## Hard gate

The VM verification script refuses to start unless the target commit has these GitHub checks green:
- `Bootstrap Installer Preflight`
- `Core Modules & Exoskeleton E2E`
- `smoke-test`

This prevents expensive VM runs on commits that are already known-bad.

## Required local tools for VM verification

The local VM verifier expects:
- `gh`
- `jq`
- `curl`
- `qemu-system-x86_64`
- `qemu-img`
- `cloud-localds`
- `ssh`
- `ssh-keygen`
- `timeout`

Typical Debian/Ubuntu packages:
- `qemu-system-x86`
- `qemu-utils`
- `cloud-image-utils`
- `openssh-client`
- `jq`
- `gh`

## Example

```bash
bash scripts/vm/verify_bootstrap_in_vm.sh main
```

Or for a specific commit:

```bash
bash scripts/vm/verify_bootstrap_in_vm.sh <commit-sha>
```

## Output

The verifier writes an evidence bundle under:
- `/srv/unifai-vm-checks/unifai-bootstrap-check/`

Expected artifacts include:
- VM serial log
- installer stdout/stderr capture
- service status report
- basic endpoint probe output

## Intent

This is not final installer architecture.
It is the validation scaffold for the current bootstrap PoC:
- CI catches obvious regressions early
- a real VM tells us whether the bootstrap actually boots the stack
