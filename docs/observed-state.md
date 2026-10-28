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

## Current policy readback

On 2026-10-28, authenticated `gh api` calls as owner `Samwise-x` reconciled the
organization baseline. Default repository permission is `none`; member repository
creation is disabled for public and private repositories. Organization Actions now
allow GitHub-owned actions only, require full-length SHA pins, and disallow verified
marketplace actions and extra patterns. Workflow tokens remain read-only and cannot
approve pull requests. Organization 2FA remains disabled.

`members_can_change_repo_visibility` and `members_can_delete_repositories` both read
`false` after the owner changed them through the settings UI. These fields are returned
by GET but absent from GitHub's documented Update an organization request body, and the
REST PATCH did not change them. The controller treats any future drift as manual-only.

The `Maintainers` team (ID `20375471`, slug `maintainers`) has `Samwise-x` with the
maintainer role and a `maintain` grant on `admin`, `.github`, `repository-template`
and `baseline-canary`. The pending `BVEnterprisess` invitation remains a direct-member
invitation.

The `admin/governance` environment (ID `25527561232`) has custom deployment branches
enabled, protected-branch matching disabled and exactly the `main` branch policy. It
has no required reviewer. This does not establish successful privileged execution.

The organization rulesets endpoint returned HTTP 403 with an explicit GitHub Team plan
upgrade requirement. The auditor classifies this as `unsupported_plan`, not as absent
configuration or an unexplained read failure. The ignored `.local/org-policy-results.json`
contains sanitized live readback and two consecutive zero-write policy and team passes.
Overall acceptance remains false because owner 2FA is open, Safe-Settings authentication
is pending, and the canary suite has not run.
