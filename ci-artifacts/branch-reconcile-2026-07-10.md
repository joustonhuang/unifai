# Branch Reconcile Note — 2026-07-10 09:50 Asia/Taipei

## Current state

- `transplant/fix-openclaw-config-path-and-local-mode-clean-stack` is the cleaner publish candidate.
- `fix/openclaw-config-path-and-local-mode` still carries extra local-only history and doc churn.
- Divergence count from `git rev-list --left-right --count fix/openclaw-config-path-and-local-mode...transplant/fix-openclaw-config-path-and-local-mode-clean-stack`:
  - `fix/openclaw-config-path-and-local-mode`: `18`
  - `transplant/fix-openclaw-config-path-and-local-mode-clean-stack`: `22`

## Transplant-only commits

```text
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

## Manual review queue

- Mixed docs+code older commits still needing conscious keep/drop review:
  - `d8539bb scripts: harden verifier publish boundary`
    Likely split across `22b7bc9`, `a16bb5f`, and later checkpoint-refresh commits; review only for any behavior still missing.
  - `aaee837 scripts/docs: refresh vm verifier checkpoint state`
    Likely superseded by `47c18d7` plus the later checkpoint/doc stabilization chain on transplant.
- Reviewed mixed docs+code older commits now ready to drop:
  - `7756061 dev: harden verifier preflight remote boundary`
    Functional coverage is already present on transplant via `c867fa3` for the preflight/GitHub-gate code path, `22b7bc9` for the later publish-boundary hardening, and `5837f8c` for the missing-remote smoke restoration. Remaining delta is checkpoint/doc churn, not missing behavior.
  - `f4232c5 docs: sync visible verifier boundary state`
    Its exact behavior is already represented and then extended on transplant: the checkpoint-refresh helper still rewrites the GitHub-visible head and tracked local head lines, the smoke test still asserts those synced boundary values, and later commits such as `05b564a`, `47c18d7`, and `6b715c9` broaden that same checkpoint/doc sync path substantially. Remaining delta is earlier wording/doc-state churn, not missing logic.
- Older doc/checkpoint-only commits remaining for review or drop:
  - `18f633f docs: refresh verifier publish checkpoint`
  - `0b062e3 docs: refresh verifier publish checkpoint`
  - `4996e4f docs: sync verifier publish boundary`
  - `4aa294f docs: refresh visible verifier checkpoint`
  - `d7e7152 docs: refresh checkpoint helper boundary`
  - `7af8398 docs: refresh checkpoint helper state`
  - `9e2f0bf docs: sync verifier checkpoint narrative`

## Best next move

Use `transplant/fix-openclaw-config-path-and-local-mode-clean-stack` as the canonical local publish baseline. The next manual block should review the 2 still-open mixed older commits above in order, confirm each one is already functionally represented by newer transplant commits, and then treat the 7 older doc-only commits as intentional drop candidates rather than replay work.
