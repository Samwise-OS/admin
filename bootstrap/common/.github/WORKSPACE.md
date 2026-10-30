# Workspace conventions

These files are a repository starting point for future Samwise-OS repositories. They are copied or retained when the repository template is used. GitHub Free organization settings do not centrally enforce these local conventions, and this document makes no claim about controls over a developer's Windows or WSL host.

## Branches and worktrees

- Use `codex/<short-task-name>` for Codex-created branches unless the repository owner specifies another naming rule.
- A Git worktree is a separate working directory linked to the same local repository. It has its own `HEAD` and index, while refs and objects are shared. List the worktrees before acting with `git worktree list`.
- Do not reset, clean, remove, move, or check out over another person's or agent's worktree or branch. Preserve uncommitted and untracked changes. Coordinate before touching a shared branch; Git prevents checking out one branch in multiple worktrees by default.
- Create a worktree only for an explicit need, and remove only a worktree you own after confirming its changes are committed or preserved. Do not use force options to bypass Git's safety checks.
- Worktree paths are machine-local. Windows and WSL may use different path roots and Git installations; choose paths valid in the environment running Git and do not assume one environment can safely manage the other's paths.

## Credentials and local state

- Never commit access tokens, passwords, private keys, credential files, or personal machine configuration. Use approved secret stores and environment-specific credential helpers.
- Do not put secrets in `.devcontainer/devcontainer.json`, image build arguments, shell history, or logs. Keep Codespaces secrets in GitHub's secret settings when Codespaces are used.
- Treat this repository guidance as reviewable policy text, not host-level enforcement. GitHub controls apply to remote repository resources; local worktree lifecycle and workstation behavior remain under the local Git/host environment.

## Default development container

The sibling `.devcontainer/devcontainer.json` pins Microsoft's official `mcr.microsoft.com/devcontainers/base:ubuntu-24.04` image by digest. It deliberately declares no project runtime, application setup, Feature, LLM, or agent-tool installation. Change it through a reviewed repository commit when a concrete project need is established, and refresh the digest deliberately when updating the base image.

The pinned manifest digest was read from the official MCR registry's `Docker-Content-Digest` response header on 2026-10-30 for `https://mcr.microsoft.com/v2/devcontainers/base/manifests/ubuntu-24.04` (HTTP 200, OCI image index). The repository configuration pins the image reference; GitHub Free organization policy does not enforce that future repositories retain it.
