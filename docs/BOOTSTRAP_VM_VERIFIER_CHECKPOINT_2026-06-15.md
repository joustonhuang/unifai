# Bootstrap VM Verifier Checkpoint — 2026-06-15

## Branch
- Working branch: `transplant/fix-openclaw-config-path-and-local-mode-clean-stack`
- GitHub-visible branch head: `22560dc`
- Latest tracked local head in the stack: `517fb5a`
- Latest non-doc logic head in the local stack: `517fb5a`
- Tracked local branch state at checkpoint: ahead by 6 commits over the GitHub-visible branch head

## Local commit stack after `5baa4b0`
1. `f4946cd` — `vm: require scp before verifier report copyback`
2. `c3dd862` — `docs: refresh vm verifier checkpoint handoff`
3. `a11ed88` — `docs: stabilize vm verifier checkpoint state`
4. `368306a` — `docs: settle publish-boundary handoff state`
5. `b08bbca` — `docs: refresh vm verifier checkpoint state`
6. `517fb5a` — `Fail closed on stale visible verifier refs`
## What is now true locally
- Bootstrap installer preflight remains green.
- The bootstrap-preflight workflow itself is now pinned to Node24-safe GitHub Action majors (`actions/checkout@v5`, `actions/setup-python@v6`, `actions/upload-artifact@v5`), and the workflow contract checker now fails locally if those pins drift.
- Bootstrap installer preflight now also smoke-tests the GitHub branch-visibility helper in a temporary repo, so the “is this branch actually GitHub-visible?” gate no longer relies on syntax-only coverage.
- Bootstrap installer preflight now has its own explicit contract checker and an offline smoke test for the GitHub check-gate inspector, so the preflight scaffold and required-check diagnosis path are both self-tested instead of syntax-only guarded.
- The GitHub check-gate inspector is now more resilient on busy commits: it paginates through check runs and annotations, still prioritizes the likely root failure signal, and caps noisy annotation dumps with an omission summary.
- The verifier-preflight remote-boundary hardening bundle is now preserved as a clean local checkpoint commit: `7756061` (`dev: harden verifier preflight remote boundary`).
- Live host-readiness has improved since the older missing-QEMU note: the required verifier tools are present on this host, and the current live state is narrower (`/dev/kvm` is present but not writable, `gh` is installed and authenticated, no `GH_TOKEN`/`GITHUB_TOKEN` is exported).
- The verifier path now has three distinct local guard layers before VM boot:
  1. branch visibility check
  2. GitHub required-check gate inspection
  3. one-command wrapper for the common preflight flow
- The wrapper is protected by:
  - syntax checking in bootstrap preflight
  - a contract checker (`scripts/check_vm_verifier_preflight_contract.py`)
  - a dry-run smoke test (`scripts/smoke_test_vm_verifier_preflight_wrapper.sh`)
- The latest local hardening commit narrows one more mismatch between smoke coverage and real operator repos:
  - the preflight-wrapper smoke test now auto-detects the GitHub-backed remote instead of assuming a hard-coded `github` remote name
  - explicit local SHAs now have a dedicated fail-closed smoke path when no GitHub-backed remote can be detected at all
  - bootstrap preflight and its contract checkers now require that missing-GitHub-remote smoke path
  - the wrapper contract checker now also forbids the stale hard-coded smoke ref `github/fix/openclaw-config-path-and-local-mode`, so this exact GitHub-visible failure mode cannot quietly re-enter the local bundle
- Fresh local `bash scripts/bootstrap_installer_preflight.sh` reruns are green with the current publish-boundary maintenance bundle in place.
- `ci-artifacts/bootstrap-preflight/commit-candidate.txt` now captures the current local checkpoint, host-readiness snapshot, verification gates, and the exact next visible-ref move as a one-file handoff.
- The verifier/preflight stack now has fail-closed smoke coverage for:
  - GitHub branch visibility divergence
  - GitHub required-check success/failure inspection with annotations
  - forced red-path failure
  - GitHub fallback SHA-resolution failure
  - explicit local SHA preflight failure when no GitHub-backed remote exists
  - SSH-never-ready excerpt surfacing from serial/qemu logs
  - remote-verification failure excerpt surfacing from installer/report/serial/qemu logs
  - remote-verification failure when `report.txt` cannot be copied back from the VM
- Bootstrap installer preflight now also executes two more realistic local verifier-environment probes instead of only syntax-checking them:
  - a forced-TCG launch smoke path for `scripts/vm/verify_bootstrap_in_vm.sh`
  - a host-readiness helper smoke test for `scripts/check_vm_host_readiness.sh`
- The current local hardening stack has moved well beyond that earlier nine-commit checkpoint chain on top of the GitHub-visible branch: the latest tracked commit is now `517fb5a`, that same commit is also the latest non-doc logic head, the sandbox currently carries 1 uncommitted publish-boundary maintenance update, and the branch is `ahead 6` over `fix/openclaw-config-path-and-local-mode`.
- The verifier no longer drops installer-phase VM failures on the floor: installer errors now emit the evidence bundle path plus installer-output, serial-log, and qemu-log excerpts, and that path is covered by a dedicated local smoke test.
- Bootstrap preflight now locks that installer-failure path into its own required coverage, so future verifier edits cannot silently drop it while still appearing preflight-green.
- The current local sandbox now carries one small publish-boundary maintenance delta beyond the tracked local stack:
  - `docs/BOOTSTRAP_VM_VERIFIER_CHECKPOINT_2026-06-15.md`
- Fresh local verification at the current sandbox state is green again:
  - `python3 scripts/check_publish_stack_parity_contract.py`
  - `python3 scripts/check_publish_stack_reconciliation_note.py`
  - `python3 scripts/check_publish_stack_reconciliation_note_contract.py`
  - `python3 scripts/check_compare_publish_branch_histories_contract.py`
  - `python3 scripts/check_branch_reconcile_handoff.py`
  - `python3 scripts/check_branch_reconcile_handoff_contract.py`
  - `python3 scripts/check_github_branch_visibility_contract.py`
  - `python3 scripts/check_vm_verifier_checkpoint_freshness_contract.py`
  - `python3 scripts/check_vm_verifier_checkpoint_refresh_contract.py`
  - `python3 scripts/check_vm_host_readiness_contract.py`
  - `bash scripts/smoke_test_publish_stack_parity.sh`
  - `bash scripts/smoke_test_compare_publish_branch_histories.sh`
  - `bash scripts/smoke_test_publish_stack_reconciliation_note.sh`
  - `bash scripts/smoke_test_branch_reconcile_handoff.sh`
  - `python3 -B scripts/smoke_test_vm_verifier_checkpoint_freshness.py`
  - `python3 -B scripts/smoke_test_vm_verifier_checkpoint_refresh.py`
  - `bash scripts/bootstrap_installer_preflight.sh` (rerun with the publish-boundary maintenance bundle in place)
