# Codespaces template acceptance evidence

**Date:** 2026-10-30  
**Actor:** authenticated GitHub CLI account `Samwise-x`  
**Repository/ref:** `Samwise-OS/repository-template` / `main`  
**Result:** **PARTIAL; runtime acceptance failed against the pre-fix remote config.**

## Evidence

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
  No plan, billing, or spending setting was changed. GitHub's message indicates
  this user-owned Codespace was paid; this run makes no claim about the final
  monetary amount.
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

## Diagnosis and pending retest

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

The fix is integrated into PR10 branch revision
`0d35cb084c96d482a82261ee9c65af33f99828ae`. At the last authenticated check,
`Samwise-OS/repository-template` `main` was still at
`c5f14882817a06f1982b4fcd34d429477b3061a`; it does not yet contain the Feature.
This run therefore cannot claim that the fix builds or provides a working remote
shell. Re-run the live create and remote shell check only after the authenticated
contents API for the target template's `main` confirms the pinned Feature reference.

Before considering that rerun, the authenticated personal billing UI was inspected
read-only. The existing Samwise-x Codespaces budget is `$0.00` and reports `Usage
blocked`; the current Codespaces metered-usage view had no rows. GitHub documents
that personal Free accounts receive included Codespaces usage and that excess use is
blocked without an enabled spending limit. No billing settings were changed.
GitHub does not document an API or CLI field for exact remaining included quota, so
the remaining allowance is not independently quantified here. GitHub's CLI notice
that a Codespace is “paid for by Samwise-x” identifies the owner; it does not prove
that a charge was incurred. See [included-usage guidance](https://docs.github.com/en/codespaces/troubleshooting/troubleshooting-included-usage)
and [Codespaces billing](https://docs.github.com/en/billing/concepts/product-billing/github-codespaces).

## Acceptance boundary

GitHub created an available Codespace and confirmed that it selected the pinned
repository config path on `main`. This establishes config selection and environment
creation only. The attempted remote shell could not start because the container lacks
the SSH server required by `gh codespace ssh`; no runtime acceptance is claimed.
The local config now declares the official SSH server Feature, but it needs integration
and live retesting. The test instance was deleted and the final user-owned Codespace
list is empty.

## Reproduction notes

The initial local CLI attempt used unsupported `-i` shorthand for idle timeout and
was rejected before creating a Codespace; the successful invocation used
`--idle-timeout`. A worktree `git status --short` was clean before execution. No
credentials or raw authentication output are included here.
