# Operating procedure

## Validate declarations and inspect live state

Use Python 3.11+ and the official GitHub CLI. Run these secretless local checks before
publishing a manifest change:

```powershell
python scripts/audit.py validate
python scripts/generate_repository_settings.py --check
python scripts/validate_safe_settings.py
```

`python scripts/audit.py audit-managed --output .local/managed-audit.json` reads only
the declared repositories, checks the organization and immutable repository identities,
compares repository defaults, and reads back exact named ruleset details. Its receipt
contains comparison states and difference paths only. It returns 0 for match, 2 for
drift, 3 for an unknown read, and 4 for invalid configuration or execution failure.
The separate `python scripts/audit.py audit --output .local/observed-state.json` is a
full owner-authenticated inventory of membership, installations, organization policies
and repository summaries. Keep that full report in ignored `.local/`; it includes
access and inventory data and must not be published unchanged. A GitHub Free 403 on
organization rulesets is reported as unsupported plan, while other denied reads remain
unknown.

The secretless `governance` workflow runs the `scripts/doctor.py` receipt checks on PRs
and pushes. Its receipt proves the exact checks and checkout identity recorded there;
it does not prove authenticated GitHub policy behavior. The reusable
`.github/workflows/repository-baseline.yml` publishes the `baseline / standards` check.
Use live acceptance records in `docs/acceptance.md` for enforcement claims.

## Provision a repository

`config/repositories.json` is the declaration for repository names, stable IDs,
visibility, purpose, template status and source. `scripts/provision.py` is run locally
by an active organization owner with authenticated `gh`:

```powershell
python scripts/provision.py --workflow-sha <40-character-admin-main-sha>
python scripts/provision.py --workflow-sha <40-character-admin-main-sha> --apply
```

The workflow SHA must identify trusted code on remote `admin/main`. The provisioner
checks organization ID and owner role, inventories existing repositories and validates
stable IDs before mutation. It creates a missing repository once, records the observed
ID as adoption-required, and proposes shared-file changes as a deterministic branch
and ordinary pull request. It never pushes shared files to `main` or force-updates an
unexpected branch. Review and merge the proposal through repository controls; rerun
against the newly observed base only when its result says it is needed. A pending
content pull request is not convergence.

Before a new repository enters Safe-Settings reconciliation, add its immutable ID to
the manifest, regenerate settings, and have the owner add the repository to the
installed App's selected set. Verify that selection in GitHub. App installation
selection and the generated program allowlist are independent gates. The provisioner
does not delete repositories, change visibility, rename or transfer repositories, or
silently adopt a same-name repository with a different ID.

## Reconcile shared repository settings

`.github/workflows/reconcile.yml` is the Safe-Settings writer. Manually dispatch it
from `main` with `full_sync_nop: true` to preview. Review the plan, then dispatch
`false` to apply. It validates manifests and generated config before credential use,
checks the trusted `main` SHA twice before the writer and once after, and emits a
sanitized request receipt plus independent post-apply readback. Repository settings
and named rulesets are read after the Safe-Settings step even when that step fails; a
drift or unknown read fails the job.

The readback uses a short-lived token from the installed Safe-Settings App, limited
to the manifest-derived repository list and carrying the same Administration write,
Checks write, and Contents read permissions as the established Safe-Settings
integration. GitHub omits administrative fields from lower-privilege responses. The
auditor issues GET requests only, but the token itself has write capability. The
workflow pins the official `actions/create-github-app-token` v3.0.0 tag target by
commit and lets the action revoke the token at job completion. An unselected new
repository causes token creation or readback to fail; update and verify the App's
selected repositories as a separate owner operation.

The daily 06:17 UTC schedule is protected by the versioned
`safe_settings.schedule_enabled` flag, currently false. The gate executes before any
step references the App key. Keep it disabled until full four-repository readback,
idempotent zero-write rerun, and canary functional acceptance are recorded. Updating
that flag requires an ordinary reviewed change on `main`. The schedule owns only
shared repository settings; organization defaults, Actions policies, team membership
and repository grants stay in the separate authenticated owner CLI controller.

Safe-Settings credentials are environment-scoped to `governance`, whose allowed
deployment branch must be `main`. Do not expose them to PR code, `pull_request_target`,
arbitrary refs, or general-purpose jobs. The private key belongs in the approved
GitHub Environment secret store; never place it in manifests, logs or receipts. An
environment name in YAML alone does not establish its GitHub deployment protection;
check the environment's live branch restrictions before claiming that control.

Organization policy and team operations use the official API via
`python scripts/organization.py plan` followed by `apply` only when the proposed
diff is intended. The controller verifies organization ID, active owner identity and
role, reads before writing, records partial failures and reads back each policy.
Fields not supported by the documented update request are reported as manual-only
drift. It only adds explicitly listed existing users, does not accept invitations or
remove unrelated members, and defers a repository grant until that repository exists.
2FA enforcement remains pending until the owner completes and verifies enrollment.

## Recovery and retained evidence

Before changing access controls, verify owner enrollment and recovery access. Rollback
only fields touched by the failed operation after reading their current state; do not
restore from a whole organization dump. For a bad ruleset, use the verified owner's
administrative path to disable that specific rule and preserve the failed run and PR
evidence. For a compromised App, disable the writer workflow, suspend or remove its
installation and rotate its credentials, then read state back before re-enabling.
Recovery is not claimed tested until a recorded exercise proves it.

`.local/` is ignored and holds temporary diagnostic output, not a backup. Any retained
local backup in this Windows workflow belongs under `E:\backups\Codex`; verify its
hash and confirm local-source removal before treating externalization as complete.
