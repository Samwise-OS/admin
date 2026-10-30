# Organization repository provisioning rollout evidence

**Recorded:** 2026-10-30 06:00 UTC

**Provisioner source:** `Samwise-OS/admin` main `9811e2dba4ecb5e4cb6564b385a7f6b4e46d6e2b`
**Scope:** existing managed repositories `.github`, `repository-template`, and `baseline-canary`

The owner-authenticated `scripts/provision.py --apply` run reconciled each declared
repository's shared files through a normal pull request. All three PRs passed the
required `baseline / standards` check on the exact head SHA before squash merge. No
`--admin` merge path was used.

| Repository | PR | PR head | Required check run | Squash merge commit |
| --- | --- | --- | --- | --- |
| `.github` | [#1](https://github.com/Samwise-OS/.github/pull/1) | `e73f0c90428e9cc5c519f83cd9eaa1a3ec1d1e3e` | `41011171898` — pass | `663fb92077488220a7f168eadb7ea3bfdb228591` |
| `repository-template` | [#1](https://github.com/Samwise-OS/repository-template/pull/1) | `1f4d9ae271aa1556ac3cff28e7870ac04f3fa378` | `41011189557` — pass | `808daccca9b87c4499edf793139993cd4170b438` |
| `baseline-canary` | [#5](https://github.com/Samwise-OS/baseline-canary/pull/5) | `f9ff8e6c4c329b5af887896a2e03a5eac2d47348` | `41011205037` — pass | `68b68301305674d868c033b845c31ed7f3f8b938` |

The post-merge plan-only run against the same administration workflow SHA reported
`already_converged` for all three repositories. Each had no pending content PR, no
metadata changes, no label changes, and private vulnerability reporting enabled with
no change required. This establishes provisioning convergence for the declared files
and metadata; it does not establish Safe-Settings readback or organization policy
reconciliation, which are separate acceptance steps.

The first local invocation hit a Windows CP1252 decoding exception while reading GitHub
CLI output after provisioning had begun. The rerun set `PYTHONUTF8=1`; the provisioner
reused the deterministic PRs and the follow-up plan confirmed zero remaining changes.

## Four-repository Safe-Settings apply and drift detection

Configuration revision `c5f1488` completed the all-four apply in
[run 41011641487](https://github.com/Samwise-OS/admin/actions/runs/41011641487):
success with five managed configuration mutations. The sanitized workflow artifact's
managed audit returned `MATCH` for repository identity, shared settings and the exact
named ruleset on `admin`, `.github`, `repository-template` and `baseline-canary`. A
separate authenticated owner-CLI audit also matched all four; its sanitized output is
retained locally at `.local/all-four-owner-readback.json` because the full audit
contains private inventory.

A controlled drift injection then changed `baseline-canary.has_wiki` from the declared
`false` value to `true` on repository ID `1436487640`. The targeted audit exited 2 and
reported only `baseline-canary.has_wiki` as drift in
`.local/drift-injection-2026-10-30.json`. This confirms detection of the intended
field-level drift. Repair, successful readback and the next zero-write apply remain
pending; the scheduled workflow activation flag stays false until those checks and the
parent's explicit activation decision are complete.
