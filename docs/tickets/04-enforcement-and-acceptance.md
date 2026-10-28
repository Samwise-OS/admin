## Parent

https://github.com/Samwise-OS/admin/issues/1

## What to build

Activate least-privilege organization controls and tested per-repository enforcement,
then publish functional acceptance and recovery evidence for the complete baseline.

## Acceptance criteria

- [ ] Member/Actions defaults match declared policy without removing the existing owner.
- [ ] Required CI rejects failing and missing-check PRs; a corrected normal PR merges.
- [ ] Rules reject non-bypass direct/force pushes and protected-branch deletion on the canary.
- [ ] Same-name check substitution boundary is tested/documented accurately.
- [ ] Reversible drift is detected, repaired and clean on the following pass.
- [ ] 2FA/recovery state and any remaining authentication gate are recorded honestly.
- [ ] No application/platform work is introduced and final evidence names residual trust limits.

## Blocked by

Provisioning and native reconciliation tickets; native dependencies linked in GitHub.
