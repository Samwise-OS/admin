# Actor and freshness acceptance evidence — 2026-10-30

Authenticated GitHub API checks used the saved `BVEnterprisess` credential through a process-scoped `GH_TOKEN`; the token was cleared after each command and never written to evidence. `GET /user` returned `BVEnterprisess`. Organization membership readback showed `state=active`, `role=member`. On `Samwise-OS/baseline-canary`, GitHub reported `pull=true`, `push=false`, `maintain=false`, and `admin=false`; the public repository allows forks.

## Effective actor boundary

Two same-value administrative operations were attempted after reading their current state:

- `PUT /orgs/Samwise-OS/memberships/BVEnterprisess` with the existing `role=member` was rejected with **HTTP 403**: “You must be an admin to add or update an organization membership.” The membership remained active and `member` afterward.
- `PUT /repos/Samwise-OS/baseline-canary/rulesets/26186884` with the active ruleset's read-back values returned **HTTP 404 Not Found**. GitHub concealed the admin-only update endpoint from this pull-only actor. The ruleset remained active with the same required check policy.

The effective repository role confirms this actor cannot push directly to the canary or grant organization membership roles. The public repository permits forks, so a fork-based PR is the configured contribution path; that path was not exercised. The member account's 2FA state is not exposed by the authenticated user endpoint used here. No account or organization settings changed.

## Check freshness

The canary ruleset `samwise-default-branch` (ID `26186884`) is active on `~DEFAULT_BRANCH` and requires `baseline / standards` from GitHub Actions App `15368` with `strict_required_status_checks_policy=true`. Required approving reviews are `0`.

Live test PR [#6](https://github.com/Samwise-OS/baseline-canary/pull/6) established A8:

1. Its initial head `77428b62118f02ccccc615cc8f00d082eca64499` received a successful App 15368 check in run [41091906185](https://github.com/Samwise-OS/baseline-canary/actions/runs/41091906185).
2. The PR advanced to `e27aa57a926d79b81f143468c8c839643e877db2` with `[skip ci]`. That head had zero check runs and combined status `pending`; the earlier successful check remained on the previous SHA. A normal merge attempt returned **HTTP 405**, explicitly reporting `Required status check "baseline / standards" is expected.`
3. The PR advanced again to `635087bee47bfe6d09e69a7dc6cd351107e60a29`. Fresh run [41092106539](https://github.com/Samwise-OS/baseline-canary/actions/runs/41092106539) passed on that exact head, and PR #6 merged normally as `8a2ce4e79aa2370fa3266f7101f5c005d7e5c5d4`.

Stale-review dismissal is inapplicable to this solo-owner policy because required approving reviews are zero; no review behavior was changed or claimed.

Cleanup PR [#7](https://github.com/Samwise-OS/baseline-canary/pull/7) passed run [41092229628](https://github.com/Samwise-OS/baseline-canary/actions/runs/41092229628), merged normally, and removed the temporary fixture. Final readback confirmed main at `a047bdde4bbb42ea156057a025d12a8b27cbe1fb`, the fixture file absent, both probe branches absent, and both PRs closed as merged.

Sanitized machine-readable evidence is in [`.local/actor-acceptance-2026-10-30.json`](../.local/actor-acceptance-2026-10-30.json). The shared admin checkout received no commits or branch changes.
