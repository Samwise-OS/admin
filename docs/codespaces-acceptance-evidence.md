# Codespaces template acceptance evidence

**Date:** 2026-10-30  
**Actor:** authenticated GitHub CLI account `Samwise-x`  
**Repository/ref:** `Samwise-OS/repository-template` / `main`  
**Result:** **PASS for live template runtime, required files, stop/start, and cleanup.**
The initial pre-fix run failed as documented below; a fresh run passed after the fix
reached the target template.

## Initial pre-fix run evidence

- `gh auth status` reported the active `Samwise-x` account with the `codespace`
  scope. No auth refresh or account switch was performed.
- `gh repo view Samwise-OS/repository-template --json nameWithOwner,isTemplate,defaultBranchRef,url`
  reported a template repository with default branch `main`.
- The authenticated contents API returned
  `.devcontainer/devcontainer.json` containing
  `mcr.microsoft.com/devcontainers/base:ubuntu-24.04@sha256:d94c97dd9cacf183d0a6fd12a8e87b526e9e928307674ae9c94139139c0c6eae`.
  This is the declared digest. No runtime image digest was observed.
- Before the run, `gh codespace list -R Samwise-OS/repository-template` returned
  `[]` for this actor.
- `gh codespace create -R Samwise-OS/repository-template -b main -m basicLinux32gb
  -d samwise-template-acceptance --idle-timeout 10m --retention-period 1h --status`
  reported: `Codespaces usage for this repository is paid for by Samwise-x`.
  The create response yielded `samwise-template-acceptance-97rr6px4prxpcxg57`.
  No plan, billing, or spending setting was changed. GitHub's message identifies
  the payer account; it does not establish that a charge was incurred.
- Authenticated `gh codespace view` reported:
  - state `Available`;
  - repository `Samwise-OS/repository-template`;
  - Git status `main - 0 commits ahead, 0 commits behind`;
  - devcontainer path `.devcontainer/devcontainer.json`;
  - machine `2 cores, 8 GB RAM, 32 GB storage`;
  - idle timeout `10 minutes`.
- `gh codespace ssh -c samwise-template-acceptance-97rr6px4prxpcxg57 -- <command>`
  failed with `error getting ssh server details: failed to start SSH server` and
  the message that an SSH server is not installed in the container. The same
  failure prevented `gh codespace logs` from retrieving logs. Therefore remote
  checkout files, shell/runtime tools, post-create behavior, and effective image
  digest were not verified. Treat workspace usability acceptance as failed or
  blocked, not passed.
- Cleanup: `gh codespace delete -c
  samwise-template-acceptance-97rr6px4prxpcxg57 --force` exited 0. A subsequent
  authenticated repo-filtered list returned `[]`, verifying absence.

## Root cause and fix

The CLI's `gh codespace ssh --help` states that the container must have an SSH
server pre-installed and suggests the official `ghcr.io/devcontainers/features/sshd`
Feature for Debian-based images. The exact failure above is consistent with the
template's pre-fix image lacking that server. The repository and bootstrap copies
now declare the official SSH server Feature by OCI digest
(`ghcr.io/devcontainers/features/sshd@sha256:f5251b8e4325f68f7280973c6cd65daff414449c66f240621502d4e8e74eb7ee`),
while retaining the digest-pinned Ubuntu 24.04 base image. The digest was resolved
from the official GHCR manifest for the upstream `1.1.0` tag. The official Feature
metadata identifies that release as `1.1.0`, and its README says it adds an SSH
server ([official feature](https://github.com/devcontainers/features/tree/main/src/sshd)).
The Dev Container reference CLI supports OCI Feature references by SHA-256 digest
([official resolver](https://github.com/devcontainers/cli/blob/main/src/spec-configuration/containerCollectionsOCI.ts));
the Features spec's dependency example also includes a digest reference
([spec](https://github.com/devcontainers/spec/blob/main/docs/specs/devcontainer-features.md#referencing-a-feature)).
Local JSON, image digest, and Feature declaration assertions passed.

The fix was integrated in PR10 and propagated to the target template through
template-content PR #2. Before the successful test, the authenticated contents API
confirmed that `Samwise-OS/repository-template` `main` at
`d35c2c4240662930cd50c2025c939b5e6b924bf8` contained the exact pinned Feature
reference. The authenticated Codespaces API showed no existing environment for
this repository.

Before the successful create, the authenticated personal billing UI was inspected
read-only. The existing Samwise-x Codespaces budget is `$0.00` and reports `Usage
blocked`; the current Codespaces metered-usage view had no rows. GitHub documents
that personal Free accounts receive included Codespaces usage and that excess use is
blocked without an enabled spending limit. No billing settings were changed.
GitHub does not document an API or CLI field for exact remaining included quota, so
the remaining allowance is not independently quantified here. GitHub's CLI notice
that a Codespace is “paid for by Samwise-x” identifies the owner; it does not prove
that a charge was incurred. See [included-usage guidance](https://docs.github.com/en/codespaces/troubleshooting/troubleshooting-included-usage)
and [Codespaces billing](https://docs.github.com/en/billing/concepts/product-billing/github-codespaces).

## Successful post-fix runtime acceptance

- Created `samwise-template-acceptance-pj447x6qxv7xc9w4v` from
  `Samwise-OS/repository-template` `main` with machine `basicLinux32gb`. GitHub
  reported state `Available`, devcontainer path `.devcontainer/devcontainer.json`,
  2 cores, 8 GB RAM, 32 GB storage, and a 5-minute idle timeout.
- The `gh codespace create --status` process eventually exited 1 while polling
  post-create status, reporting `vscode@localhost: Permission denied
  (publickey,password)`. This did not prevent the environment from reaching
  `Available`; the separate `gh codespace ssh` remote shell verification below
  succeeded before and after stop/start.
- `gh codespace ssh` connected as `vscode` to `codespaces-c4bb60`. Commands in
  `/workspaces/repository-template` reported branch `main`, commit
  `d35c2c4240662930cd50c2025c939b5e6b924bf8`, and origin
  `https://github.com/Samwise-OS/repository-template`.
- The remote config contained the expected immutable Ubuntu base-image digest and
  exact pinned sshd Feature digest. All required baseline files were present and
  nonempty: `README.md`, `AGENTS.md`, `.editorconfig`, `.gitattributes`,
  `.github/CODEOWNERS`, `.github/WORKSPACE.md`,
  `docs/agents/issue-tracker.md`, `docs/agents/triage-labels.md`, and
  `docs/agents/domain.md`.
- The container provided `bash`, `git`, `jq`, `curl`, and `/usr/sbin/sshd`.
  `python3` was absent; the template declares no application language/runtime, so
  no Python tooling requirement is claimed. The Git checkout was clean.
- `gh codespace stop` moved the instance through `ShuttingDown` to `Shutdown`.
  The authenticated REST start endpoint returned `Queued`; a later read showed
  `Available`. A fresh SSH command confirmed the same main branch and commit,
  `sshd` path, and clean checkout after restart.
- Cleanup: `gh codespace delete -c
  samwise-template-acceptance-pj447x6qxv7xc9w4v --force` exited 0. The
  repo-filtered list returned `[]`; direct authenticated lookup returned HTTP 404.

## Acceptance boundary

The final live run verified config selection, remote shell execution, required files,
shell and Git tools, SSH service presence, clean checkout, stop/start recovery, and
test-instance cleanup. The earlier pre-fix attempt established the missing SSH
server as the root cause. The final user-owned Codespace list is empty.

## Reproduction notes

The initial local CLI attempt used unsupported `-i` shorthand for idle timeout and
was rejected before creating a Codespace; the successful invocation used
`--idle-timeout`. A worktree `git status --short` was clean before execution. No
credentials or raw authentication output are included here.

## Admin maintenance runtime

**Status:** **PASS** for live runtime, doctor, stop/start, and test-instance cleanup.

The template runtime acceptance above does not establish that the organization
admin Codespace can execute its maintenance checks. `docs/validation-receipts.md`
declares `python3 scripts/doctor.py --output .local/validation-receipt.json` as the
secretless validation command, and `scripts/doctor.py` runs the existing Python
validators and unittest suite. The Python checks use the standard library; no
application runtime or Python package set is required. The earlier shared-base
runtime probe observed that `python3` was absent, so this was a real admin-tooling
gap.

The admin-only `.devcontainer/devcontainer.json` now adds the official
`ghcr.io/devcontainers/features/python` Feature pinned to manifest digest
`sha256:fbcad6955caeecc5ad3f7886baf652e25cba5225a6c4c2287c536de2e5607511`.
The manifest was resolved from the official GHCR `1.8.0` tag; its embedded Feature
metadata reports version `1.8.0`. The selected Python release is `3.12.16`, listed
as the latest Python 3.12 security release on Python.org at the time of this change.
Feature options disable optional pipx/lint/test tooling and JupyterLab. The official
Feature source accepts an exact CPython version by resolving CPython release tags;
the generated container still must prove the installed runtime.

Primary sources: [official Python Feature metadata](https://github.com/devcontainers/features/blob/main/src/python/devcontainer-feature.json),
[official Python Feature installer](https://github.com/devcontainers/features/blob/main/src/python/install.sh),
[Python 3.12.16 release](https://www.python.org/downloads/release/python-31216/), and
[official Dev Container Features project](https://github.com/devcontainers/features).

The doctor also runs Node.js-based repository checks, so the admin-only container
pins the official `ghcr.io/devcontainers/features/node` Feature to OCI manifest
digest `sha256:2a19d3b0b3879437637cfd292eb29fee0afcfbe6364e33db9afc4f80c5c1f956`.
The digest was resolved from the official `2` tag using the GHCR manifest API; the
Feature metadata identifies it as the official Node.js Feature. Its `version`
option accepts an explicit Node.js release, and `22.23.4` is the official Node.js
22 LTS release dated 2026-10-21.

Primary sources: [official Node Feature metadata](https://github.com/devcontainers/features/blob/main/src/node/devcontainer-feature.json),
[official Node Feature README](https://github.com/devcontainers/features/blob/main/src/node/README.md),
[official Node Feature installer](https://github.com/devcontainers/features/blob/main/src/node/install.sh),
and [Node.js 22.23.4 release](https://nodejs.org/en/blog/release/v22.23.4).

## Successful admin runtime validation

- Created `samwise-admin-doctor-acceptance-7v667gx4gg5wcpjx5` from
  `Samwise-OS/admin` branch `codex/close-out-organization-baseline` using
  `.devcontainer/devcontainer.json` and machine `basicLinux32gb`. GitHub reported
  the Codespace `Available`.
- The remote checkout was clean at commit
  `eba5dbdfd52a93a60e0b35517e38f5b720466ea0`, the pushed revision containing the
  pinned Python and Node Features. The branch advanced by one docs-only commit
  while the Codespace was building, so this checkout is one commit behind its
  current branch ref; no code or devcontainer changes were omitted.
- Remote runtime commands reported `Python 3.12.16` and `v22.23.4`.
- Ran the documented command exactly:
  `python3 scripts/doctor.py --output .local/validation-receipt.json`.
  It exited 0 with aggregate `pass`; configuration, repository settings,
  Safe-Settings, and unit tests all passed. The unittest log reports 79 tests and
  `OK` with no skips. The receipt records matching head and checkout SHAs and
  `worktree_dirty: false`.
- Sanitized receipt and four validation logs are retained locally under ignored
  `.local/codespaces-admin-doctor-acceptance-eba5dbd/`; receipt SHA-256 is
  `B4B30860091390DF9BF3FA6FBD6B29386E710ECBAFBBDBB7AA9CDD7A4BE3B629`.
- After stopping and restarting the Codespace, GitHub reported it `Available`;
  SSH again reported the same checkout SHA, clean worktree, Python 3.12.16,
  Node v22.23.4, and the persisted validation receipt.

The test Codespace was deleted. The authenticated repository-filtered list returned
`[]`, and direct lookup of the deleted resource returned HTTP 404. No billing or
plan settings were changed.
