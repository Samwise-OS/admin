# Operational acceptance

Status: **PARTIAL; operational acceptance is not complete.** The original four-repository
configuration apply and independent readback pass. Fresh repository provisioning is
created, adopted, protected and independently reconciled across the five-repository
managed scope. Repository CI acceptance are recorded. Deliberate canary drift was
detected and repaired manually in the earlier four-repository proof. The owner account
has 2FA enabled; the current
organization member 2FA-disabled filter and outside-collaborator inventory are empty.
The organization-level requirement is enabled and matched by owner-authenticated
readback; the documented organization REST update does not set that field, so future
drift requires GitHub security settings. A real
scheduled event, `41060159080`, ran before this activation change and correctly skipped
all credentialed steps. A credentialed scheduled reconciliation after activation remains
pending. A temporary reversible canary setting drift has been injected for this
scheduled acceptance; the event must repair it and independently read back the
five-repository scope. Codespaces runtime acceptance is recorded separately.

Configuration verification and human/device acceptance are separate. The live
Codespaces runtime check now passes within the tested template and runtime boundary.
GitHub Free's lack of organization-owned Codespaces budgets is an operating boundary;
the committed devcontainer supplies a reproducible repository default and no paid
upgrade is assumed.

| ID | Acceptance area | Current result |
| --- | --- | --- |
| A1 | Authorized inventory and plan boundaries | **Pass for the five declared managed repositories.** Safe-Settings selects all repositories; the program allowlist explicitly declares five. App reconciliation [41093839764](https://github.com/Samwise-OS/admin/actions/runs/41093839764) and independent readback matched identity, shared settings and active named rulesets for all five. The current scheduled acceptance injects a reversible settings drift on `baseline-canary`; its repair is tracked under A10. The organization rulesets endpoint confirms a Team-plan limitation, so repository rulesets are used. Owner 2FA and the organization requirement are enabled, and all current members are compliant. See [observed state](observed-state.md) and [org policy evidence](org-policy-evidence.md). |
| A2 | Declarative provisioning and repeatability | **Pass for the three previously managed targets and fresh repository.** Their adoption/content PRs merged after required checks passed, and the subsequent plan-only run reported no content, metadata, label, or vulnerability-reporting changes. Fresh repository `bootstrap-acceptance-20261030` is created, adopted, standard content merged, actively protected and matched in App reconciliation; its repeat plan at the durable workflow pin returned `already_converged` with no changes or proposals. See [rollout evidence](organization-rollout-evidence.md) and [fresh repository evidence](new-repository-acceptance-evidence.md). |
| A3 | Inherited standards and template behavior | **Pass for inspected actor and repository.** The issue chooser, Bug and Feature forms, required fields, labels, security links and inherited guidance rendered in the authenticated browser. Scope is limited to the inspected `baseline-canary` repository and actor. See [rendered issue form evidence](issue-form-acceptance-evidence.md). |
| A4 | Default-branch policy against direct, force and deletion updates | **Pass for bounded canary enforcement tests.** Fresh unassociated and force updates to canary `main` were rejected. A DELETE attempt against an isolated disposable branch was rejected under an active exact-ref deletion ruleset, and the production canary ruleset independently reads back its default-branch deletion rule. The real default branch was not deleted. See [canary evidence](canary-acceptance-evidence.md). |
| A5 | Required-check rejection | **Pass.** A failing check and a missing required check prevented normal PR merges. A same-name legacy status from `Samwise-x` did not satisfy the App-bound requirement. |
| A6 | Normal positive PR path | **Pass.** Canary PR #4 passed the real reusable standards workflow and merged normally without `--admin`. |
| A7 | Check producer identity | **Verified with a trust limitation.** The wrong-App same-name status was rejected. An alternate Actions workflow using the same GitHub Actions App could emit the required context and pass; App binding does not bind a check to a workflow implementation. |
| A8 | Freshness and stale-review behavior | **Freshness pass; stale-review behavior not applicable to current zero-approval policy.** A successful old-head check did not permit merge after the PR head changed; the stale head was rejected with HTTP 405 until a fresh exact-head check passed. See [actor and freshness evidence](actor-and-freshness-evidence.md). |
| A9 | Effective actor permissions and credential boundaries | **Pass for tested pull-only member boundary.** `BVEnterprisess` is an active member with pull access; same-role membership update returned HTTP 403 and same-value ruleset update returned HTTP 404. No settings changed. Fork-based PR contribution was not exercised. See [actor and freshness evidence](actor-and-freshness-evidence.md). |
| A10 | Drift detection, repair, and idempotence | **Four-repository manual drift/repeat pass; five-repository scheduled test pending.** Run [41011641487](https://github.com/Samwise-OS/admin/actions/runs/41011641487) applied the original four repositories. Repair [41011804776](https://github.com/Samwise-OS/admin/actions/runs/41011804776) made one mutation; repeat [41011894264](https://github.com/Samwise-OS/admin/actions/runs/41011894264) made zero and independently matched. Five-repository apply/readback [41093839764](https://github.com/Samwise-OS/admin/actions/runs/41093839764) also matched. A reversible canary wiki drift is currently awaiting repair by an actual scheduled event and follow-up zero-write readback. |
| A11 | Failure recovery | **Verified for exercised failures.** Retained CI diagnostics exposed a CI-only fixture defect; missing administrative visibility failed readback rather than passing; the corrected readback and deliberate setting-drift repair converged. Arbitrary failure modes are not certified by these cases. |
| A12 | Canary lifecycle and cleanup | **Pass for retention and isolated cleanup.** `baseline-canary` remains present with its history intact. The temporary deletion fixture ruleset and disposable branch were removed after the isolated deletion test; the real canary was not deleted. |

The detailed functional cases, run IDs, refs and rule-suite evaluations are in
[canary acceptance evidence](canary-acceptance-evidence.md). The five-write apply,
four-repository match, and injected drift receipt are appended to
[organization rollout evidence](organization-rollout-evidence.md). Sanitized public
evidence excludes the complete private inventory and raw API responses.

Completion remains open until a scheduled event after activation completes
reconciliation and independent readback, then the temporary five-minute cadence is
removed through a normal reviewed change.
