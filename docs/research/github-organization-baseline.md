# GitHub organization baseline research

Research date: 2026-10-27. Scope: GitHub.com organization infrastructure for Samwise-OS. Sources: official GitHub documentation and GitHub CLI documentation only. This research makes **no claims about the live organization's settings, plan, members, authentication, or effective permissions**. All implementation choices and tests below are recommendations until observed in the target organization.

## Findings and plan/authority gates

| Control | Documented capability and constraint | Recommended baseline |
| --- | --- | --- |
| Organization access | Owners control base repository permissions; repository grants can increase them. Base permissions do not apply to outside collaborators. [Base permissions](https://docs.github.com/en/organizations/managing-user-access-to-your-organizations-repositories/managing-repository-roles/setting-base-permissions-for-an-organization) | Base permission `none`; explicit team-to-repository grants after inventory. Approve access reduction before applying. |
| Repository roles | Read, triage, write, maintain, and admin are predefined. Custom repository roles require Enterprise Cloud. Owners have admin access to all organization repositories. [Repository roles](https://docs.github.com/en/organizations/managing-user-access-to-your-organizations-repositories/managing-repository-roles/repository-roles-for-an-organization) | Small owners set, visible maintainer teams, least privilege; avoid purchasing Enterprise just to name roles. |
| Authentication | Owners can require 2FA on Free, Team, and Enterprise; Enterprise Managed Users have a different boundary. Enabling it blocks noncompliant members' access and removes noncompliant outside collaborators. [2FA requirement](https://docs.github.com/en/organizations/keeping-your-organization-secure/managing-two-factor-authentication-for-your-organization/requiring-two-factor-authentication-in-your-organization) | Inventory compliance and recovery first; explicit owner approval before enforcement. |
| Repository rulesets | Public repositories support rulesets on Free; private repositories require Pro/Team/Enterprise. Repository admins or an appropriate custom permission manage repository rules. [About rulesets](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-rulesets/about-rulesets) | Prefer rulesets, inspect existing branch protection too, and enforce a default-branch policy only after a canary test. |
| Organization rulesets | Organization-wide rulesets are available on Team/Enterprise; creation is an owner operation. Rules can target all repositories or selected names/properties. Additional repository rules aggregate rather than weaken organization rules. [Organization rulesets](https://docs.github.com/en/organizations/managing-organization-settings/creating-rulesets-for-repositories-in-your-organization) | Use one centrally managed baseline when entitled; otherwise explicitly reconcile per-repository rules and document the weaker central authority. |
| Evaluation mode | The REST reference identifies `evaluate` as Enterprise-only. [Rules API](https://docs.github.com/en/rest/orgs/rules) | Do not assume Team offers an evaluation rollout. Use disabled configuration plus a deliberately targeted active canary when evaluation is unavailable. |
| Workflow identity enforcement | Enterprise Cloud documentation exposes organization/enterprise ruleset workflows requiring a specific workflow. This is distinct from a named status check. [Workflow rule](https://docs.github.com/en/enterprise-cloud%40latest/repositories/configuring-branches-and-merges-in-your-repository/managing-rulesets/available-rules-for-rulesets#require-workflows-to-pass-before-merging) | Treat this as an entitlement gate to verify in the live plan/API. The consulted general Team documentation does not establish Team entitlement for this specific rule. Do not promise it solely because ordinary org rulesets work. |
| Actions policy | Owners control organization Actions policies; enterprise policy can override them. Restricting to organization-only actions blocks even `actions/checkout`. The SHA-pinning policy still allows reusable workflows referenced by tag. [Actions policy](https://docs.github.com/en/organizations/managing-organization-settings/disabling-or-limiting-github-actions-for-your-organization) | Explicit allowlist including required GitHub actions; pin reusable workflows separately by SHA. Inventory policy precedence first. |
| Programmatic access | Owners govern app installation and token policies; app-manager status alone does not authorize installing an organization app. [Programmatic access](https://docs.github.com/en/organizations/managing-programmatic-access-to-your-organization/about-programmatic-access-in-your-organization) | Keep installation/access grants as owner approval items. Token presence does not prove sufficient effective authority. |

## Official management interfaces and declarative reconciliation

GitHub CLI `gh api` can call REST/GraphQL, load JSON request bodies with `--input`, and traverse pages with `--paginate`. Adding field parameters changes its default method to POST, so use an explicit method in automation. [CLI API reference](https://cli.github.com/manual/gh_api)

The following are documented API surfaces, not a claim that the current credential can call them successfully:

| Resource | Official API surface |
| --- | --- |
| Organization member defaults and creation restrictions | `GET/PATCH /orgs/{org}`. Update requires owner authority. Use granular creation fields rather than the deprecated `members_allowed_repository_creation_type`; organization API security defaults are also being superseded by security configurations. [Organizations API](https://docs.github.com/en/rest/orgs/orgs#update-an-organization) |
| Repositories and creation from templates | List/create org repositories; read/update a repository; generate from template. Repository payloads cover visibility, description, features, merge settings and archival. [Repositories API](https://docs.github.com/en/rest/repos/repos) |
| Teams and grants | List/create/update teams and add/update team repository permissions. Lists reflect what the caller can see, and team slugs derive from names. [Teams API](https://docs.github.com/en/rest/teams/teams) |
| Membership and roles | Membership changes require an authenticated owner; invitations remain pending until accepted. [Members API](https://docs.github.com/en/rest/orgs/members#set-organization-membership-for-a-user) |
| Organization rulesets | List/get/create/update/delete rulesets; write operations require organization Administration permission. Insufficiently privileged reads can omit `bypass_actors`. [Rules API](https://docs.github.com/en/rest/orgs/rules) |
| Actions policy and token defaults | Organization/repository policy endpoints include selected actions and workflow permissions; current API exposes `sha_pinning_required`. [Actions permissions API](https://docs.github.com/en/rest/actions/permissions) |
| Repository classification | Organization custom-property definitions and repository values have REST management. [Custom properties API](https://docs.github.com/en/rest/orgs/custom-properties) |

**Recommended implementation pattern:** retain the existing human-reviewed configuration authority in `Samwise-OS/admin` rather than create a competing repository-settings manifest. See the Safe-Settings addendum below. Use official `gh`/REST for discovery, verification, provisioning and explicitly separated controls that the chosen pinned reconciler does not own. This is an engineering recommendation, not a GitHub-provided organization-wide declarative product.

Recommended reconciliation contract:

1. Discover with complete pagination; record caller, authority, plan/feature observations, API version and observation time. Represent unreadable resources as unknown, never compliant or absent.
2. Normalize only managed fields. Exclude IDs, timestamps, generated URLs and array order where semantically unordered; retain meaningful bypass actors and permissions. Compare desired and observed values.
3. Produce a deterministic plan before mutation. Identify objects by stable recorded IDs after discovery, with name/slug mappings where necessary. Create only when truly absent; update only a semantic difference. Never implement ruleset reconciliation as unconditional POST.
4. Apply explicitly approved scope, then read back each modified resource. Handle partial completion and rate-limit/error responses explicitly. Do not interpret 404 as absence until the credential's visibility has been established.
5. Repeat the same apply: expect zero writes and zero semantic differences. For drift proof, introduce one reversible canary deviation, detect it, reconcile it, and verify a clean second pass.
6. Separate destructive removal, archival, visibility changes, credential grants, membership changes and owner privileges from routine additive reconciliation. An absent desired object should not silently trigger deletion.

These are proposed acceptance semantics. The APIs above provide operations; they do not themselves supply a transactional or automatically idempotent organization reconciler.

## Standards, templates and ownership

An ordinary organization's community defaults live in a **public** repository named `.github`; an Enterprise Managed Users organization uses internal visibility. Defaults apply to repositories missing their own equivalent file, including private repositories. Repository-specific issue templates/configuration replace the entire default issue-template set. Defaults are links/display behavior, not files injected into each clone. GitHub explicitly disallows a default license. [Default community files](https://docs.github.com/en/enterprise-cloud%40latest/communities/setting-up-your-project-for-healthy-contributions/creating-a-default-community-health-file)

Recommended public `.github` contents are CONTRIBUTING, CODE_OF_CONDUCT, SECURITY/support guidance, issue forms/config and a PR template, with public-safe information only. Keep repository licenses explicit and owner-approved; organizational bootstrap is not authority to relicense existing code. CODEOWNERS is repository-local, must exist on the PR's base branch, and owners/teams must have write access; teams must be visible. Protect CODEOWNERS itself and workflow/governance files. [CODEOWNERS](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/about-code-owners)

Template generation copies file structure and starts new history. It is not an ongoing upgrade channel; **inference/recommendation:** later standards changes need reconciliation/update PRs. Avoid assuming repository settings, teams, rulesets or secrets are provisioned merely because template files were copied. [Repository generation](https://docs.github.com/en/repositories/creating-and-managing-repositories/creating-a-repository-from-a-template)

Organization workflow templates reside in `.github/workflow-templates` with YAML and matching `.properties.json` metadata; `$default-branch` is substituted at creation. **Recommendation:** use these as discoverable starter callers; use provisioning/API checks to establish actual adoption. [Workflow templates](https://docs.github.com/en/actions/how-tos/reuse-automations/create-workflow-templates)

## Workflow security and identity pitfalls

Reusable workflows reside in `.github/workflows` and declare `workflow_call`; callers invoke them at job level. GitHub describes SHA references as safest for stability/security. [Reuse workflows](https://docs.github.com/en/actions/how-tos/reuse-automations/reuse-workflows) Called workflows can reduce, not elevate, caller token permissions. [Reuse reference](https://docs.github.com/en/actions/reference/workflows-and-actions/reusing-workflow-configurations)

Recommended validation workflows use explicit minimum permissions, immutable dependencies, deterministic inputs/tool versions, timeouts, and separate validation from privileged reconciliation. Do not pass organization administration credentials to untrusted PR execution. GitHub warns that checking out and executing untrusted PR code in `pull_request_target` can expose privileged tokens/secrets. [Secure PR-target use](https://docs.github.com/en/actions/reference/security/securely-using-pull_request_target)

**Named-check spoofing:** writers/integrations can set status checks; select an expected GitHub App source when configuring a required check. [Status-check rule](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-rulesets/available-rules-for-rulesets#require-status-checks-to-pass-before-merging) **Inference:** binding to GitHub Actions' App identifies the producer, not a particular workflow file. A repository writer may alter the caller or add another Actions workflow using the expected check name. Therefore a required reusable-workflow caller plus a check name is not equivalent to centrally enforced workflow identity. Protect caller changes with review and test adversarial substitution; use required ruleset workflows when actually entitled.

**Skipping and merge queues:** path/branch-filtered required workflows can stay pending; conditionally skipped jobs report success. A gate depending on other jobs should execute with `always()` and explicitly inspect every required result. Merge queues require the `merge_group` trigger. [Required-check troubleshooting](https://docs.github.com/en/enterprise-cloud%40latest/pull-requests/how-tos/merge-and-close-pull-requests/troubleshooting-required-status-checks)

**Single-owner review deadlock:** PR authors cannot approve their own PRs. [Required reviews](https://docs.github.com/en/pull-requests/how-tos/review-pull-requests/approving-a-pull-request-with-required-reviews) **Recommendation:** establish the actual number of independent reviewers before requiring approvals. Use a documented solo-owner exception or explicit PR-only break-glass path if necessary; do not present bot approval as independent review. Rulesets support PR-only bypass, which retains a PR trail while allowing bypass. [Bypass configuration](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-rulesets/creating-rulesets-for-a-repository)

## Automation identity

GitHub recommends GitHub Apps for long-lived organization integrations; PATs are user-bound and suited to short-lived scripts/testing. Apps remain installed when the installer leaves and do not consume a seat. Apps can authenticate inside Actions when GITHUB_TOKEN lacks needed access. [App versus PAT/Actions](https://docs.github.com/en/apps/creating-github-apps/about-creating-github-apps/deciding-when-to-build-a-github-app)

Recommendation: use the existing authorized credential for bounded bootstrap inspection, and propose an organization-owned GitHub App only if scheduled cross-repository reconciliation requires it. Keep execution on GitHub Actions rather than introduce an external service. Grant only the operation-specific organization/repository permissions verified against the endpoint docs. Separate a read-only drift identity from an approved mutation identity when operationally justified. Never store private keys or tokens in desired-state files or evidence artifacts.

## Proposed functional acceptance matrix

These are **tests to execute**, not completed verification. Run mutating negative cases only against an approved disposable canary and use the intended non-bypass actor. A successful owner operation does not prove a contributor restriction. Each evidence record should contain actor/permission context, repository/ref/commit, request/run identifiers, expected versus actual result, and readback; redact credentials.

| Test | Evidence required |
| --- | --- |
| Credential/visibility boundary | Membership/role plus authenticated resource inventory; missing permissions identified explicitly. Public enumeration alone cannot certify private inventory. |
| Reproducible provision | Create an approved canary from the manifest/template; verify visibility, default branch, metadata, files, teams, Actions and effective rules. Repeat and prove no duplicate objects/no writes. |
| Community defaults | A canary missing local guidance displays default contribution/support/security and issue/PR templates; a local override behaves as documented. Verify public content is suitable for private repositories too. |
| Branch enforcement | Non-bypass contributor direct push, force push, and protected-branch deletion attempts are rejected for the declared policy. Capture actual refusal and effective rules readback. |
| Failed/missing CI | Open a deliberately failing canary PR; merge must fail. Remove/rename the required caller and verify the missing check does not permit merge. |
| Substitution resistance | Attempt a same-name green check from the wrong source and a same-name alternate Actions workflow. Record whether either can satisfy the gate; do not certify workflow identity if substitution succeeds. |
| Positive merge | Correct the canary input; expected pinned workflow runs against the PR's current commit; required independent review, if configured, occurs; ordinary merge succeeds without bypass. |
| Fresh-commit behavior | Push a new commit after review; check fresh execution and declared stale-review behavior. Test merge-group execution only if a queue is in the baseline. |
| Privilege minimization | Validation runs cannot administer the organization, expose unrelated secrets, or apply configuration. Test authorized permissions without logging secret values. |
| Drift/idempotence | Reversible metadata deviation appears in the plan; approved apply restores it; readback matches; next plan/apply is empty. |
| Lifecycle | Approved archive operation sets `archived`; repository remains discoverable and excluded from active provisioning. No deletion is needed to prove lifecycle. |
| Recovery and handoff | Approved break-glass procedure remains operable by the designated owner; owner-only/manual and unreadable controls appear as explicit residual gates. |

Recommended completion criterion: a versioned manifest, scoped reconciler, owner decision register, API state report, canary run/PR evidence and zero-drift second pass. Any unavailable entitlement, identity gate, independent review, authentication setting or unreadable policy stays documented as a limitation; configuration presence alone is not operational acceptance.

## Addendum: existing Safe-Settings authority and owner versus credential

**Principal-supplied observations, not independently reverified by this research agent:** the organization is Free; Samwise-x is its sole owner; `Samwise-OS/admin` is public and contains a README describing Safe-Settings as canonical plus `.github/settings.yml` declaring `repository.delete_branch_on_merge: true`; installed apps show the Codex connector, not a Safe-Settings App; organization administration reads are blocked by the active OAuth credential's missing `admin:org` scope. Retain the principal's API records as the evidence for these observations.

Being a human organization owner and having an authorized API token are separate requirements. GitHub's troubleshooting guidance explicitly checks both the OAuth token's scopes and the authorizing user's required permissions. A 403/404 can reflect insufficient credentials and is not evidence that a policy/resource does not exist. [REST troubleshooting](https://docs.github.com/en/rest/using-the-rest-api/troubleshooting-the-rest-api) **Recommendation:** describe this gate as "owner account, insufficient current credential scope" rather than "not an owner" or "organization not configured". Restore the narrow required authenticated access before certifying organization administration state.

The `github/safe-settings` URL currently redirects to `github-community-projects/safe-settings`; the consulted default branch is `main-enterprise`. Its README documents centralized configuration in an admin repository, default-branch application and a runtime operated as a webhook service, scheduled job or GitHub Actions invocation. Its default exclusions include `admin`, `.github` and `safe-settings`. [Current upstream README](https://github.com/github-community-projects/safe-settings) **Recommendation:** identify it accurately as the current upstream community project, pin and inspect an exact revision before adoption, and explicitly scope management of the governance/default repositories. Do not imply the existing YAML activates itself or that a hosted GitHub service is already enforcing it.

Upstream provides an Actions full-sync guide using `npm run full-sync`, a GitHub App created for repository access, and runtime credentials/configuration including `APP_ID`, private key and admin/config paths. The example uses schedule and workflow dispatch. [Upstream Actions guide](https://github.com/github-community-projects/safe-settings/blob/main-enterprise/docs/github-action.md) **Inference:** this execution mode can stay on GitHub-hosted Actions without a persistent external webhook server. It still needs an installed and authorized App, stored credentials, pinned dependency/runtime setup, and successful acceptance tests; creating YAML alone is insufficient. Do not copy the guide's historical version tags as an audited current pin.

**Recommended boundary:** preserve `admin/.github/settings.yml` as canonical for fields actually supported by the selected Safe-Settings revision. Verify its schema and merge semantics from that pinned source. Put any supplemental organization policy manifest in the same admin repository and list field ownership explicitly: Safe-Settings must not own the same fields as a custom `gh api` mutation script. `gh api` readback is an independent verification path, not a competing configuration authority. An API-only reconciler is an alternative requiring an explicit replacement decision, not an automatic second writer.

**Free-plan result:** the current stated plan can support public repository rulesets and an Actions-based reconciliation approach, while org-wide rulesets remain unavailable under the documented Team/Enterprise gate above. API scripting cannot bypass feature entitlement. The sole-owner review caveat remains a genuine operational decision before enabling independent required approval.

### Exact source pin and implementation boundary

The GitHub branch API resolved `main-enterprise` to **`e19444e0d69de050ba55d0262b71fcd8a98edfef`** during this research. This is an inspected candidate pin, **not an approved or operationally validated dependency**. [Pinned source](https://github.com/github-community-projects/safe-settings/tree/e19444e0d69de050ba55d0262b71fcd8a98edfef)

The pinned plugin set contains repository settings, teams/collaborators, branches, labels/milestones, rulesets, environments, variables, properties, custom roles, archival and app-installation controls. The repository plugin calls repository create/update APIs. There is no general organization-settings or Actions-policy plugin in that set. **Source-based conclusion:** do not claim Safe-Settings manages organization base permissions, member creation privileges, 2FA or Actions permission policies; use separately owned official API/manual controls for those. The filename `.github/settings.yml` describes repository defaults across an organization, not blanket support for all organization administrative fields. [Pinned settings implementation](https://github.com/github-community-projects/safe-settings/blob/e19444e0d69de050ba55d0262b71fcd8a98edfef/lib/settings.js), [repository plugin](https://github.com/github-community-projects/safe-settings/blob/e19444e0d69de050ba55d0262b71fcd8a98edfef/lib/plugins/repository.js)

The pinned `isRestricted` implementation admits repositories matching an explicit `restrictedRepos.include` array, so `admin` can be included deliberately. It checks include before exclude, which differs from the README's combined-filter explanation. **Recommendation:** use an include-only canary list initially; do not combine include/exclude without a test against this pin. [Pinned scope implementation](https://github.com/github-community-projects/safe-settings/blob/e19444e0d69de050ba55d0262b71fcd8a98edfef/lib/settings.js)

The pinned package requires Node `>=22.0.0`, despite older deployment prose. The Actions guide documents `FULL_SYNC_NOP=true`, `GH_ORG` account selection and `npm run full-sync`; the CLI exits nonzero on absent installations or returned errors. [Package/runtime](https://github.com/github-community-projects/safe-settings/blob/e19444e0d69de050ba55d0262b71fcd8a98edfef/package.json), [pinned Actions guide](https://github.com/github-community-projects/safe-settings/blob/e19444e0d69de050ba55d0262b71fcd8a98edfef/docs/github-action.md), [CLI behavior](https://github.com/github-community-projects/safe-settings/blob/e19444e0d69de050ba55d0262b71fcd8a98edfef/full-sync.js)

Proposed minimal workflow shape (pseudocode, **not activation-ready YAML**):

```text
workflow_dispatch only initially; no PR-controlled privileged execution
permissions: contents: read
concurrency: one organization sync, cancel-in-progress false
checkout admin's reviewed default-branch commit using pinned actions/checkout SHA
checkout safe-settings at e19444e0d69de050ba55d0262b71fcd8a98edfef into .safe-settings-code
setup a pinned compatible Node 22 runtime using pinned actions/setup-node SHA
npm ci in .safe-settings-code using its pinned lockfile
npm run full-sync in .safe-settings-code with:
  GH_ORG=Samwise-OS
  ADMIN_REPO=admin
  CONFIG_PATH=.github
  DEPLOYMENT_CONFIG_FILE=<checked-out admin deployment-settings.yml absolute path>
  APP_ID=<organization-controlled app id>
  PRIVATE_KEY=<protected Actions secret>
  GITHUB_CLIENT_ID/GITHUB_CLIENT_SECRET=<if required by chosen runtime configuration>
  FULL_SYNC_NOP=true initially; explicit approved apply changes it to false
independent gh API readback and semantic drift comparison
```

The Actions guide supplies the client-id/secret variables but does not establish that they are individually necessary for installation-only full-sync. Verify the pinned runtime's exact authentication requirement before requesting them. Start with an App installed only on the approved canary/admin repositories and explicit scope configuration; add schedules only after acceptance and owner authorization. Full-sync uses App installation credentials, while the workflow's default GITHUB_TOKEN only reads its own repository.

The upstream App manifest requests broad repository permissions (including Administration, Checks, Contents, Issues, Pull requests, Statuses, Environments and Actions variables write), Members write, organization Administration write, custom-role/property permissions, and enterprise app-installation permissions. This is **the upstream full-feature manifest, not a least-privilege grant required by the proposed Free-plan baseline**. [Pinned App manifest](https://github.com/github-community-projects/safe-settings/blob/e19444e0d69de050ba55d0262b71fcd8a98edfef/app.yml) Recommendation: derive the enabled-plugin permission set from official endpoint references and test it. Repository Administration write is needed for repository settings/rules; Contents read for configuration, Metadata read for discovery, Checks write only if check publication is used, and Members/team grants only when that plugin is enabled. Do not request enterprise rights/custom-role administration for a Free org merely because present in the upstream manifest. GitHub's endpoint-specific permission tables and `X-Accepted-GitHub-Permissions` are the authority for final App grants. [Choosing App permissions](https://docs.github.com/en/apps/creating-github-apps/registering-a-github-app/choosing-permissions-for-a-github-app)
