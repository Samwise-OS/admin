# Safe-Settings repository ruleset payload at the reviewed pin

**Scope:** source commit [`e19444e0d69de050ba55d0262b71fcd8a98edfef`](https://github.com/github-community-projects/safe-settings/tree/e19444e0d69de050ba55d0262b71fcd8a98edfef). This note answers what that version routes to GitHub's repository-ruleset API; it is not evidence of live installation, acceptance, or enforcement.

## Accepted configuration shape

The pinned implementation has no independent JSON Schema or allowlist for ruleset fields. It takes each entry in `rulesets`, resolves its supported human-readable actor/reviewer names, then submits the remaining object through GitHub's repository ruleset create/update endpoints. Therefore the authoritative payload contract is GitHub's repository Rules API schema, subject to Safe-Settings' preprocessing. The repository plugin selects scope `repo` by default and calls `GET/POST/PUT/DELETE /repos/{owner}/{repo}/rulesets`. [Pinned rulesets plugin](https://github.com/github-community-projects/safe-settings/blob/e19444e0d69de050ba55d0262b71fcd8a98edfef/lib/plugins/rulesets.js#L30-L55) [Pinned repository endpoint paths](https://github.com/github-community-projects/safe-settings/blob/e19444e0d69de050ba55d0262b71fcd8a98edfef/lib/plugins/rulesets.js#L202-L230) [GitHub create repository ruleset](https://docs.github.com/en/rest/repos/rules#create-a-repository-ruleset)

For a repository override, the practical structure is:

```yaml
rulesets:
  - name: samwise-default-branch
    target: branch
    enforcement: disabled # GitHub API values: disabled, active, evaluate
    bypass_actors: []
    conditions:
      ref_name:
        include: ["~DEFAULT_BRANCH"]
        exclude: []
    rules:
      - type: deletion
      - type: non_fast_forward
      - type: pull_request
        parameters:
          allowed_merge_methods: [squash]
```

The ruleset object follows the API's `name`, optional `target` (default `branch`; supported `branch`, `tag`, `push`), required `enforcement`, `bypass_actors`, `conditions`, and `rules` fields. `conditions.ref_name.include`/`exclude` are arrays of ref names or patterns; `~DEFAULT_BRANCH` and `~ALL` are special includes. [GitHub create repository ruleset payload](https://docs.github.com/en/rest/repos/rules#create-a-repository-ruleset)

Safe-Settings recognizes `ruleset_scope` values `repo` and `org`; absent value defaults to `repo`. For suborg configuration, file-local `ruleset_scope` overrides the org-wide default. Invalid values warn and fall back to `repo`. `org` scope for a suborg is only effective when `suborgproperties` is a nonempty array; otherwise it falls back to repository scope. Org-scoped entries are aggregated into one organization-ruleset sync with repository-property conditions. Repository scope is the appropriate mode for this project's per-repository configuration. [Pinned scope selection and fallback](https://github.com/github-community-projects/safe-settings/blob/e19444e0d69de050ba55d0262b71fcd8a98edfef/lib/settings.js#L2208-L2224) [Pinned org-scope aggregation](https://github.com/github-community-projects/safe-settings/blob/e19444e0d69de050ba55d0262b71fcd8a98edfef/lib/settings.js#L2235-L2298)

`suborgrepos` belongs in a `.github/suborgs/<name>.yml` config alongside `rulesets`; it is an array of repository-name glob patterns used to select the repositories inheriting that suborg config. The repo-specific resolver tests each pattern against the repository name. Multiple matching suborg files targeting one repository cause a conflict rather than a merge. [Pinned suborg config expansion](https://github.com/github-community-projects/safe-settings/blob/e19444e0d69de050ba55d0262b71fcd8a98edfef/lib/configManager.js) [Pinned repo-name glob matching](https://github.com/github-community-projects/safe-settings/blob/e19444e0d69de050ba55d0262b71fcd8a98edfef/lib/settings.js)

## Enforcement and rule parameters

The repository REST API accepts `enforcement: disabled`, `active`, or `evaluate`. `disabled` stores a non-enforcing ruleset; `active` applies it. `evaluate` is documented as Enterprise-only, so it is not a viable Free-plan setting. The rules-for-branch endpoint omits rulesets in `evaluate` or `disabled`, which is why reading a ruleset object alone and inspecting effective rules answer different questions. [GitHub create repository ruleset](https://docs.github.com/en/rest/repos/rules#create-a-repository-ruleset) [GitHub get rules for a branch](https://docs.github.com/en/rest/repos/rules#get-rules-for-a-branch)

For `required_status_checks`, parameters include `required_status_checks` (an array of `{context, integration_id?}`), `strict_required_status_checks_policy`, and optional `do_not_enforce_on_create`. A status context is required; `integration_id` pins the expected producer. Safe-Settings contains special override handling for `required_status_checks` when reconciling partial external overrides, but it otherwise forwards API-compatible rule payloads. [GitHub required status checks schema](https://docs.github.com/en/rest/repos/rules#create-a-repository-ruleset) [Pinned rulesets override handling](https://github.com/github-community-projects/safe-settings/blob/e19444e0d69de050ba55d0262b71fcd8a98edfef/lib/plugins/rulesets.js#L5-L11)

For `pull_request`, supported parameters include `allowed_merge_methods` (one or more of `merge`, `squash`, `rebase`), `dismiss_stale_reviews_on_push`, review-dismissal restrictions, required approval count, code-owner review, last-push approval, and required review-thread resolution. The API describes `pull_request` as requiring changes to be submitted via a pull request before merge. [GitHub pull request rule schema](https://docs.github.com/en/rest/repos/rules#create-a-repository-ruleset)

## `allowed_merge_methods`

**Yes.** The exact field is `rules[].parameters.allowed_merge_methods` on a rule whose `type` is `pull_request`; it is not a top-level repository-ruleset field. GitHub documents the three accepted strings and requires at least one. The pinned Safe-Settings code does not filter this parameter out: it sends the config entry to the create/update repository-ruleset endpoint. The repository's current sample payload uses `["squash"]`, matching this shape. [GitHub pull request parameters](https://docs.github.com/en/rest/repos/rules#create-a-repository-ruleset) [Pinned rulesets create/update calls](https://github.com/github-community-projects/safe-settings/blob/e19444e0d69de050ba55d0262b71fcd8a98edfef/lib/plugins/rulesets.js#L259-L302) [Current repository sample](../../config/default-branch.ruleset.json)

**Boundary:** this concludes payload support only. Whether GitHub accepts a particular rule/parameter under the organization's current plan and repository state, and whether the resulting ruleset is active and effective, must be confirmed by authenticated API readback and behavior acceptance.
