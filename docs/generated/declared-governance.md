# Declared Samwise-OS governance (generated)

<!-- GENERATED: python3 scripts/docs_sync.py --write; do not edit by hand. -->

This page projects version-controlled declarations, **not** observed GitHub
enforcement or device-side acceptance. See [operational acceptance](../acceptance.md)
for independently recorded live evidence.

## Managed repository identities

| Repository | Immutable ID | Purpose |
| --- | --- | --- |
| `admin` | 1436238530 | Organization control plane |
| `.github` | 1436487227 | Samwise-OS public community defaults and engineering guidance |
| `android` | 1443683343 | Canonical governed offline Android USB provisioning and fleet acceptance |
| `baseline-canary` | 1436487640 | Retained canary repository for Samwise-OS organization controls |
| `bootstrap-acceptance-20261030` | 1439988641 | Retained acceptance repository for fresh Samwise-OS provisioning |
| `repository-template` | 1436487455 | Canonical public repository template for Samwise-OS engineering |

**Declared managed repository count:** 6

## Organization policy

| Field | Declared value |
| --- | --- |
| `default_repository_permission` | `"none"` |
| `members_can_change_repo_visibility` | `false` |
| `members_can_create_private_repositories` | `false` |
| `members_can_create_public_repositories` | `false` |
| `members_can_create_repositories` | `false` |
| `members_can_delete_repositories` | `false` |
| `two_factor_requirement_enabled` | `true` |

## GitHub Actions policy

| Field | Declared value |
| --- | --- |
| `allowed_actions` | `"selected"` |
| `enabled_repositories` | `"all"` |
| `sha_pinning_required` | `true` |

## Workflow token policy

| Field | Declared value |
| --- | --- |
| `can_approve_pull_request_reviews` | `false` |
| `default_workflow_permissions` | `"read"` |

## Repository provisioning defaults

| Field | Declared value |
| --- | --- |
| `archive_requires_owner_approval` | `true` |
| `default_branch` | `"main"` |
| `default_visibility` | `"public"` |
| `delete_repositories` | `false` |
| `name_pattern` | `"^[a-z0-9]+(?:-[a-z0-9]+)*$"` |
| `reserved_names` | `["admin", ".github"]` |
| `review_approvals` | `0` |

## Repository settings reconciliation

| Field | Declared value |
| --- | --- |
| `app_id` | `5504298` |
| `authenticated` | `true` |
| `candidate_commit` | `"e19444e0d69de050ba55d0262b71fcd8a98edfef"` |
| `installation_id` | `176024067` |
| `installed` | `true` |
| `last_apply_run` | `41561843117` |
| `last_nop_run` | `41008940440` |
| `permissions` | `{"administration": "write", "checks": "write", "contents": "read", "metadata": "read"}` |
| `repositories` | `["admin", ".github", "repository-template", "baseline-canary", "bootstrap-acceptance-20261030", "android"]` |
| `repository` | `"github-community-projects/safe-settings"` |
| `repository_selection` | `"all"` |
| `schedule_enabled` | `true` |
| `source_review_complete` | `true` |

## Shared repository defaults

| Field | Declared value |
| --- | --- |
| `allow_merge_commit` | `false` |
| `allow_rebase_merge` | `false` |
| `allow_squash_merge` | `true` |
| `delete_branch_on_merge` | `true` |
| `has_issues` | `true` |
| `has_wiki` | `false` |

## Reconciliation trigger

- Scheduled cron expression: `17 6 * * *`
- Scheduled activation declaration: `true`

## Canonical source blob identities

Any change to an authoritative declaration source changes its Git blob ID
fingerprint, requiring this generated page to be updated in the same PR.

| Canonical source | Git blob SHA-1 |
| --- | --- |
| `config/organization.json` | `177815a63f010920769472fdf2db01e3df1ed6b4` |
| `config/repositories.json` | `766540dc590b3587f2183f0abd02fae560355304` |
| `.github/settings.yml` | `038717a647afa09db1850a3f23c87ee0f24a648e` |
| `.github/workflows/reconcile.yml` | `642cd6b82bdf811279ee2899ca7df06bf82f0df7` |

Regenerate with: `python3 scripts/docs_sync.py --write`
