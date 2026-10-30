# Native repository maintenance

## Authority and managed scope

`config/organization.json` and `config/repositories.json` declare the organization
identity, managed repository names and IDs, repository purpose, template source, and
provisioning defaults. `scripts/generate_repository_settings.py` turns those manifests
into `.github/deployment-settings.yml` and one `.github/repos/<name>.yml` file for
each managed repository. Run the generator after a manifest change; CI runs its
`--check` mode and rejects generated drift. `scripts/validate_safe_settings.py`
checks the resulting Safe-Settings configuration before any reconciliation credential
is referenced. The supported set currently includes `admin`, `.github`,
`repository-template`, and `baseline-canary`.

Safe-Settings owns the shared repository defaults in `.github/settings.yml`. Its
workflow is `.github/workflows/reconcile.yml`; the source is pinned to
[`e19444e0d69de050ba55d0262b71fcd8a98edfef`](https://github.com/github-community-projects/safe-settings/tree/e19444e0d69de050ba55d0262b71fcd8a98edfef),
and the upstream lockfile SHA-256 is
`8C0EDE66EB57296B64B0A2144C9AF75553A1B271E571DCCA278606DCD6150F7B`. The workflow
installs Node 22.23.4 production dependencies with lifecycle scripts disabled before
referencing the GitHub App key.

The installed Safe-Settings App selects all repositories (installation ID
`176024067`). The program allowlist still limits reconciliation to `admin`, `.github`,
`repository-template`, and `baseline-canary`. It has Repository Administration write, Contents read, Checks
write, and Metadata read. The generated `restrictedRepos.include` allowlist is an
additional program boundary; the App installation remains the authorization boundary.
The App does not own organization settings, Actions policy, teams, or repository
creation.

## Reconciliation operation

Manual dispatch on `main` defaults to a full-sync preview (`full_sync_nop: true`). An
owner reviews that plan before selecting apply (`false`). A daily 06:17 UTC schedule
is declared enabled in the activation change, alongside a temporary five-minute
acceptance cadence. Remove the temporary cadence through a normal reviewed change
after one successful post-activation schedule run. Scheduled event `41060159080` ran while
`main` still declared the flag false; its gate correctly skipped every credentialed
step, so it is not acceptance evidence for active scheduled reconciliation. After
the activation change reaches `main`, wait for a new scheduled event and verify
successful reconciliation and readback. The schedule applies only the declared
Safe-Settings repository baseline.

Credentialed runs check that remote `main` equals the checked-out `GITHUB_SHA` before
and immediately before Safe-Settings starts, then check again after it exits. A
post-run mismatch fails the workflow and requires independent state review before a
retry because Safe-Settings reads remote configuration. The workflow serializes
manual and scheduled runs with a non-cancelling concurrency group.

The request tracer counts only managed repository configuration writes, rejects
unsupported tracing and unclassified writes, and excludes Safe-Settings check-run
publication. Full-sync console output remains in a runner-local private log and is not
uploaded. The workflow emits a sanitized reconciliation receipt containing the
revision, run identity, mode, exit code and allowlisted trace counters. It then runs
`python3 scripts/audit.py audit-managed` as a separate read-only operation. This
comparison checks the organization ID; each immutable repository ID, full name and
owner ID; declared repository defaults; and the exact named ruleset's enforcement,
bypass actors, conditions and rules. It reads ruleset details by ID. Extra unrelated
rulesets are preserved and ignored. Missing expected IDs or denied/malformed reads
are `unknown`; missing managed rules, unexpected rules, wrong parameters, inactive
enforcement, bypass actors or the wrong required-check integration are drift. Drift
or unknown fails the workflow. The receipt includes only comparison states and
difference paths, never the full inventory. Full owner inventory remains a separate
local authenticated operation under `docs/operations.md`.

The independent audit receives a short-lived token from the installed Safe-Settings
App after reconciliation. The official `actions/create-github-app-token` v3.0.0
source is pinned to the immutable commit resolved from its official GitHub tag. The
workflow derives the token's repository scope from the organization and repository
manifests. The token carries the same Administration write, Checks write, and Contents
read permissions as the established Safe-Settings integration because lower-privilege
responses omit administrative fields. The audit code issues GET requests only, but
the token itself has write capability. The action revokes the token after the job.
This does not expand the App's installation permissions. If GitHub denies a required
read, the run fails closed as unknown. No scheduled reconciliation should be treated
as accepted until a post-activation scheduled run proves these reads and the current
manifests' full managed scope.

## New repository coverage

The provisioning utility is invoked locally by the authenticated owner with the
official `gh` CLI. It validates the remote administration workflow revision, org
identity and owner role, then creates a new repository or reconciles existing
metadata. Changes to shared files are proposed on a deterministic branch and normal
pull request; the utility does not push those files directly to `main`. The desired
repository must be added to `config/repositories.json` and run through the generator
before its baseline ruleset enters reconciliation.

Newly created repositories first return an adoption-required ID. Record the ID in the
manifest, re-run identity checks, and review the generated settings. If Safe-Settings
must manage the new repository, the organization owner must add it to the App's
selected installation repositories and verify that selection through GitHub. A
manifest edit alone does not grant App access. Existing repositories with a missing
or mismatched ID are never adopted silently. Deletion, archival, renaming, transfer,
or visibility conversion stays outside routine reconciliation.

## Codespaces and local workspaces

The organization template carries a checked-in `.devcontainer/devcontainer.json`
with an immutable base-image digest. GitHub uses that repository configuration when
creating a Codespace from the template. This provides a reproducible repository
default; it does not create an organization-wide setting. On GitHub Free, Codespaces
are user-owned and billed to their creator, so org-level Codespaces spending, machine,
retention and access policies are not controls available to this organization plan.
The organization does not currently pay for or govern these user-owned Codespaces.
Local Git worktrees likewise remain developer-host state; GitHub rules govern pushed
commits and pull requests, not local directories.

## Live evidence and acceptance

The authenticated reconciliation evidence recorded in
[`reconciliation-evidence-2026-10-30.md`](reconciliation-evidence-2026-10-30.md)
shows a successful preview (`41008940440`), first apply (`41008996205`), and
zero-write second apply (`41009078745`) for `admin` and `baseline-canary`. It also
records independent readback of their repository defaults, canary ruleset `26186884`,
and Safe-Settings check publication. That is evidence for those two repositories and
that revision. Later authenticated runs applied all four repositories and proved
zero-write idempotence; see the linked rollout evidence. Scheduled event `41060159080`
occurred while the `main` manifest still had the activation flag false, so its gate
skipped credentialed work. The first post-activation scheduled run remains unobserved.
The current organization 2FA-disabled member filter is empty, the outside-collaborator
inventory is empty, and the owner account has 2FA enabled. The organization-level
requirement is now enabled; owner-authenticated readback matches the declared value.
Future drift must be corrected through GitHub security settings because the documented
organization REST update request does not accept this field.
