# Samwise-OS organization foundation

## Problem Statement

The organization has a declared settings file but no installed executor, CI enforcement,
repeatable repository provisioning or evidence of autonomous maintenance. The owner needs
a verified GitHub foundation before any application/platform work begins.

## Solution

Manage public repositories through a versioned organization baseline, reproducible
provisioning, canonical engineering guidance, GitHub-native automation and tested
quality/access controls. Use the current Free plan and a workable solo-owner model.
Human interaction is reserved for authentication; routine implementation decisions
are delegated to Codex within the stated organizational authority.

## User Stories

1. As owner, I want authenticated inventory so unknown permissions remain visible.
2. As owner, I want one authority per setting so automation converges consistently.
3. As maintainer, I want a reproducible repository request so creation needs no coordination.
4. As maintainer, I want an idempotent retry so failures do not create duplicate resources.
5. As contributor, I want inherited public guidance so conventions are discoverable.
6. As contributor, I want explicit repository ownership and security reporting.
7. As maintainer, I want canonical namespaced Matt Pocock workflows for engineering work.
8. As maintainer, I want specs, ADRs, tickets and dependencies recorded in GitHub.
9. As maintainer, I want behavior tests at the GitHub boundary rather than implementation mocks.
10. As owner, I want least-privilege member and Actions defaults.
11. As owner, I want protected branches to reject direct pushes and destructive updates.
12. As maintainer, I want failing/missing CI to prevent merges.
13. As sole maintainer, I want a normal successful PR path without fictitious independent review.
14. As owner, I want App scope and credentials contained within GitHub-native execution.
15. As owner, I want unknown or partial failures to be reported as failures.
16. As owner, I want drift detected and declared reversible settings repaired.
17. As maintainer, I want a zero-change second pass proving convergence.
18. As owner, I want lifecycle and recovery behavior proven without deleting real history.
19. As future project owner, I want application/language choices kept outside this bootstrap.
20. As auditor, I want evidence tied to actual actors, commits, requests and runs.
21. As future repository owner, I want the same manifest-derived baseline and pinned
    workspace declaration, so a repository starts with consistent GitHub conventions.
22. As maintainer, I want provisioning updates proposed through idempotent pull
    requests, so reconciliation works under the protections it establishes.
23. As maintainer, I want complete failure receipts retained by required CI, so a
    bounded repair starts with the exact failures and revision rather than repeating discovery.
24. As owner, I want scheduled credentialed reconciliation separated from secretless
    pull-request validation, so contributor-controlled jobs cannot access organization credentials.

## Implementation Decisions

Use official GitHub CLI/REST and GitHub-hosted Actions. Public repositories, main
default branches, squash merging and no mandatory independent approval support the
current Free/solo constraints. Required named checks bind the expected App while
documenting the workflow-substitution boundary. Preserve repository settings authority;
inspect the executor before installing its App. Use GitHub Issues with canonical triage
roles and native dependencies. Glossary and concise ADRs record terminology/tradeoffs.
No bulk deletion, visibility conversion or relicensing is required.

The repository manifests define the managed set; generated Safe-Settings files are
verified outputs rather than independently maintained policy. Repository workspace
declarations are versioned and image-digest pinned. Git worktrees follow documented
client conventions; remote GitHub controls apply to the resulting branches and PRs.
The existing Free plan remains the selected organizational plan. Actual Codespaces
verification uses explicitly authorized user authentication and records the exercised path.

Required validation emits revision-bound, versioned receipts and retained diagnostics.
Missing, empty or skipped required execution is non-passing. Receipt data is evidence,
never executable repair instructions or authority to change acceptance criteria.

## Testing Decisions

The highest public seam is authenticated GitHub behavior: official API/CLI and real
Actions/PR execution. Use an isolated canary for deliberate failures, positive merges,
direct-push rejection and drift/idempotence. Lower-level tests cover only the bounded
HTTP/CLI adapter and deterministic comparison where these affect safe failure handling.
Work one red/green behavior slice at a time. Do not claim prior local tests were TDD.

## Out of Scope

Application development, external infrastructure, agent runtime, model orchestration,
paid-plan purchase, new human identities and the broader autonomous engineering platform.

## Further Notes

Authentication may require owner interaction. Record unresolved authentication as a
live gate; continue independent work. Completion requires operational evidence, not
only this specification or configuration files.
