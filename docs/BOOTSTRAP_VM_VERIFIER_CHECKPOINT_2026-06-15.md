# Bootstrap VM Verifier Checkpoint — 2026-06-15

## Branch
- Working branch: `fix/openclaw-config-path-and-local-mode`
- GitHub-visible branch head: `5baa4b0`
- Latest local head in the stack: `aa8cd7b`
- Latest non-doc logic head in the local stack: `03d08af`
- Local branch state at checkpoint: ahead by 33 commits over the GitHub-visible branch head

## Local commit stack after `5baa4b0`
1. `d8c9143` — `dev: add GitHub branch visibility check`
2. `517332a` — `dev: add GitHub check gate inspector`
3. `3063370` — `dev: fold check gate inspector into preflight`
4. `48bc63e` — `docs: clarify verifier preflight flow`
5. `3f57e39` — `scripts: add vm verifier preflight wrapper`
6. `588eb85` — `scripts: relax verifier preflight ref handling`
7. `e85623d` — `tests: guard verifier preflight wrapper contract`
8. `ab2a7b2` — `tests: smoke test verifier preflight wrapper`
9. `d18e5ff` — `docs: checkpoint vm verifier branch state`
10. `d0551e5` — `ci: pin bootstrap preflight actions to node24-safe majors`
11. `b5c3210` — `docs: refresh vm verifier checkpoint state`
12. `e724750` — `tests: smoke test github branch visibility gate`
13. `87b553a` — `docs: refresh verifier checkpoint after guardrail updates`
14. `70709d3` — `tests: lock bootstrap preflight contract`
15. `d013011` — `tests: smoke test github check gate`
16. `1cb116d` — `tests: harden github check gate diagnostics`
17. `9f238a4` — `docs: refresh vm verifier publish boundary`
18. `b29f575` — `scripts: fail fast on local-only verifier refs`
19. `3f1688c` — `docs: note local-only ref preflight guard`
20. `82b6f43` — `tests: lock verifier preflight wrapper into bootstrap contract`
21. `7e54422` — `tests: lock workflow guard steps into contract`
22. `d91ab00` — `tests: harden verifier tcg fallback path`
23. `1be4456` — `tests: cover vm host readiness helper`
24. `f9f0b25` — `docs: refresh vm verifier checkpoint state`
25. `2debfb0` — `docs: sync vm verifier boundary guidance`
26. `54e3760` — `docs: refresh vm verifier publish state`
27. `2b31af0` — `tests: harden vm verifier failure diagnostics`
28. `376062b` — `tests: cover vm verifier remote failure excerpts`
29. `f24a91a` — `docs: refresh vm verifier checkpoint state`
30. `03d08af` — `tests: cover missing vm report on verifier failure`
31. `5b132f5` — `docs: refresh vm verifier checkpoint state`
32. `aa8cd7b` — `docs: refresh vm verifier checkpoint state`

## What is now true locally
- Bootstrap installer preflight remains green.
- The bootstrap-preflight workflow itself is now pinned to Node24-safe GitHub Action majors (`actions/checkout@v5`, `actions/setup-python@v6`, `actions/upload-artifact@v5`), and the workflow contract checker now fails locally if those pins drift.
- Bootstrap installer preflight now also smoke-tests the GitHub branch-visibility helper in a temporary repo, so the “is this branch actually GitHub-visible?” gate no longer relies on syntax-only coverage.
- Bootstrap installer preflight now has its own explicit contract checker and an offline smoke test for the GitHub check-gate inspector, so the preflight scaffold and required-check diagnosis path are both self-tested instead of syntax-only guarded.
- The GitHub check-gate inspector is now more resilient on busy commits: it paginates through check runs and annotations, still prioritizes the likely root failure signal, and caps noisy annotation dumps with an omission summary.
- The check-gate hardening bundle is now preserved as a clean local commit instead of only a dirty working tree, so the publish boundary is sharper and less likely to be lost or restaged incorrectly when GitHub visibility opens.
- Live host-readiness has improved since the older missing-QEMU note: the required verifier tools are present on this host, and the current warnings are narrower (`/dev/kvm` not writable, `gh` installed but unauthenticated, no `GH_TOKEN`/`GITHUB_TOKEN` exported).
- The verifier path now has three distinct local guard layers before VM boot:
  1. branch visibility check
  2. GitHub required-check gate inspection
  3. one-command wrapper for the common preflight flow
- The wrapper is protected by:
  - syntax checking in bootstrap preflight
  - a contract checker (`scripts/check_vm_verifier_preflight_contract.py`)
  - a dry-run smoke test (`scripts/smoke_test_vm_verifier_preflight_wrapper.sh`)
- The verifier/preflight stack now has fail-closed smoke coverage for:
  - GitHub branch visibility divergence
  - GitHub required-check success/failure inspection with annotations
  - forced red-path failure
  - GitHub fallback SHA-resolution failure
  - SSH-never-ready excerpt surfacing from serial/qemu logs
  - remote-verification failure excerpt surfacing from installer/report/serial/qemu logs
  - remote-verification failure when `report.txt` cannot be copied back from the VM
- Bootstrap installer preflight now also executes two more realistic local verifier-environment probes instead of only syntax-checking them:
  - a forced-TCG launch smoke path for `scripts/vm/verify_bootstrap_in_vm.sh`
  - a host-readiness helper smoke test for `scripts/check_vm_host_readiness.sh`
- The current local hardening stack is preserved as clean commits through `aa8cd7b`, rather than as an uncommitted sandbox delta.

## Known real blocker
- First real VM proof still cannot start from this branch until these local commits become GitHub-visible.
- The last GitHub-visible ref tested was `5baa4b0`, and its required check `Bootstrap Installer Preflight` was red, so verifier execution stopped before VM boot.
- A fresh gate check on 2026-06-17 still shows `5baa4b0` red: `Bootstrap Installer Preflight` failed at https://github.com/joustonhuang/unifai/actions/runs/27492489483/job/81260207531. The public workflow still pins Node20-era actions (`actions/checkout@v4`, `actions/setup-python@v5`, `actions/upload-artifact@v4`), and the failing annotation summary surfaces those deprecation warnings alongside a generic `Process completed with exit code 1` marker.
- `main` has moved independently since that public branch head, but that does not change the current blocker: the verifier boundary is still GitHub visibility plus a green required-check gate on the exact visible ref you plan to boot.
- Once the branch is visible, the first likely execution friction is host-side, not code-side: `/dev/kvm` is present but not writable on this host so the verifier will run in slower TCG mode, and `gh` is installed but unauthenticated with no `GH_TOKEN`/`GITHUB_TOKEN` exported, so the API gate may fail closed or rate-limit.

## Recommended next move when external boundary opens
1. Make the current local branch tip GitHub-visible (the latest non-doc logic commit in that tip is `03d08af`).
2. Run:
   ```bash
   bash scripts/run_vm_verifier_preflight.sh <github-visible-ref>
   ```
3. If preflight reports a red required check, inspect it first with:
   ```bash
   python3 scripts/check_github_check_gate.py <github-visible-ref>
   ```
4. If preflight passes, run:
   ```bash
   bash scripts/vm/verify_bootstrap_in_vm.sh <github-visible-ref>
   ```
5. If verifier startup friction appears immediately, check host readiness first with:
   ```bash
   bash scripts/check_vm_host_readiness.sh
   ```

## Why this checkpoint exists
This branch now contains several small local hardening commits. The main risk is not code uncertainty but restart friction and losing the verified sequence. This note preserves the exact branch state and next action boundary.
