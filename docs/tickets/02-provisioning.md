## Parent

https://github.com/Samwise-OS/admin/issues/1

## What to build

Provision public organization community defaults, a reusable repository template and
an isolated canary reproducibly through official GitHub interfaces.

## Acceptance criteria

- [ ] Provisioning consumes a versioned manifest and rejects out-of-boundary targets.
- [ ] Community guidance and repository-local ownership/engineering standards are usable.
- [ ] A real canary consumes the immutable reusable standards workflow.
- [ ] An identical second provisioning pass creates nothing and changes no managed content.
- [ ] Partial retries preserve object identity and fail visibly on ambiguity.

## Blocked by

Inventory and governance CI ticket; native dependency linked in GitHub.
