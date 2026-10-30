# Native repository maintenance

Safe-Settings owns the shared repository defaults in `.github/settings.yml`.
The bounded batch runner is `.github/workflows/reconcile.yml`; its only trigger is
manual dispatch on `main`, and its deployment environment is `governance`. The
environment must restrict deployment branches to `main` and contain
`SAFE_SETTINGS_APP_ID` as a variable and `SAFE_SETTINGS_PRIVATE_KEY` as a secret.
The App installation selects four repositories: `admin`, `.github`,
`repository-template`, and `baseline-canary`. It grants only repository
Administration write, Contents read, Checks write, and Metadata read.
Safe-Settings reconciliation is separately limited to `admin` and
`baseline-canary` by its configuration allowlist.

The workflow pins Safe-Settings to
[`e19444e0d69de050ba55d0262b71fcd8a98edfef`](https://github.com/github-community-projects/safe-settings/tree/e19444e0d69de050ba55d0262b71fcd8a98edfef), checks the lockfile SHA-256
`8C0EDE66EB57296B64B0A2144C9AF75553A1B271E571DCCA278606DCD6150F7B`, and installs
Node 22.23.4 production dependencies with lifecycle scripts disabled. The
validator rejects unapproved settings, executable validator sections, alternate
repository/suborg config paths, symlinks, and any deviation from the exact
canary ruleset payload before the App key is exposed. The shared candidate in
`config/default-branch.ruleset.json` remains disabled; only the canary override
is prepared for active enforcement.

The workflow checks that GitHub's current `main` commit is the checked-out
trusted commit before and after full-sync because Safe-Settings loads remote
configuration from the default branch. A small `undici:request:create` preloader
prints a sanitized mutation-request count and fails when tracing is unsupported
or sees an unclassified write. It records only repository PATCH and ruleset
POST/PUT/DELETE requests for `admin` and `baseline-canary`; it never logs request
paths, headers, bodies, query strings or tokens. The local fetch fixture proves
that configuration writes are counted while check-run reporting is excluded.
The pre/post SHA checks still leave a narrow race between the precheck and
Safe-Settings' remote config read. A postcheck failure means state must be read
back independently before any retry.

`restrictedRepos.include` currently limits reconciliation to `admin` and
`baseline-canary`. The App installation is the actual authorization boundary;
the YAML allowlist and `GH_ORG` are additional program-level limits. Expanding
reconciliation to `.github` or `repository-template` requires a deliberate update
to the allowlist, validator and acceptance evidence; those repositories are
already selected in the App installation.

## Live evidence and acceptance sequence

The real canary PR run `40618226036` failed the `baseline / standards` check
from GitHub Actions App `15368` because `.editorconfig` was deliberately empty.
The same check context passed on canary main at run `40618028804`. PR
[`#1`](https://github.com/Samwise-OS/baseline-canary/pull/1) remains open and
unmerged as the negative fixture for a later cannot-merge assertion. Its file
must be restored before a normal acceptance PR is merged.

The first authenticated NOP, run `40619654778` on admin main SHA
`3fe39dc3316255916b65f83e12e094383f8e1efd`, completed successfully after the
owner installed the App key in the `governance` environment. Safe-Settings
logged installation `176024067`, one successful installation sync, and four
planned repository-setting changes across `admin` and `baseline-canary`. Because
the input was NOP, it did not apply those changes or the candidate ruleset. This
run proves the authenticated App path reached both allowlisted repositories; the
owner separately confirmed the selected installation set of four repositories
through GitHub's installation UI/API. The earlier NOP attempt failed before API
authentication because the runner received no private-key value; it is not
acceptance evidence.

1. Keep `SAFE_SETTINGS_APP_ID` and `SAFE_SETTINGS_PRIVATE_KEY` scoped to the
   `governance` environment, whose deployment policy allows `main` only.
2. Review the successful NOP plan, then apply the reviewed baseline. Independently
   read back repository settings and the exact ruleset payload after apply; confirm
   the `Safe-Settings` check publication separately.
3. Run NOP again. Require no planned settings or ruleset changes and a supported
   mutation receipt with zero managed configuration-write requests. The check
   reporting writes are excluded from that receipt by design.
4. Confirm the canary active ruleset and attempt to merge PR #1 without owner
   bypass. The failing `baseline / standards` check must block merge. Then restore
   `.editorconfig`, observe a green check, and verify a normal squash PR can merge.
5. Only after canary recovery and an accepted second pass should reconciliation
   expand to `.github` or `repository-template`, or a scheduled trigger be added.

There is intentionally no scheduled trigger yet. Add one only after canary apply,
independent readback and the second-pass NOP are accepted. The existing
`scripts/audit.py` remains an independent read-only observer; it does not write
repository state. The main workflow's current trusted revision is
`3fe39dc3316255916b65f83e12e094383f8e1efd`; local changes for the active canary
ruleset, validator hardening, mutation receipt and exact Node pin are prepared
for a follow-up PR and have not been applied to GitHub.
