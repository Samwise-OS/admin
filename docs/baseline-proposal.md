# Samwise-OS baseline and applied policy

Date: 2026-10-28. Status: **POLICY PARTIALLY APPLIED; OPERATIONAL ACCEPTANCE OPEN**.

## Scope and authority

The owner authorized completing the GitHub organization bootstrap on GitHub Free with
public repositories, routine autonomous decisions, and a solo-owner review count of
zero. Application and platform implementation remain out of scope. Human action is
required only for real authentication gates.

`config/organization.json` is authoritative for organization defaults, Actions policy,
the Maintainers team, and its repository grants. `admin/.github/settings.yml` retains
shared repository settings authority. Safe-Settings remains a separate repository
settings executor; it has not been source-audited, installed or authenticated. No field
has two writers.

## Applied and remaining controls

- Base repository permission is `none`; non-owner repository creation is disabled,
  including public and private creation.
- Organization Actions allow only GitHub-owned actions, disallow verified-marketplace
  actions and patterns, and require full-SHA pins. Workflow tokens remain read-only and
  cannot approve pull requests.
- The `Maintainers` team exists with `Samwise-x` as maintainer and `maintain` access to
  `admin`, `.github`, `repository-template` and `baseline-canary`. Grants are applied
  automatically by a later reconciliation once a declared repository exists.
- The `admin/governance` environment exists with an exact `main` branch deployment
  policy, no required reviewers, and no protected-branch-only policy. It is a
  configuration fact; privileged workflow execution is not yet accepted.
- Repository deletion and visibility-change restrictions now both read false after the
  owner changed the GitHub UI settings. The organization REST update endpoint accepts
  PATCH but does not apply these fields; its documented body omits them. The controller
  reports any future drift as manual-only and does not replay ineffective writes.
- Organization 2FA enforcement remains off until the owner completes 2FA enrollment.
- Organization rulesets are not required on GitHub Free. The live rulesets endpoint
  returned an explicit 403 upgrade requirement; use public per-repository rulesets.

## Repository and solo-owner defaults

Keep existing repositories and history. New repository requests default to public,
`main`, kebab-case names, and zero required independent approvals. Owners retain
administrative authority; visible team grants make maintainership explicit. No pending
invitation is removed or changed. The pending `BVEnterprisess` direct-member invitation
is preserved.

Per-repository branch rules and required checks still need the canary suite before
activation. Free-plan named checks retain the workflow-writer trust boundary. No claim
of immutable workflow identity or full operational acceptance is made.

## Remaining gates

1. Owner completes 2FA enrollment; then inventory all current members/collaborators and
   enable organization enforcement only if everyone is compliant.
2. Safe-Settings App inspection, selected installation and key/variable setup remain
   separately gated and are being handled outside this policy controller.
3. Execute the canary enforcement, idempotence, failure and recovery suite. Record
   evidence before revising acceptance status.

The observed-state document preserves the initial pre-write audit separately from
current applied readback. `.local/org-policy-results.json` contains sanitized controller
evidence; it is ignored and must not be published unchanged.
