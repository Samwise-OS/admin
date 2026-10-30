# Samwise-OS verification checkpoint — 2026-10-30

This is an evidence record, not a substitute for current authenticated GitHub state.
Before further mutation, recheck remote main, PR heads, configuration and audit results.

## Deployed and verified

- PRs [#7](https://github.com/Samwise-OS/admin/pull/7), [#8](https://github.com/Samwise-OS/admin/pull/8) and [#9](https://github.com/Samwise-OS/admin/pull/9) are merged. The tested executor/readback code is on main at `c5f14882817a06f1982b4fcd34d429477b3061a8`.
- All four declared repository identities, merge defaults and active named rulesets matched in retained App-authenticated readback and separate owner-authenticated readback.
- Standards updates merged through green, exact-head ordinary PRs in `.github` (#1), `repository-template` (#1), and `baseline-canary` (#5). The next provisioning plan had no content, metadata, label or vulnerability-reporting changes. Source workflow revision: `9811e2dba4ecb5e4cb6564b385a7f6b4e46d6e2b`.
- Organization policy and exact team-grant reconciliation repeated without writes. All seven canonical labels and private vulnerability reporting have reproducible provisioning paths.
- The latest source suite passed **79 tests**, zero skips. Required CI retains versioned receipts, complete diagnostics and fallback evidence for early failure. Standards and Spec reviews were performed separately; no hard blockers remained.
- Full all-repository apply [41011641487](https://github.com/Samwise-OS/admin/actions/runs/41011641487) made five managed mutations. Injected canary wiki drift was detected; repair [41011804776](https://github.com/Samwise-OS/admin/actions/runs/41011804776) made one mutation. Real repeat [41011894264](https://github.com/Samwise-OS/admin/actions/runs/41011894264) made **zero managed mutations** and its independent audit matched.
- The full owner audit also reported match, no drift resources and no unreadable resources. It deliberately does not certify all functional acceptance cases.
- Current canary negative/positive proofs and exact actor qualifications are in [canary evidence](canary-acceptance-evidence.md). The wrong-source status was rejected; another Actions workflow can satisfy the same App-bound name. Fresh direct/force updates were denied. Isolated deletion was denied and its fixture cleaned up. A normal corrected PR merged without bypass.

## Activation and remaining owner actions

This revision declares daily native reconciliation at **06:17 UTC**, with no LLM calls.
Scheduled run `41060159080` occurred before the activation change reached `main`; the
gate skipped all credentialed work. A post-activation scheduled run must complete
reconciliation and independent readback before relying on the schedule.

1. The owner account has 2FA enabled; the member 2FA-disabled filter is empty and there are no outside collaborators. The organization requirement is enabled and owner-authenticated API readback matches the declaration.
2. The Codespaces scope authorization flow timed out. A fresh official `gh auth refresh -h github.com -s codespace` requires owner interaction before a real environment smoke test can run. A pinned devcontainer declaration is deployed; a live Codespace build is not claimed.
3. The Safe-Settings installation now selects **All repositories** for installation `176024067`. The manifest and generated program allowlist continue to bound current reconciliation to four declared repositories; no App permission change was made.

Non-owner actor permissions and the rendered issue chooser remain explicitly partial
in [acceptance](acceptance.md). Do not close the parent foundation issue as fully
accepted while those cases and authentication gates remain unresolved.

## Resume from committed tools

Use `scripts/doctor.py` for secretless validation, `scripts/audit.py audit-managed`
for declared repository defaults/rulesets, and `scripts/audit.py audit` for the full
owner inventory. Keep raw owner inventory under ignored `.local/` only. Provision
through `scripts/provision.py` with the recorded immutable workflow revision; it
proposes ordinary PRs and refuses stale or modified proposal trees.

Canonical instructions are `AGENTS.md`, `CONTEXT.md`, the ADRs, the specification and
GitHub issues #1/#3/#4/#5. Use `mattpocock-skills:implement`, `:tdd`, and separate
`:code-review` axes. Route execution through DevOps Automator on GPT-6 Luna with
bounded context. Do not treat older temporary handoffs as current truth.

## New authenticated observations — 2026-10-30

The latest owner-authenticated check confirms the owner account has 2FA enabled, the two current organization members have no 2FA-disabled accounts, and there are no outside collaborators. The organization requirement is enabled and readback matches the declaration. The controller treats it as manual-only if it drifts because GitHub's documented organization-update REST request does not include this field.

The Safe-Settings installation now selects all repositories (installation `176024067`), while the reviewed manifest allowlist still limits current managed scope to four repositories. Scheduled event `41060159080` ran before activation reached `main`: it passed the activation guard, skipped all credentialed steps, and does not count as active schedule acceptance. A later scheduled event on the activated `main` revision must complete reconciliation and independent readback.
