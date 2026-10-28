# Safe-Settings bounded execution review

Reviewed 2026-10-27 for Samwise-OS. Read-only research: upstream source and package archives were downloaded and inspected; **no dependency code was installed or executed, no GitHub resources were changed, and no credentials were accessed**. The source-derived permission proposal below still requires a real authenticated NOP/apply/readback test before being called operationally proven.

## Decision

**Recommend retaining Safe-Settings as the repository-settings authority**, running its pinned full-sync command in GitHub Actions. External hosting is unnecessary for this mode. The existing `admin/.github/settings.yml` should remain authoritative; repository rulesets belong in a repository override or a repo-scoped suborg file. The reviewed implementation can avoid organization grants entirely for this bounded use case. [Pinned full-sync entrypoint](https://github.com/github-community-projects/safe-settings/blob/e19444e0d69de050ba55d0262b71fcd8a98edfef/full-sync.js), [upstream Actions guide](https://github.com/github-community-projects/safe-settings/blob/e19444e0d69de050ba55d0262b71fcd8a98edfef/docs/github-action.md)

Do not copy the complete upstream App manifest. It enables enterprise app-installation/custom-role/property and other capabilities unnecessary here. [Pinned App manifest](https://github.com/github-community-projects/safe-settings/blob/e19444e0d69de050ba55d0262b71fcd8a98edfef/app.yml)

## Identity of the reviewed inputs

- Source commit: `e19444e0d69de050ba55d0262b71fcd8a98edfef` from `github-community-projects/safe-settings`; `github/safe-settings` redirects to this project. [Pinned source](https://github.com/github-community-projects/safe-settings/tree/e19444e0d69de050ba55d0262b71fcd8a98edfef)
- `package-lock.json` local SHA-256: `8C0EDE66EB57296B64B0A2144C9AF75553A1B271E571DCCA278606DCD6150F7B`. Its parsed records contain 1,070 dependency entries, of which 354 are non-dev entries; all 354 have integrity fields and npm-registry HTTPS resolved URLs, with no `hasInstallScript` flag. These are static lockfile observations, not a vulnerability audit. [Pinned lockfile](https://github.com/github-community-projects/safe-settings/blob/e19444e0d69de050ba55d0262b71fcd8a98edfef/package-lock.json)
- Package engine: Node `>=22.0.0`. Locked Probot: `14.3.2`; locked `@probot/get-private-key`: `2.1.1`. The two published package tarballs were downloaded and their SHA-512 integrity values compared successfully with the lockfile before reading their compiled JavaScript. [Pinned package](https://github.com/github-community-projects/safe-settings/blob/e19444e0d69de050ba55d0262b71fcd8a98edfef/package.json), [Probot package inspected](https://registry.npmjs.org/probot/-/probot-14.3.2.tgz), [key-loader package inspected](https://registry.npmjs.org/@probot/get-private-key/-/get-private-key-2.1.1.tgz)
- Download-only research files are under `.local/research-safe-settings/`. No runtime testing is implied by their presence.

## Minimum proposed GitHub App grants

For **unmodified upstream full-sync**, existing repository settings plus repository rulesets, configuration read from `admin`, numeric/no bypass actors, no provisioning/branch creation, no team/property selectors, and no webhook mode:

| Permission | Level | Why the actual code needs it |
| --- | --- | --- |
| Repository Administration | Write | `repository` plugin reads/PATCHes repository settings; rulesets plugin lists/reads/creates/updates/deletes repository rulesets. [Repository plugin](https://github.com/github-community-projects/safe-settings/blob/e19444e0d69de050ba55d0262b71fcd8a98edfef/lib/plugins/repository.js), [rulesets plugin](https://github.com/github-community-projects/safe-settings/blob/e19444e0d69de050ba55d0262b71fcd8a98edfef/lib/plugins/rulesets.js), [official rules API permission](https://docs.github.com/en/rest/repos/rules#create-a-repository-ruleset) |
| Repository Contents | Read | Loads `.github/settings.yml`, suborg/repository YAML, directories/git trees and latest admin commit. [Config loader](https://github.com/github-community-projects/safe-settings/blob/e19444e0d69de050ba55d0262b71fcd8a98edfef/lib/configManager.js), [settings loader/reporting](https://github.com/github-community-projects/safe-settings/blob/e19444e0d69de050ba55d0262b71fcd8a98edfef/lib/settings.js), [official contents API](https://docs.github.com/en/rest/repos/contents#get-repository-content) |
| Repository Checks | Write | Every non-NOP `handleResults()` invokes `createCheckRun()` against the latest admin commit. This occurs even if only repository defaults/rulesets are enabled. [Settings implementation, methods createCheckRun/handleResults](https://github.com/github-community-projects/safe-settings/blob/e19444e0d69de050ba55d0262b71fcd8a98edfef/lib/settings.js), [official Checks requirement](https://docs.github.com/en/rest/checks/runs#create-a-check-run) |
| Repository Metadata | Read | Required baseline discovery; lists repositories accessible to the installation. [Installation enumeration](https://github.com/github-community-projects/safe-settings/blob/e19444e0d69de050ba55d0262b71fcd8a98edfef/lib/settings.js), [official installations API](https://docs.github.com/en/rest/apps/installations#list-repositories-accessible-to-the-app-installation) |
| Organization permissions | None | With no org rulesets, custom roles, properties, team selectors, app-installation management or memberships configured, those plugins/API paths are not needed. [Plugin dispatch and org guards](https://github.com/github-community-projects/safe-settings/blob/e19444e0d69de050ba55d0262b71fcd8a98edfef/lib/settings.js) |

Do **not** request Contents write, Issues, Pull requests, Statuses, Actions, Actions variables, Members, organization Administration, custom-role/property or enterprise permissions for this bounded runner. This is a source-derived proposal; the final native run must confirm there are no unexpected permission failures. An App registration may request broader permissions later, but doing so requires a new reviewed need rather than copying the upstream defaults.

Install the App on only `admin` and an approved public canary initially. Grant access to additional managed repositories deliberately. This installation boundary is stronger than `GH_ORG` and YAML filtering: filtering constrains cooperative program behavior but cannot stop compromised code using the App's actual privileges. The App private key also permits minting tokens for every installation of that App, so prefer a dedicated private Samwise-OS App with only this installation. [Installation authentication and token scope](https://docs.github.com/en/apps/creating-github-apps/authenticating-with-a-github-app/authenticating-as-a-github-app-installation)

## Startup and API execution trace

1. `full-sync.js` calls `createProbot().ready()`, loads the app function and invokes `syncInstallation(nop)`. It exits nonzero on no installation, returned errors or exceptions. [Entrypoint](https://github.com/github-community-projects/safe-settings/blob/e19444e0d69de050ba55d0262b71fcd8a98edfef/full-sync.js)
2. The app function starts `info()` **without awaiting it**; that independently lists App installations and requests the authenticated App. `syncInstallation()` also lists installations. These are App-JWT operations, not organization Administration operations. It obtains an installation client for the selected account. [Startup/source](https://github.com/github-community-projects/safe-settings/blob/e19444e0d69de050ba55d0262b71fcd8a98edfef/index.js#L169), [App API JWT requirement](https://docs.github.com/en/rest/apps/apps#get-the-authenticated-app)
3. `GH_ORG` limits the selected account case-insensitively and fails when unmatched. It is not a cryptographic token boundary. Leave `GH_ENTERPRISE` unset: enterprise enrichment/verification is then skipped. No org-level permissions are required merely to list the App's own installations or inspect its own registration. [Account selection and enterprise guards](https://github.com/github-community-projects/safe-settings/blob/e19444e0d69de050ba55d0262b71fcd8a98edfef/index.js#L357)
4. Full-sync loads local deployment YAML and **remote** admin settings from the default branch through the API. Local checkout of a PR branch does not make remote configuration loads use that PR's revision: full-sync passes no explicit ref. It loads override maps, runs configured org phases, enumerates installation repositories, applies scope, then repository/plugin reconciliation. [ConfigManager](https://github.com/github-community-projects/safe-settings/blob/e19444e0d69de050ba55d0262b71fcd8a98edfef/lib/configManager.js), [syncAll/updateAll](https://github.com/github-community-projects/safe-settings/blob/e19444e0d69de050ba55d0262b71fcd8a98edfef/lib/settings.js)
5. Normal mode publishes a `Safe-Settings` check to the latest admin commit. Its reporting catch logs failures without adding them to `settings.errors`; therefore successful exit alone does not prove check publication. Full-sync NOP without webhook payload reports summary/logs rather than creating PR comments/checks. [Reporting methods](https://github.com/github-community-projects/safe-settings/blob/e19444e0d69de050ba55d0262b71fcd8a98edfef/lib/settings.js#L1042)

Avoid team-name bypass actors/required-reviewer slug lookups unless adding Members read is intended; use no bypass actors or explicitly reviewed numeric actor IDs. The rulesets plugin may call team or custom-repository-role APIs for friendly-name resolution. Built-in repository role names are mapped locally, but custom names query the org role API. [Resolver](https://github.com/github-community-projects/safe-settings/blob/e19444e0d69de050ba55d0262b71fcd8a98edfef/lib/plugins/rulesets.js#L99)

## Environment and private-key format

The locked Probot `lib/create-probot.js` maps APP_ID and the private-key loader into App authentication. It does not consume `GITHUB_CLIENT_ID`/`GITHUB_CLIENT_SECRET`; installation auth options contain appId/privateKey. `WEBHOOK_SECRET` defaults, and `full-sync.js` creates no HTTP server. Thus those OAuth/webhook secrets are **not required for this batch entrypoint**. The broader upstream Actions example lists them because it is not a minimum-authentication example. [Inspected Probot distribution](https://registry.npmjs.org/probot/-/probot-14.3.2.tgz), [upstream example](https://github.com/github-community-projects/safe-settings/blob/e19444e0d69de050ba55d0262b71fcd8a98edfef/docs/github-action.md)

| Variable | Proposed value/requirement |
| --- | --- |
| `APP_ID` | Dedicated App's numeric ID; required. |
| `PRIVATE_KEY` | Protected secret containing raw PEM with real newlines, escaped-newline PEM, or exact base64 encoding of the complete PEM. Do not add surrounding quote characters to secret contents. |
| `PRIVATE_KEY_PATH` | Alternative file path if PRIVATE_KEY absent. Prefer the protected secret to avoid persistent key files. |
| `GH_ORG` | `Samwise-OS`; explicitly required by this deployment. |
| `ADMIN_REPO` | `admin`. |
| `CONFIG_PATH` | `.github`. |
| `SETTINGS_FILE_PATH` | `settings.yml`. |
| `DEPLOYMENT_CONFIG_FILE` | Absolute runner path to checked-out admin deployment YAML, rather than relying on working directory. |
| `FULL_SYNC_NOP` | Exact string `true` for preview; `false` for approved apply. Only equality to `true` activates NOP. |
| `LOG_LEVEL` | `info`; default Probot level is warn, which hides useful success summaries. Avoid debug in privileged production logs. |
| `CRON`, `GH_ENTERPRISE`, `GHE_HOST`, `GHE_PROTOCOL`, proxy variables | Leave unset for the bounded GitHub.com batch runner unless a separately reviewed need exists. |
| `GITHUB_CLIENT_ID`, `GITHUB_CLIENT_SECRET`, `WEBHOOK_SECRET` | Omit for batch full-sync. |

The key loader first honors PRIVATE_KEY, optionally decodes exact round-trippable base64, normalizes escaped newlines and validates PKCS#1/PKCS#8 PEM markers; then it considers PRIVATE_KEY_PATH or auto-discovered `.pem` files. Raw multiline PEM is supported; base64 is an option, not mandatory. [Locked loader 2.1.1 distribution, dist-src/index.js](https://registry.npmjs.org/@probot/get-private-key/-/get-private-key-2.1.1.tgz), [Safe-Settings env mapping](https://github.com/github-community-projects/safe-settings/blob/e19444e0d69de050ba55d0262b71fcd8a98edfef/lib/env.js)

## Exact configuration shape

Keep organization-wide repository defaults in `admin/.github/settings.yml`:

```yaml
repository:
  delete_branch_on_merge: true

# Initial rollout preserves unrelated live rulesets.
additive_plugins:
  - rulesets
```

**Do not put `rulesets:` at this file's root on the Free plan.** The pinned `schema/settings.json` explicitly says those are org-level rulesets, not inherited repository defaults; runtime `returnRepoSpecificConfigs()` deletes them before per-repo merge. [Global schema](https://github.com/github-community-projects/safe-settings/blob/e19444e0d69de050ba55d0262b71fcd8a98edfef/schema/settings.json#L57), [dispatch](https://github.com/github-community-projects/safe-settings/blob/e19444e0d69de050ba55d0262b71fcd8a98edfef/lib/settings.js#L2457)

For a canary, use `admin/.github/repos/<canary-name>.yml`; the filename selects the repository. Or use one `admin/.github/suborgs/public-baseline.yml` with a non-overlapping `suborgrepos` list/glob and explicit `ruleset_scope: repo`. These are examples of proposed policy shape, not approved final review/check requirements:

```yaml
# .github/suborgs/public-baseline.yml
suborgrepos:
  - approved-canary
ruleset_scope: repo
rulesets:
  - name: samwise-default-branch
    target: branch
    enforcement: active
    bypass_actors: []
    conditions:
      ref_name:
        include: ["~DEFAULT_BRANCH"]
        exclude: []
    rules:
      - type: deletion
      - type: non_fast_forward
```

The repository override uses the same `rulesets` array without `suborgrepos`/`ruleset_scope`. Add PR/status rules using the official repository ruleset REST payload, with check names/integration IDs established through actual runs. Do not include organization-only `conditions.repository_name` in repository rulesets. The pinned schemas use REST schema references; their generated `schema/dereferenced` files avoid live resolution of floating external references. [Repository schema](https://github.com/github-community-projects/safe-settings/blob/e19444e0d69de050ba55d0262b71fcd8a98edfef/schema/repos.json), [suborg schema](https://github.com/github-community-projects/safe-settings/blob/e19444e0d69de050ba55d0262b71fcd8a98edfef/schema/suborgs.json), [official payload](https://docs.github.com/en/rest/repos/rules#create-a-repository-ruleset)

Ruleset objects are matched by name, then updated by existing ID; repository-scoped `find()` filters to source_type Repository. Without additive mode, Diffable deletes live entries omitted from the desired list. `additive_plugins: [rulesets]` suppresses those removals while retaining add/update behavior. **Recommendation:** initially preserve unknown rulesets; adopt/delete them only after inventory and explicit mapping. [Rulesets](https://github.com/github-community-projects/safe-settings/blob/e19444e0d69de050ba55d0262b71fcd8a98edfef/lib/plugins/rulesets.js), [Diffable removal semantics](https://github.com/github-community-projects/safe-settings/blob/e19444e0d69de050ba55d0262b71fcd8a98edfef/lib/plugins/diffable.js)

Deployment YAML can explicitly admit `admin`:

```yaml
restrictedRepos:
  include:
    - admin
    - approved-canary
```

This replaces the default exclusions when the file exists. Runtime include filtering admits matching names; if both include/exclude exist the inspected runtime checks include first, unlike README wording. Use include-only scope. Remote global settings are merged over local deployment settings (`Object.assign`), so allowlist validation must reject `restrictedRepos` in remote settings if the local list is intended as an immutable guard. Installation repository selection remains the effective authorization boundary. [Deployment loader](https://github.com/github-community-projects/safe-settings/blob/e19444e0d69de050ba55d0262b71fcd8a98edfef/lib/deploymentConfig.js), [merge](https://github.com/github-community-projects/safe-settings/blob/e19444e0d69de050ba55d0262b71fcd8a98edfef/index.js#L30), [scope](https://github.com/github-community-projects/safe-settings/blob/e19444e0d69de050ba55d0262b71fcd8a98edfef/lib/settings.js#L2625)

## Trust, supply chain and verification conditions

- **Configuration is potentially executable code.** Both deployment YAML and remote settings can contain validator JavaScript compiled with `new Function`; NOP does not sandbox it. Accept only trusted default-branch configuration, reject validator/script and unsupported sections for this baseline, and never expose the App key while executing arbitrary PR contents. [Deployment validators](https://github.com/github-community-projects/safe-settings/blob/e19444e0d69de050ba55d0262b71fcd8a98edfef/lib/deploymentConfig.js), [remote validator compilation](https://github.com/github-community-projects/safe-settings/blob/e19444e0d69de050ba55d0262b71fcd8a98edfef/lib/settings.js#L841)
- **Run one approved default-branch workflow at a time.** Checkout admin and upstream by explicit revision; install with `npm ci --omit=dev --ignore-scripts`, not floating npm install. The lock records show no production lifecycle-script flags, making this a reasonable candidate; actual successful execution still needs verification. Scope secrets to the full-sync step, with no checkout credential persistence or untrusted PR trigger. This is a recommended hardening pattern, not an executed test.
- **Do not equate second-run idempotence with no API writes.** Non-NOP always creates a reporting check, even on zero configuration drift. Require zero settings/ruleset mutations and an empty semantic NOP plan; permit intentional audit-report writes. [Result handling](https://github.com/github-community-projects/safe-settings/blob/e19444e0d69de050ba55d0262b71fcd8a98edfef/lib/settings.js#L1121)
- **Scope/readback has failure edges.** ConfigManager treats 404 as absent; config-map loading logs and returns an empty list after some API failures. Full-sync can therefore miss configuration without a complete proof from exit status alone. Verify that expected files and target repos were actually loaded and that independent API state matches. [ConfigManager](https://github.com/github-community-projects/safe-settings/blob/e19444e0d69de050ba55d0262b71fcd8a98edfef/lib/configManager.js), [loadConfigMap](https://github.com/github-community-projects/safe-settings/blob/e19444e0d69de050ba55d0262b71fcd8a98edfef/lib/settings.js#L2699)
- **Pinning is reproducibility, not certification.** The complete transitive code was not security-audited, no vulnerability scan was executed, and this commit is not assumed to be a signed release. Its privileged dependency tree needs version/update review. Current schemas reference a floating REST description in source form; use pinned dereferenced schemas for offline validation. [Lockfile](https://github.com/github-community-projects/safe-settings/blob/e19444e0d69de050ba55d0262b71fcd8a98edfef/package-lock.json), [schemas](https://github.com/github-community-projects/safe-settings/tree/e19444e0d69de050ba55d0262b71fcd8a98edfef/schema/dereferenced)

Acceptance before expanding installation access: confirm requested App grants and installation repositories; run NOP with known one-field canary drift; inspect plan/error/output; run apply; verify changed settings and ruleset IDs with independent REST calls; verify check publication separately; run NOP again and require no settings drift; functionally reject non-bypass direct/force/deletion attempts for the selected rules; confirm an ordinary compliant PR can merge. Test App rotation/revocation and workflow secret permissions as part of authorization setup. These are recommended gates, not completed work.

## Official-CLI fallback if this candidate fails

If bounded execution fails without broad permissions, do not expand the App blindly. A minimal alternative is a default-branch Actions job that reads the same repository defaults and an explicitly versioned ruleset payload, lists current repository/rulesets with `gh api --paginate`, compares only managed fields, PATCHes changed repository fields and POSTs/PUTs a single named ruleset, then performs independent readback. Keep the same authority in `admin`, explicitly replace the Safe-Settings writer, and never run both on the same fields. Official `gh api` supports explicit methods and JSON request files. [CLI reference](https://cli.github.com/manual/gh_api), [repository API](https://docs.github.com/en/rest/repos/repos#update-a-repository), [rules API](https://docs.github.com/en/rest/repos/rules)

Tradeoff: this removes the 354-package Safe-Settings production runtime and reporting Checks permission, but Samwise-OS must own the bounded comparison/idempotence/error handling logic. It also gives up Safe-Settings overlays and plugin semantics. **This review does not recommend switching preemptively:** the inspected batch path has a plausible least-privilege configuration that should first be tested. There is no reason to provision external infrastructure for either approach.
