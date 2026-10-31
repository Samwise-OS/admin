# Organization policy evidence

Observed 2026-10-28 at 02:15 UTC through authenticated GitHub REST requests using
`gh`, as organization owner `Samwise-x` (organization ID `349008063`). The organization
is on GitHub Free. This document records live settings and operation boundaries; it does
not certify the end-to-end bootstrap.

## Applied organization settings

`GET /orgs/Samwise-OS` confirmed default repository permission `none`; repository
creation disabled for ordinary members (`members_can_create_repositories=false`, with
public/private creation both false); deletion and repository-visibility changes both
false; organization 2FA requirement false.

The single current organization member is `Samwise-x`. The one live
`GET /orgs/Samwise-OS/members?filter=2fa_disabled` check returned `Samwise-x`, so not all
existing members are enrolled. Outside collaborators were empty. Therefore organization
2FA enforcement remains off. `BVEnterprisess` is still a pending `direct_member`
invitation and was not accepted, declined, or modified.

Actions settings read back as: enabled for all organization repositories; allowed
actions policy `selected`; GitHub-owned actions allowed; verified actions disallowed;
pattern allowlist empty; full-SHA pinning required. Workflow permissions are read-only,
and workflows cannot approve pull requests. The org-wide rulesets endpoint returns an
explicit upgrade-to-Team 403 on the Free plan; repository rulesets remain the supported
path.

The `Maintainers` team (ID `20375471`, slug `maintainers`) has `Samwise-x` as a team
maintainer. The team has `maintain` grants on `admin` (ID `1436238530`), `.github`
(ID `1436487227`), `repository-template` (ID `1436487455`) and `baseline-canary` (ID
`1436487640`).

The `admin/governance` environment (ID `25527561232`) uses a custom deployment branch
policy with exactly `main`; `protected_branches=false`, `custom_branch_policies=true`,
and no required reviewer. `can_admins_bypass=true` is returned by GitHub, so this setting
does not prevent an administrator bypass. A successful governance run (`40617769323` on
commit `28908af`) is CI evidence only; the functional canary cases remain open.

Safe-Settings App `samwise-os-safe-settings` (App ID `5504298`, installation ID
`176024067`) is installed with `repository_selection=selected`. Its observed grants are
Administration write, Checks write, Contents read and Metadata read. The four selected
repositories are `admin`, `.github`, `repository-template` and `baseline-canary`.
Authenticated no-op run `40619654778` succeeded. This proves the no-op invocation only;
scheduled reconciliation remains disabled. The manifest keeps
`source_review_complete=false` until the source-review record is explicitly updated.

The organization policy reconciler's local sanitized evidence is
`.local/org-policy-results.json`. It records two consecutive passes with zero policy
writes and no team or grant writes on the second pass. The second pass read back all
four team grants as matching. A successful no-op run, readback or repeated no-write pass
does not establish canary enforcement, failure recovery or full operational acceptance.

## Manual-only policy setters

The public REST `Update an organization` request body documents repository defaults and
repository-creation controls, but omits `members_can_delete_repositories`,
`members_can_change_repo_visibility`, and `two_factor_requirement_enabled`. Attempts to
include deletion/visibility fields in that PATCH returned success without changing the
settings. The owner applied deletion and visibility through the GitHub member-privileges
UI; the API readback above confirms both false. Do not retry those fields as REST writes.

At the 2026-10-28 observation, the recommended next step was to keep the organization
requirement off until the affected principals enrolled, then enable it through GitHub
security settings. That precondition was later satisfied: the latest authenticated
inventory returned zero 2FA-disabled members and zero outside collaborators, the
invitation was accepted, and the owner enabled the requirement. Current readback follows.

See GitHub's [REST API endpoints for organizations](https://docs.github.com/en/rest/orgs/orgs?apiVersion=2022-11-28)
for the update request fields. The observation above is historical; the latest verified
state is recorded below.

## Latest authenticated state — 2026-10-30

Owner-authenticated CLI reads confirmed personal 2FA enabled, two organization members,
zero members returned by `filter=2fa_disabled`, and zero outside collaborators. The
principal enabled the organization requirement in GitHub security settings. Independent
`GET /orgs/Samwise-OS` returned `two_factor_requirement_enabled=true`; both existing
members remained. No personal recovery codes were requested or inspected. See
[`2fa-enforcement-evidence.md`](2fa-enforcement-evidence.md).

Safe-Settings installation `176024067` now reports `repository_selection=all`. The
manifest program allowlist declares five repositories, including newly adopted
`bootstrap-acceptance-20261030` (ID `1439988641`). App apply/readback
[41093839764](https://github.com/Samwise-OS/admin/actions/runs/41093839764) matched identity, shared
settings and managed rulesets across all five. The owner controller then wrote the
Maintainers `maintain` grant for the new repository; its immediate repeat returned
`complete=true` with all five grants already matching.

Scheduled run [41060159080](https://github.com/Samwise-OS/admin/actions/runs/41060159080)
was a genuine timer event, but `main` still had `schedule_enabled=false`. The activation
gate passed and all credentialed reconciliation and readback steps were skipped. It is
not schedule acceptance. Subsequent post-activation scheduled run
[41129273464](https://github.com/Samwise-OS/admin/actions/runs/41129273464) repaired the
isolated canary settings drift with one managed mutation and independently matched the
five-repository scope. The following scheduled run
[41152199154](https://github.com/Samwise-OS/admin/actions/runs/41152199154) made zero
managed mutations and independently matched the same scope. The temporary acceptance
cadence was removed in the reviewed closeout change; daily 06:17 UTC remains enabled.
