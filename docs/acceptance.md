# Operational acceptance

Status: **NOT EXECUTED**. Local validation and read-only inventory have passed only
their stated scope. No organization baseline completion is claimed.

Every live case records the configuration commit/digest, organization and repository
IDs, actor/effective permission, endpoint and request/run/PR identifiers, current
commit SHA, expected/actual behavior and readback. Redact credentials. A denied
permission or missing entitlement is a blocked/unknown test, never a pass.

| ID | Test | Required result | Status |
| --- | --- | --- | --- |
| A1 | Full authorized inventory | Owner and credential independently verified; complete repo/member/team/App/policy inventory, no unreadable required controls | Partial: four policy reads unknown |
| A2 | Declarative provisioning | Approved canary generated with expected files/settings/grants; second identical operation creates nothing | Pending owner authorization and visibility/plan |
| A3 | Inherited standards | Canary without local overrides displays public `.github` defaults; repository-local CODEOWNERS and license handled explicitly | Pending community/template repos |
| A4 | Effective default-branch policy | Intended non-bypass contributor cannot direct push, force push or delete the protected default branch | Pending actor, canary and rule activation |
| A5 | CI rejection | Deliberately failing PR cannot merge; missing/renamed required check cannot merge | Pending real workflow/ruleset |
| A6 | Positive path | Corrected current-head PR runs expected CI and merges normally with selected review policy, without bypass | Pending review decision |
| A7 | Check identity | Wrong-App same-name check rejected; alternate Actions workflow substitution tested and result documented | Pending; Actions App binding alone is insufficient |
| A8 | Freshness | New commit causes new CI and declared stale-review behavior | Pending |
| A9 | Effective permissions | Test actor cannot perform prohibited admin/member operations; validation jobs cannot use organization write credentials | Pending scoped identity |
| A10 | Drift and idempotence | Approved reversible metadata drift detected, repaired, read back; next sync zero semantic changes AND zero writes | Pending executor/App |
| A11 | Failure recovery | Partial sync fails visibly; approved retry converges; designated owner can recover a bad canary rule | Pending |
| A12 | Lifecycle | Approved canary retained or archived; inventory reflects status; no deletion | Pending retention choice |

Do not perform negative writes on `admin` or delete a real default branch. Use the
approved disposable canary with a known recovery path. Owner operations do not prove
contributor restrictions. Do not weaken production policy to manufacture a green test.

Known trust boundary: on Free, per-repository named checks remain dependent on trusted
writers and protection of workflow/caller files. If an alternate workflow satisfies the
same App-bound check, document that limitation. Do not certify centrally immutable
workflow identity; evaluate a supported stronger entitlement/control if it is required.

Completion requires A1-A12 evidence or an explicit owner-accepted documented exception
for each unmet control, zero unmanaged drift in the declared scope, an approved recovery
path and a successful second reconciliation. Provisioning and enforcement may not be
waived merely because configuration files or a health check exist.
