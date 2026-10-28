## Parent

https://github.com/Samwise-OS/admin/issues/1

## What to build

Run repository-setting reconciliation through pinned Safe-Settings on GitHub Actions
with an inspected organization-owned App and bounded credentials, plus independent
API verification and explicit ownership for supplemental organization policies.

## Acceptance criteria

- [ ] Source/lockfile and exact minimum App grants are inspected before installation.
- [ ] Native App authentication and canary-only dry run succeed in the real workflow.
- [ ] Approved managed repository settings converge with API readback.
- [ ] A second real reconciliation is semantically clean and demonstrably writes nothing.
- [ ] A scheduled native maintenance path detects/reconciles declared drift and fails on partial errors.
- [ ] Privileged workflow execution uses protected trusted source and exposes no keys in logs.

## Blocked by

Inventory and governance CI ticket; native dependency linked in GitHub. Owner App
registration/installation authentication is a live gate.
