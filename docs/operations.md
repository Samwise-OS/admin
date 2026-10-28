# Operating procedure

## Read-only validation

Use Python 3.11+ and an already authenticated official GitHub CLI. Invoke
`python scripts/audit.py validate` from this repository to validate the declarations.
Invoke `python -m unittest discover -s tests -v` to exercise the public API boundary
adapters and deterministic behavior. Invoke `python scripts/audit.py audit --output
.local/observed-state.json` for fresh authenticated inventory and read-only comparison.
Use `python scripts/organization.py plan` to show policy writes without mutation, then
`python scripts/organization.py apply` to reconcile authorized organization policies,
team membership and grants. The controller verifies organization ID, owner identity and
role before writing; it reads first, records partial failures, and reads back each
policy. Fields absent from the documented organization update request are reported as
manual-only drift and are not replayed as ineffective writes. The team synchronizer
defers a grant until the declared repository exists and applies it on a later run.

Sanitized execution evidence is written to ignored `.local/org-policy-results.json`.
It is local diagnostic evidence containing organization access state; do not publish it.

Exit codes: 0 means the compared settings match (or local validation passed), 2 means
observed settings drift, 3 means at least one read is unknown, and 4 means an execution
or configuration error. An incomplete result can also contain drift. A matching settings
report is never operational acceptance. An organization rulesets 403 explicitly
requiring GitHub Team is classified as `unsupported_plan`; other denied reads remain
unknown. The utility does not compare effective rules, membership intent, installations,
template inheritance or functional CI behavior;
these remain separate acceptance tests. Repository ruleset lists are observations only.

The script explicitly issues GET requests against github.com, verifies the organization
ID, completely paginates array inventories and aborts if a returned repository leaves
the named organization. Missing fields differ from null/false. It does not treat a denied
read as absence. Evidence output must stay under `.local/`, which is gitignored and
contains potentially private membership/repository data. Do not publish it unchanged.

## Approved provisioning contract

After owner decisions and canary validation, a repository request must declare its
name, visibility, purpose, owners/team grants, template commit and applicable CI profile.
Use a versioned per-repository manifest reviewed in `admin`. Validate reserved names,
organization identity, plan entitlement and requested privileges before creating anything.

Use the official create-from-template API. Query exact owner/name first; a 403/404 is
not sufficient evidence of absence without established authenticated visibility. If
the repository already exists, compare its stable ID with the managed inventory and
reconcile only approved fields. Record a newly created ID immediately so retries can
resume after partial completion. Never repeat create blindly after a network timeout.

Apply explicit repository settings, visible team grants and tested rules separately:
template generation copies files, not the complete administrative state. Install
CODEOWNERS in each repository; it is not an inherited community default. Observe the
expected successful CI check before making it required. Verify readback, inherited
community guidance and a real normal contributor PR. Repeating the operation must
create no duplicate repository/team/ruleset and produce no semantic updates.

For archived repositories, preserve history and omit routine active-repository updates.
Treat an undeclared repository as unmanaged inventory requiring review, not something
to delete. Licensing, renaming, transfers and visibility changes are explicit decisions.

## Reconciliation activation

Safe-Settings owns shared repository settings after its separate source/grant review
and installation approval. Its pinned source must be checked out by immutable commit,
its lockfile must be honored, and dependency installation must occur before credentials
are exposed. Do not grant its upstream example manifest wholesale. Use canary-only
include scope first. Test partial failures and exit status; dry-run is not acceptance.

Organization defaults and Actions policy are separate approved official API operations.
Capture original managed values, submit only intended fields, then GET each resource.
Actions policy PUT sends its complete required body, including unchanged
`enabled_repositories`. Apply selected mode before selected-action restrictions. Deletion
and visibility member-privilege controls are not part of the documented organization
update request body; verify their UI changes with authenticated GET readback.

The declared `Maintainers` team is synced idempotently. Only explicitly listed existing
users are added; the controller does not accept invitations or alter unrelated members.
Repository grants are applied only for declared repositories that already exist.

Privileged execution must use reviewed default-branch code with an owner-approved
manual trigger initially. Do not use PR code, `pull_request_target`, arbitrary workflow
dispatch refs, inherited secrets, or unbounded App installations. An Environment name
alone does not prove protected execution; verify the actual protection and actor path.

## Recovery and evidence

Before access restrictions, verify owner enrollment/recovery and record original
managed values. Do not serialize keys or tokens. Keep rollback limited to affected
settings, with owner access confirmed before and after. A whole organization dump is
not a safe automatic restore input.

For a bad rule, use the verified owner's administrative path to disable only the
identified rule and preserve the failed PR/run evidence. For a compromised App, disable
the writer workflow, suspend/remove its installation and rotate credentials under owner
authority. Re-run readback before re-enabling. No recovery operation is claimed tested yet.

Any future retained local backup for this Windows workflow belongs under
`E:\backups\Codex`; hash-verify it before treating it as a recovery artifact. The ignored
`.local` report is temporary audit evidence, not a backup.
