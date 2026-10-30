# Governance validation receipts

The secretless `governance` job runs `python3 scripts/doctor.py --output .local/validation-receipt.json`. The doctor runs the existing organization configuration validator, generated repository-settings `--check`, Safe-Settings validator and complete unittest suite. It performs no authenticated GitHub reads, writes, model calls or repair. Live read-only organization audit remains a separate, explicit operation described in `docs/operations.md`.

Receipt schema version 1 records check-contract version `2026-10-30.2`, PR source head SHA (or workflow SHA outside PRs), actual checkout SHA, whether the local worktree was dirty, UTC creation time, platform, available GitHub repository/run/ref/PR identity, aggregate outcome, diagnostics, and ordered per-check command, expected/actual result, exit code, duration, pass/fail/unknown status, reason, retry count, timeout bound and evidence path. Full command output is kept in separate `.local/validation-logs/*.txt` files. These logs are diagnostic evidence for these known secretless commands; the doctor does not accept arbitrary commands or logs as instructions. Do not add credentials to this workflow or include sensitive inventory in artifacts.

The required check inventory is fixed in `scripts/doctor.py`: organization config, generated repository settings, Safe-Settings config, and unittests. The doctor runs every check after a command failure where possible and writes the receipt before returning nonzero. A nonzero command fails. A zero-exit unittest run with missing/malformed summary, zero executed tests, or any skipped test makes that required check `unknown`; a nonzero unittest exit remains a failure even if its summary is missing. Failure or unknown prevents an aggregate pass. If Git HEAD cannot be established, the receipt is unknown and contains no check results. CI's always-running summary calls out missing evidence, and the artifact step uploads the receipt and logs even after validation failure; missing files fail artifact publication. Artifact retention is 14 days.

Evidence records checkout HEAD, PR source head and base where provided, workflow SHA and run metadata. The dirty flag distinguishes local edits from the committed checkout. These fields identify the revision inspected; they do not prove that a PR-authored workflow or script is trusted, that a live ruleset requires this check, or that intended actors experience effective enforcement. PR validation receives only `contents: read` and no repository secrets. Treat its receipt and logs as evidence, never as trusted repair instructions. The workflow uses GitHub's official `actions/upload-artifact` action pinned to commit `ea165f8d65b6e75b540449e92b4886f43607fa02`, resolved from its official `v4` ref.

Local use:

```powershell
python scripts/doctor.py --output .local/validation-receipt.json
```

The output path must resolve beneath ignored `.local/`. Exit codes are 0 for pass, 1 for fail, and 2 for unknown or invalid output configuration. Inspect receipt and log artifacts for diagnosis. This command does not replace authenticated acceptance tests in `docs/acceptance.md`.
