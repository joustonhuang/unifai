# Bootstrap VM Verifier Checkpoint — 2026-06-15

## Branch
- Working branch: `transplant/fix-openclaw-config-path-and-local-mode-clean-stack`
- GitHub-visible branch head: `ccda045`
- Latest tracked local head in the stack: `3c159fe`
- Latest non-doc logic head in the local stack: `3c159fe`
- Tracked local branch state at checkpoint: ahead by 33 commits over the GitHub-visible branch head

## Local commit stack after `5baa4b0`
1. `2c75337` — `scripts: check publish stack parity`
2. `75577aa` — `tests: allow local cleanup branch preflight refs`
3. `47c18d7` — `scripts/docs: refresh vm verifier checkpoint state`
4. `5837f8c` — `tests: restore no-github-remote preflight smoke`
5. `c867fa3` — `dev: harden verifier preflight remote boundary`
6. `22b7bc9` — `scripts: harden verifier publish boundary`
7. `d0488d4` — `tests: cover non-github check-gate refs`
8. `de9b247` — `tests: cover secondary check-gate rate limits`
9. `e26db83` — `scripts: compare publish branch histories`
10. `d3b15a7` — `docs: refresh verifier checkpoint state`
11. `a16bb5f` — `scripts: clarify checkpoint tip drift`
12. `a6d8e52` — `docs: refresh verifier checkpoint stack`
13. `4e233df` — `docs: record checkpoint doc-only tip`
14. `05b564a` — `scripts: keep checkpoint docs stable`
15. `9ff53af` — `docs: refresh verifier checkpoint state`
16. `3e8eb9b` — `scripts: clarify doc-only publish boundary handoff`
17. `1acded9` — `docs: refresh verifier checkpoint state`
18. `e6c2390` — `scripts: clarify branch visibility recovery guidance`
19. `1f167d8` — `docs: refresh verifier checkpoint state`
20. `6b715c9` — `scripts/docs: track live checkpoint branch name`
21. `da5438a` — `scripts: print explicit publish-history review buckets`
22. `848004e` — `scripts: show publish-history review paths`
23. `530c9d0` — `docs: capture publish branch review queue`
24. `89c892d` — `docs: shrink publish branch review queue`
25. `f5a023a` — `docs: trim publish branch mixed review queue`
26. `09ffd8c` — `docs: reduce publish branch mixed review queue`
27. `a2151e4` — `docs: finish mixed publish branch review queue`
28. `0ba2ec4` — `docs: mark legacy publish docs as drop candidates`
29. `e354075` — `scripts: clarify doc-only reconciliation end state`
30. `8d1aace` — `scripts: suppress reviewed legacy publish history`
31. `e771a87` — `scripts/docs: preserve publish-boundary maintenance bundle`
32. `595bee8` — `docs: refresh verifier checkpoint after bundle commit`
33. `3c159fe` — `scripts: respect tracked github visibility branch`
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
- The current local hardening stack has moved well beyond that earlier nine-commit checkpoint chain on top of the GitHub-visible branch: the latest tracked commit is now `3c159fe`, that same commit is also the latest non-doc logic head, the sandbox currently carries 2 uncommitted publish-boundary maintenance updates, and the branch is `ahead 33` over `github/fix/openclaw-config-path-and-local-mode`.
- The verifier no longer drops installer-phase VM failures on the floor: installer errors now emit the evidence bundle path plus installer-output, serial-log, and qemu-log excerpts, and that path is covered by a dedicated local smoke test.
- Bootstrap preflight now locks that installer-failure path into its own required coverage, so future verifier edits cannot silently drop it while still appearing preflight-green.
- The current local sandbox now carries 2 uncommitted publish-boundary maintenance updates beyond the tracked local stack:
  - `docs/BOOTSTRAP_VM_VERIFICATION.md`
  - `docs/BOOTSTRAP_VM_VERIFIER_CHECKPOINT_2026-06-15.md`
- Fresh local verification at the current sandbox state is green again:
  - `python3 scripts/check_publish_stack_parity_contract.py`
  - `python3 scripts/check_compare_publish_branch_histories_contract.py`
  - `python3 scripts/check_vm_verifier_checkpoint_refresh_contract.py`
  - `python3 scripts/check_vm_host_readiness_contract.py`
  - `bash scripts/smoke_test_publish_stack_parity.sh`
  - `bash scripts/smoke_test_compare_publish_branch_histories.sh`
  - `python3 -B scripts/smoke_test_vm_verifier_checkpoint_refresh.py`
  - `bash scripts/bootstrap_installer_preflight.sh` (rerun with the publish-boundary maintenance bundle in place)
