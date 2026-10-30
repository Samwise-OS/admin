# Initial observed state

This section is the pre-reconciliation snapshot, captured on 2026-10-27. It is kept as
historical evidence and does not describe the current organization state. Current policy
readback and apply evidence follow below.

Observed during this session on 2026-10-27 (America/New_York), using authenticated
official GitHub REST calls through `gh`. Organization ID: `349008063`.
This is a point-in-time audit, not a completion certificate.

| Area | Observation | Implication |
| --- | --- | --- |
| Authenticated CLI actor | `Samwise-x`; active organization membership, role `admin` | Owner account is available; token scope remains a separate boundary |
| CLI authorization | OAuth scopes include `read:org`, `repo`, `workflow`; no `admin:org` | Organization administration reads/changes are not fully authorized |
| Connector | Membership lists empty for all three linked accounts | Connector output did not establish organization access; CLI evidence used instead |
| Plan | `free` | Public repository rulesets available; org-wide rulesets need a paid tier |
| Repository inventory | One public repository, `Samwise-OS/admin`; org reports zero private repositories | No application repositories to migrate in the observed inventory |
| Ownership/access | One returned owner/member, `Samwise-x`; no returned teams or outside collaborators | Independent review/recovery still needs an explicit decision |
| Organization default access | `read` | Proposed `none` is a real access-policy change |
| Member privileges | Creation (public/private), deletion and visibility changes enabled | Proposed restrictions require owner approval |
| 2FA | Organization requirement false | Enrollment/recovery preflight needed before enforcement |
| Installed Apps | Returned installation list contains only `chatgpt-codex-connector`, selected repositories | No Safe-Settings installation was observed |
| Existing admin content | README and `.github/settings.yml` at main commit `19ec6fcf75d3aa971281a992d727f753d3ae560b` | Existing configuration authority is retained |
| Existing declared setting | `repository.delete_branch_on_merge: true` | Declaration does not equal live application |
| Admin merge settings | Merge, rebase and squash allowed; delete-on-merge false | Proposed defaults differ from live state |
| Admin protections | Repository rulesets list empty; branch-protection GET says `Branch not protected` | No protection established for `main` |
| Admin Actions | Enabled, all actions allowed, SHA pinning false | No action allowlist/pin enforcement observed at repository level |
| Admin workflow token | Default read; workflows cannot approve PRs | This particular token default already matches the proposal |
| Admin CI | Zero returned workflow runs | No successful baseline check exists yet |
| Admin security features | Returned secret scanning, push protection and Dependabot security updates disabled | No security-feature operation or acceptance claimed |
| GitHub Actions identity | `/apps/github-actions` returns ID `15368` | Candidate required-check binding uses a live observed App ID |

Organization Actions policy GETs return 403 and explicitly request `admin:org`.
Organization ruleset GET returns 404 with a scope diagnostic. These are **unknown**
states, not evidence of missing policy. The plan limitation is separately established
by plan readback and official documentation.

The reproducible audit output is saved under ignored `.local/observed-state.json`.
It reports `comparison_state: incomplete`, organization/repository settings differences,
and four unreadable organization policy resources. It always reports operational
acceptance as false because an API comparison cannot establish functional enforcement.
The complete local response inventory is intentionally not committed to the public repo.

No live organization setting, access grant, app, rule, credential scope or schedule was
changed during this initial inspection.

## Policy readback as of 2026-10-28

On 2026-10-28, authenticated `gh api` calls as owner `Samwise-x` reconciled the
organization baseline. Default repository permission is `none`; member repository
creation is disabled for public and private repositories. Organization Actions now
allow GitHub-owned actions only, require full-length SHA pins, and disallow verified
marketplace actions and extra patterns. Workflow tokens remain read-only and cannot
approve pull requests. At that observation, organization 2FA was disabled; the later
state is recorded below.

`members_can_change_repo_visibility` and `members_can_delete_repositories` both read
`false` after the owner changed them through the settings UI. These fields are returned
by GET but absent from GitHub's documented Update an organization request body, and the
REST PATCH did not change them. The controller treats any future drift as manual-only.

The `Maintainers` team (ID `20375471`, slug `maintainers`) has `Samwise-x` with the
maintainer role and a `maintain` grant on `admin`, `.github`, `repository-template`
and `baseline-canary`. At this historical observation, the `BVEnterprisess` invitation
remained pending; it was later accepted, as recorded in actor evidence.

The `admin/governance` environment (ID `25527561232`) has custom deployment branches
enabled, protected-branch matching disabled and exactly the `main` branch policy. It
has no required reviewer. This does not establish successful privileged execution.

The organization rulesets endpoint returned HTTP 403 with an explicit GitHub Team plan
upgrade requirement. The auditor classifies this as `unsupported_plan`, not as absent
configuration or an unexplained read failure. The ignored `.local/org-policy-results.json`
contains sanitized live readback and two consecutive zero-write policy and team passes.
That historical statement predates Safe-Settings activation and the canary functional
suite. Current evidence follows; consult `docs/acceptance.md` for remaining gates.

## Current managed-repository verification

On 2026-10-30, `Samwise-OS/admin` configuration commit `c5f1488` ran the four-repository
Safe-Settings apply in [run 41011641487](https://github.com/Samwise-OS/admin/actions/runs/41011641487).
The run succeeded with five managed configuration mutations. Its sanitized independent
audit matched repository identity, settings and the named ruleset for `admin`, `.github`,
`repository-template` and `baseline-canary`. A separate authenticated owner-CLI
readback also matched all four; the sanitized local result is retained at
`.local/all-four-owner-readback.json` and is not published because the full owner audit
contains private inventory.

The authenticated Safe-Settings App is active; its installation selects all
repositories. The program allowlist now declares five repositories after adoption of
`bootstrap-acceptance-20261030` (ID `1439988641`); this new repository has not yet been
reconciled. A subsequent deliberate change of
`baseline-canary.has_wiki` was detected by targeted audit as the sole drift, recorded in
`.local/drift-injection-2026-10-30.json`. Repair run `41011804776` succeeded with one
managed mutation and match; real repeat `41011894264` succeeded with zero managed
mutations and match. Scheduled run `41060159080` occurred before activation reached
`main`; it passed the gate but skipped all credentialed steps. A successful
post-activation scheduled invocation remains unobserved. The live canary
functional outcomes are recorded in `docs/canary-acceptance-evidence.md`.

## Latest owner-authenticated policy observation — 2026-10-30

The owner account reports personal 2FA enabled. The full organization member roster
contains two accounts; the owner-only `filter=2fa_disabled` query returns zero, and the
outside-collaborator inventory is empty. The organization requirement is enabled and
`GET /orgs/Samwise-OS` reads back `two_factor_requirement_enabled=true`. Both existing
members remained after enforcement. Detailed evidence is in
[`2fa-enforcement-evidence.md`](2fa-enforcement-evidence.md).

The policy controller's latest plan returned no writes. Its apply planned zero writes,
read back all writable organization and Actions fields plus team membership and grants,
reported no manual-only drift, and returned complete. GitHub's documented organization
REST update endpoint does not provide a setter for the organization 2FA field, so
future drift requires the security UI.

The App installation selects all repositories and the current program allowlist declares
five, including newly adopted `bootstrap-acceptance-20261030` (ID `1439988641`). Its
protection and reconciliation remain pending rollout. Codespaces runtime acceptance
remains open: the prior create succeeded but remote shell failed during sshd Feature
setup. PR10 pins the official Feature by digest; the live fix still requires rollout to
the template repository's `main`. No organization-owned Codespaces budget or policy is
claimed on GitHub Free.
