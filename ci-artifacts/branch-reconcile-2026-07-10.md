# Branch Reconcile Note — refreshed 2026-08-08 16:20 Asia/Taipei

## Current state

- `transplant/fix-openclaw-config-path-and-local-mode-clean-stack` is the cleaner publish candidate.
- `fix/openclaw-config-path-and-local-mode` still carries extra legacy local-only history, but that history is now fully accounted for as absorbed, patch-equivalent, or intentional doc-only drop noise.
- The latest non-handoff branch tip captured by this note is `f6f6de3`; later doc-only checkpoint or branch-reconcile-only handoff refreshes are intentionally ignored here so the handoff does not self-stale immediately on commit.
- The last non-doc tracked publish-boundary checkpoint remains `f6f6de3` until the current doc-only tip becomes GitHub-visible.
- Divergence count from `git rev-list --left-right --count fix/openclaw-config-path-and-local-mode...transplant/fix-openclaw-config-path-and-local-mode-clean-stack`:
  - `fix/openclaw-config-path-and-local-mode`: `18`
  - `transplant/fix-openclaw-config-path-and-local-mode-clean-stack`: `228`

## Transplant-only commits

```text
60a2219 docs: settle verifier checkpoint handoff wording
696b1ab docs: refresh verifier checkpoint handoff
93c2da9 tests: pin checkpoint freshness preflight coverage
fbbc5b8 tests: pin github check gate preflight coverage
659999f tests: pin branch visibility preflight coverage
5c50083 docs: settle checkpoint verification gates
cda64f0 docs: refresh checkpoint verification gates
acea8e8 scripts: track branch-visibility checkpoint gate
bd61860 docs: refresh branch reconcile handoff
9c32439 docs: settle host readiness contract coverage handoff
0160eb0 tests: harden vm host readiness contract coverage
32c0dc1 docs: settle token coverage handoff
889eeab docs: refresh verifier checkpoint after token coverage
68306e0 tests: cover GITHUB_TOKEN host-readiness fallback
11c76e0 docs: settle post-preflight handoff state
c0589e3 docs: refresh post-preflight handoff state
f839edd docs: stabilize verifier checkpoint handoff wording
254fd1a docs: refresh verifier checkpoint after handoff hardening
22b67ed scripts: harden verifier checkpoint handoff refresh
de9b247 tests: cover secondary check-gate rate limits
d0488d4 tests: cover non-github check-gate refs
848004e scripts: show publish-history review paths
da5438a scripts: print explicit publish-history review buckets
6b715c9 scripts/docs: track live checkpoint branch name
1f167d8 docs: refresh verifier checkpoint state
e6c2390 scripts: clarify branch visibility recovery guidance
1acded9 docs: refresh verifier checkpoint state
3e8eb9b scripts: clarify doc-only publish boundary handoff
9ff53af docs: refresh verifier checkpoint state
05b564a scripts: keep checkpoint docs stable
4e233df docs: record checkpoint doc-only tip
a6d8e52 docs: refresh verifier checkpoint stack
a16bb5f scripts: clarify checkpoint tip drift
d3b15a7 docs: refresh verifier checkpoint state
e26db83 scripts: compare publish branch histories
22b7bc9 scripts: harden verifier publish boundary
c867fa3 dev: harden verifier preflight remote boundary
5837f8c tests: restore no-github-remote preflight smoke
47c18d7 scripts/docs: refresh vm verifier checkpoint state
75577aa tests: allow local cleanup branch preflight refs
2c75337 scripts: check publish stack parity
```

## Older fix-branch-only commits

```text
aaee837 scripts/docs: refresh vm verifier checkpoint state
df91afa tests: allow local cleanup branch preflight refs
27c03a9 scripts: check publish stack parity
d70998f tests: cover secondary check-gate rate limits
77bd08b tests: cover non-github check-gate refs
8ee658e scripts: lock missing-remote preflight guidance
b07fbe1 scripts: cover default vm preflight ref path
d8539bb scripts: harden verifier publish boundary
9e2f0bf docs: sync verifier checkpoint narrative
7af8398 docs: refresh checkpoint helper state
d7e7152 docs: refresh checkpoint helper boundary
1836417 scripts: stabilize verifier checkpoint refresh tracking
4aa294f docs: refresh visible verifier checkpoint
f4232c5 docs: sync visible verifier boundary state
4996e4f docs: sync verifier publish boundary
0b062e3 docs: refresh verifier publish checkpoint
18f633f docs: refresh verifier publish checkpoint
7756061 dev: harden verifier preflight remote boundary
```

## Reconciliation readout

- Patch-equivalent older commits already covered on the transplant branch:
  - `77bd08b tests: cover non-github check-gate refs`
  - `d70998f tests: cover secondary check-gate rate limits`
  - `27c03a9 scripts: check publish stack parity`
- Older code-only commits already absorbed on the transplant branch:
  - `1836417 scripts: stabilize verifier checkpoint refresh tracking`
  - `b07fbe1 scripts: cover default vm preflight ref path`
  - `8ee658e scripts: lock missing-remote preflight guidance`
  - `df91afa tests: allow local cleanup branch preflight refs`
- Replay-safe code-only older commits still unique to `fix/...`: none.
- Older mixed docs+code commits still needing conscious keep/drop review: none.
- Older doc/checkpoint-only commits still needing conscious keep/drop review: none.

## Manual review queue

- Mixed docs+code older commits still needing conscious keep/drop review:
  - none
- Reviewed mixed docs+code older commits now ready to drop:
  - `7756061 dev: harden verifier preflight remote boundary`
    Functional coverage is already present on transplant via `c867fa3` for the preflight/GitHub-gate code path, `22b7bc9` for the later publish-boundary hardening, and `5837f8c` for the missing-remote smoke restoration. Remaining delta is checkpoint/doc churn, not missing behavior.
  - `f4232c5 docs: sync visible verifier boundary state`
    Its exact behavior is already represented and then extended on transplant: the checkpoint-refresh helper still rewrites the GitHub-visible head and tracked local head lines, the smoke test still asserts those synced boundary values, and later commits such as `05b564a`, `47c18d7`, and `6b715c9` broaden that same checkpoint/doc sync path substantially. Remaining delta is earlier wording/doc-state churn, not missing logic.
  - `d8539bb scripts: harden verifier publish boundary`
    Its behavior is already represented and extended on transplant: `22b7bc9` carries the GitHub check-gate hardening and smoke coverage forward, `a16bb5f` plus the later checkpoint-refresh chain keep the boundary/checkpoint narration in sync, and the current tree still contains the explicit remote-tracking-ref resolution and wrapper coverage that this older commit was trying to protect. The remaining delta is older checkpoint/doc wording and state capture, not missing functionality.
  - `aaee837 scripts/docs: refresh vm verifier checkpoint state`
    Its checkpoint-refresh/helper bundle is already represented and extended on transplant by `47c18d7` plus the later stabilization chain: the refresh-helper contract still passes, the checkpoint-refresh smoke still passes, and the host-readiness smoke still passes. The remaining delta is older checkpoint/doc state capture, not missing helper or verification behavior.
- Older doc/checkpoint-only commits now ready to drop as non-replay churn:
  - `18f633f docs: refresh verifier publish checkpoint`
  - `0b062e3 docs: refresh verifier publish checkpoint`
  - `4996e4f docs: sync verifier publish boundary`
  - `4aa294f docs: refresh visible verifier checkpoint`
  - `d7e7152 docs: refresh checkpoint helper boundary`
  - `7af8398 docs: refresh checkpoint helper state`
  - `9e2f0bf docs: sync verifier checkpoint narrative`
  These are all older checkpoint/doc-state snapshots on the legacy branch. With replay-safe code-only commits exhausted and the mixed queue fully closed, they no longer represent functional replay candidates and should be treated as intentional drop noise unless a future audit wants one purely for narrative archaeology.

## Best next move

Use `transplant/fix-openclaw-config-path-and-local-mode-clean-stack` as the canonical local publish baseline. The remaining older-only legacy history is now entirely already-accounted-for drop noise, so the next manual block should stay focused on the external publish boundary: make the current transplant tip GitHub-visible, rerun `Bootstrap Installer Preflight` on that exact visible ref, then proceed to VM verifier preflight / proof if it stays green.
