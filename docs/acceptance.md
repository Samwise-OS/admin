# Operational acceptance

Status: **PARTIAL; operational acceptance is not complete.** The four-repository
configuration apply and independent readback pass. Provisioning and repository CI
acceptance are recorded. Deliberate canary drift was detected, repaired, and followed
by a successful zero-write real apply. Owner 2FA enrollment is not complete;
the Codespaces authentication/session follow-up was unanswered and is unverified.
Daily reconciliation is enabled by the versioned activation flag in this revision.
The first timer-triggered invocation has not yet been observed.

Configuration verification and human/device acceptance are separate. A successful
configuration readback does not complete owner 2FA or Codespaces authentication.
GitHub Free's lack of organization-owned Codespaces budgets is an operating boundary;
the committed devcontainer supplies a reproducible repository default and no paid
upgrade is assumed.

| ID | Acceptance area | Current result |
| --- | --- | --- |
| A1 | Authorized inventory and plan boundaries | **Partial.** The installed Safe-Settings App and four-repository selection are active. The organization rulesets endpoint confirms a Team-plan limitation; repository rulesets are used. Owner 2FA remains unenrolled. Codespaces scope/session acceptance is unverified. See [observed state](observed-state.md) and [org policy evidence](org-policy-evidence.md). |
| A2 | Declarative provisioning and repeatability | **Pass for declared repositories.** The three adoption/content PRs merged after their required check passed; the subsequent plan-only provisioning run reported no content, metadata, label, or vulnerability-reporting changes. See [rollout evidence](organization-rollout-evidence.md). |
| A3 | Inherited standards and template behavior | **API inheritance verified; UI acceptance partial.** The community profile API resolves code of conduct, contribution guidance and PR template to `.github`. Forms and template declarations are versioned; their rendered chooser was not independently rechecked in this run. See [provisioning evidence](provisioning-evidence.md). |
| A4 | Default-branch policy against direct and force updates | **Partial.** A fresh unassociated commit update and a force update to canary `main` were both rejected. Deletion was tested on an isolated disposable branch with a temporary exact-ref ruleset; deletion of the real default branch was not attempted. |
| A5 | Required-check rejection | **Pass.** A failing check and a missing required check prevented normal PR merges. A same-name legacy status from `Samwise-x` did not satisfy the App-bound requirement. |
| A6 | Normal positive PR path | **Pass.** Canary PR #4 passed the real reusable standards workflow and merged normally without `--admin`. |
| A7 | Check producer identity | **Verified with a trust limitation.** The wrong-App same-name status was rejected. An alternate Actions workflow using the same GitHub Actions App could emit the required context and pass; App binding does not bind a check to a workflow implementation. |
| A8 | Freshness and stale-review behavior | **Not fully tested.** New PR heads produced fresh Actions runs during the acceptance sequence, but a separate stale-review behavior test is not recorded. |
| A9 | Effective actor permissions and credential boundaries | **Partial.** Organization/team configuration is read back, and CI uses read-only `contents` permission. A non-owner actor was not available to test prohibited member/admin operations. Future member onboarding requires an actual-actor permissions test; do not infer a pass from the current solo-owner configuration. |
| A10 | Drift detection, repair, and idempotence | **Pass.** Run [41011641487](https://github.com/Samwise-OS/admin/actions/runs/41011641487) applied all four repositories. The sole injected `baseline-canary.has_wiki` drift was detected with exit 2; repair [41011804776](https://github.com/Samwise-OS/admin/actions/runs/41011804776) made exactly one managed mutation and read back match. Real repeat [41011894264](https://github.com/Samwise-OS/admin/actions/runs/41011894264) made zero managed mutations and independently read back match. |
| A11 | Failure recovery | **Verified for exercised failures.** Retained CI diagnostics exposed a CI-only fixture defect; missing administrative visibility failed readback rather than passing; the corrected readback and deliberate setting-drift repair converged. Arbitrary failure modes are not certified by these cases. |
| A12 | Canary lifecycle and cleanup | **Pass for retention and isolated cleanup.** `baseline-canary` remains present with its history intact. The temporary deletion fixture ruleset and disposable branch were removed after the isolated deletion test; the real canary was not deleted. |

The detailed functional cases, run IDs, refs and rule-suite evaluations are in
[canary acceptance evidence](canary-acceptance-evidence.md). The five-write apply,
four-repository match, and injected drift receipt are appended to
[organization rollout evidence](organization-rollout-evidence.md). Sanitized public
evidence excludes the complete private inventory and raw API responses.

Completion remains open until drift repair and the next zero-write apply/readback pass,
the schedule activation decision is reviewed, and the owner completes the outstanding
2FA enrollment. Do not represent the unanswered Codespaces session flow as accepted.
No owner 2FA requirement is enabled before enrollment and recovery readiness.
