# Native repository maintenance

Safe-Settings owns the shared repository defaults in `.github/settings.yml`.
The bounded batch runner is `.github/workflows/reconcile.yml`; its only trigger is
manual dispatch on `main`, and its deployment environment is `governance`. The
environment must restrict deployment branches to `main` and contain
`SAFE_SETTINGS_APP_ID` as a variable and `SAFE_SETTINGS_PRIVATE_KEY` as a secret.
The App installation is limited to `admin` and `baseline-canary` and grants only
repository Administration write, Contents read, Checks write, and Metadata read.

The workflow pins Safe-Settings to
[`e19444e0d69de050ba55d0262b71fcd8a98edfef`](https://github.com/github-community-projects/safe-settings/tree/e19444e0d69de050ba55d0262b71fcd8a98edfef), checks the lockfile SHA-256
`8C0EDE66EB57296B64B0A2144C9AF75553A1B271E571DCCA278606DCD6150F7B`, and installs
Node 22 production dependencies with lifecycle scripts disabled. The validator
rejects unapproved settings, executable validator sections, allowlist changes,
and active or bypassable candidate rulesets before the App key is exposed. The
workflow also confirms that GitHub's current `main` commit is the checked-out
trusted commit because Safe-Settings loads configuration from the default branch.

`restrictedRepos.include` currently limits reconciliation to `admin` and
`baseline-canary`. The App installation is the actual authorization boundary;
the YAML allowlist and `GH_ORG` are additional program-level limits. Expansion to
`.github` or `repository-template` requires a deliberate update to the allowlist,
validator, App installation selection and acceptance evidence.

## Acceptance sequence

1. Confirm the environment branch policy and exact App installation/repository
   selection through GitHub. Keep the PEM only in the `governance` environment.
2. Dispatch the workflow with `full_sync_nop=true`. Confirm the expected two
   repositories were discovered and inspect the proposed defaults and errors.
   NOP is a preview, not a sandbox for untrusted configuration.
3. After reviewing the preview, dispatch with `full_sync_nop=false`. Independently
   read back the repository settings and confirm a `Safe-Settings` check was
   published. A successful process exit alone does not prove check publication.
4. Dispatch a second NOP run. Require no settings or ruleset drift. A normal
   apply run may still create an intentional reporting check, so this is
   configuration idempotence rather than zero API writes.
5. Before activating branch protection, observe the canary's actual CI check
   names. Add only reviewed checks and test direct-push rejection, ordinary PR
   merge, and recovery behavior. Do not enable the candidate ruleset while its
   enforcement remains `disabled`.

There is intentionally no scheduled trigger yet. Add one only after canary apply,
independent readback and the second-pass NOP are accepted. The existing
`scripts/audit.py` remains an independent read-only observer; it does not write
repository state.
