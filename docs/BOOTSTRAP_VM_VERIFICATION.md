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
- syntax-check the VM verifier itself as a first-class contract
- run cheap fail-closed smoke checks for the GitHub branch-visibility gate plus VM verifier red paths, including forced verification failure and GitHub API fallback SHA-resolution failure

This layer is cheap and repeatable.
It is not proof that a fresh VM really boots the stack.

Implementation note:
- `scripts/bootstrap_installer_preflight.sh` is the single local entrypoint for these cheap checks.
- The GitHub Actions workflow should invoke that preflight once and avoid re-running the same smoke tests separately.
- The local preflight now also syntax-checks `scripts/check_github_check_gate.py`, contract-checks `scripts/bootstrap_installer_preflight.sh`, contract-checks `scripts/check_bootstrap_workflow_contract.py` via `scripts/check_bootstrap_workflow_contract_contract.py`, smoke-tests `scripts/check_github_check_gate.py`, and smoke-tests `scripts/check_github_branch_visibility.sh`, so the workflow-contract, check-gate, preflight, and branch-visibility diagnosis paths stay under the same contract as the verifier.
- `scripts/check_bootstrap_preflight_contract.py` now asserts the broader real preflight surface too: required lock/config/verifier files, the Stage 50 and VM-verifier contract checkers, the VM verifier script path itself, and the GitHub-fallback / red-path smoke checks, so local contract drift gets caught before the next GitHub-visible run.
- `scripts/check_bootstrap_preflight_contract_contract.py` now contract-checks that checker too, so the local preflight cannot silently lose installer syntax/verify coverage, service-boundary assertions, or the Stage 50 OpenClaw installer grep.

## Layer 2: Local fresh-VM verification

Script:
- `scripts/vm/verify_bootstrap_in_vm.sh <git-ref-or-sha>`

Purpose:
- boot a fresh VM
- clone the target commit from GitHub
- run `sudo bash installer.sh`
- capture service status, OpenClaw runtime evidence, and secret-handling smoke evidence

## Hard gate

The VM verification script refuses to start unless the target commit has this GitHub check green:
- `Bootstrap Installer Preflight`

It also requires these checks to be green if they exist for the target commit:
- `Core Modules & Exoskeleton E2E`
- `smoke-test`

This prevents expensive VM runs on commits that are already known-bad while still allowing refs that do not emit every optional check.

## Required local tools for VM verification

The local VM verifier expects:
- `jq`
- `curl`
- `qemu-system-x86_64`
- `qemu-img`
- `cloud-localds`
- `ssh`
- `ssh-keygen`
- `timeout`

Quick host preflight:

```bash
bash scripts/check_vm_host_readiness.sh
```

That helper reports missing binaries, `/dev/kvm` readiness, and whether GitHub auth is likely to block the first live VM proof.

Quick branch / gate preflight before spending time on a VM run:

```bash
bash scripts/check_github_branch_visibility.sh
python3 scripts/check_github_check_gate.py <github-visible-ref>
```

Use the branch-visibility check first to confirm your local branch actually matches the GitHub-visible branch head. Use the check-gate inspector next when a visible ref is unexpectedly red; it prints the current required-check status, paginates through public check runs and annotations, highlights the likely root failure signal first, shows nearby source lines from the exact failing git ref when the annotation points at a tracked file, can fall back to hinted workflow files when GitHub only reports a directory-level path like `.github`, warns when GitHub only points at a generic shell control line such as `fi`, and caps noisy annotation dumps with an omission summary before you touch verifier logic.

If you want the common local sequence as one command, use:

```bash
bash scripts/run_vm_verifier_preflight.sh <github-visible-ref>
```

That wrapper now starts with `scripts/check_vm_host_readiness.sh`, so the common path surfaces local KVM / GitHub-auth friction before the deeper preflight and gate checks. It also fails fast if you pass a local-only commit SHA that is not reachable from any GitHub-visible branch, so you get the visibility boundary error before the later GitHub check-gate step.

`gh` is preferred when installed and authenticated, but the verifier can fall back to direct GitHub API calls via `curl` when `gh` is unavailable, when `gh` is installed but unauthenticated, or when `UNIFAI_VM_VERIFY_FORCE_NO_GH=1` is set for smoke testing.

For curl fallback authentication, the verifier accepts either:
- `GH_TOKEN`
- `GITHUB_TOKEN`

If neither is set, the verifier still fails closed when commit SHA resolution cannot be proven.

Typical Debian/Ubuntu packages:
- `qemu-system-x86`
- `qemu-utils`
- `cloud-image-utils`
- `openssh-client`
- `jq`
- `gh`

## Example

Default target image is now Ubuntu 22.04 LTS (Jammy):

```bash
bash scripts/vm/verify_bootstrap_in_vm.sh main
```

Or for a specific GitHub-visible commit:

```bash
bash scripts/vm/verify_bootstrap_in_vm.sh <commit-sha>
```

Recommended operator flow:

```bash
bash scripts/run_vm_verifier_preflight.sh <github-visible-ref>
bash scripts/vm/verify_bootstrap_in_vm.sh <github-visible-ref>
```

The verifier only accepts refs GitHub can resolve for this repo. If you point it at a local-only commit, it fails closed and tells you to push that commit first or use a GitHub-visible branch/ref.

Current known boundary on this branch family:
- GitHub-visible branch head remains `ccda045`
- the local hardening stack is currently ahead of that public ref through `2731fd3` (`scripts: narrow checkpoint host readiness wording`), 51 commits ahead in total
- the local sandbox currently carries no additional uncommitted publish-boundary maintenance delta
- the latest non-doc logic delta in that local stack is `2731fd3` (`scripts: narrow checkpoint host readiness wording`) in:
  - `docs/BOOTSTRAP_VM_VERIFICATION.md`
  - `docs/BOOTSTRAP_VM_VERIFIER_CHECKPOINT_2026-06-15.md`
  - `scripts/check_vm_verifier_checkpoint_refresh_contract.py`
  - `scripts/refresh_vm_verifier_checkpoint_state.py`
  - `scripts/smoke_test_vm_verifier_checkpoint_refresh.py`
- the local wrapper coverage also now proves `scripts/run_vm_verifier_preflight.sh` keeps explicit GitHub remote-tracking refs such as `refs/remotes/github/fix/openclaw-config-path-and-local-mode` intact through the dry-run preflight path and into `scripts/check_github_check_gate.py`
- that earlier check-gate ref-resolution hardening now resolves GitHub remote-tracking refs such as `github/fix/openclaw-config-path-and-local-mode` instead of failing immediately at the commit-SHA lookup path
- a fresh local `bash scripts/bootstrap_installer_preflight.sh` rerun is green with the current publish-boundary maintenance bundle in place
- `ci-artifacts/bootstrap-preflight/commit-candidate.txt` now captures the current local checkpoint, host-readiness snapshot, verification gates, and the exact next visible-ref move as a one-file handoff.
- first real VM proof should wait for the current local head to become GitHub-visible and for `Bootstrap Installer Preflight` to rerun green on that exact visible ref
- on the current host, `/dev/kvm` is present but not writable, `gh` is installed and authenticated, and no `GH_TOKEN`/`GITHUB_TOKEN` is exported, so the first live run should expect TCG fallback, while normal GitHub API reads should flow through authenticated `gh` unless the host state changes

Override the cloud image explicitly if needed:

```bash
IMAGE_URL=https://cloud-images.ubuntu.com/jammy/current/jammy-server-cloudimg-amd64.img \
  bash scripts/vm/verify_bootstrap_in_vm.sh main
```

## Output

The verifier writes an evidence bundle under:
- `/srv/unifai-vm-checks/unifai-bootstrap-check/` when `/srv` is writable
- otherwise `${XDG_CACHE_HOME:-$HOME/.cache}/unifai-vm-checks/unifai-bootstrap-check/`

Expected artifacts include:
- VM serial log
- QEMU launcher log (`qemu.log`)
- installer stdout/stderr capture
- service status report
- basic endpoint probe output
- OpenClaw socket / HTTP probe output
- secret leakage smoke-test result from inside the VM

When `/dev/kvm` is writable, the verifier uses KVM acceleration.
Otherwise it falls back to TCG emulation and logs that downgrade explicitly so host capability drift is visible in the evidence bundle.
For deterministic smoke tests, set `UNIFAI_VM_VERIFY_FORCE_TCG=1` to force the portable TCG launch path even on KVM-capable hosts.

## Intent

This is not final installer architecture.
It is the validation scaffold for the current bootstrap PoC:
- CI catches obvious regressions early
- a real VM tells us whether the bootstrap actually boots the stack
- the verifier now also checks that OpenClaw reaches a live runtime state and that the in-VM secret leakage smoke test still passes
- CI now also carries fail-closed smoke checks proving the verifier rejects both a forced verification failure and an unresolved GitHub commit SHA in fallback mode
- local smoke coverage now also proves installer-phase VM failures surface installer/serial/qemu evidence instead of disappearing behind `set -o pipefail`, and bootstrap preflight now directly exercises that smoke path too
