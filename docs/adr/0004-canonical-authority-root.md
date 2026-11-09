# ADR-0004: Canonical authority root and explicit estate classification

Status: Proposed
Recorded: 2026-11-09
Owner: Samwise-OS/admin

## Decision

Use `Samwise-OS/admin` as the only organization-level authority registry and governance root.

The root does not own every runtime implementation. It records which repository or system owns each domain, which writer may change that domain, which verifier checks the result, and which acceptance authority may declare the result accepted.

Authoritative Samwise-OS repositories live under the `Samwise-OS` organization. A repository under a personal namespace may be a migration source or external dependency, but it cannot be the current authority for a Samwise-OS domain.

## Required state model

The root distinguishes four kinds of data.

1. Desired state. Versioned declarations and accepted policy.
2. Observed state. Authenticated readback from GitHub, hosts, devices, and services.
3. Evidence. Immutable-revision-bound receipts that record what was checked and what happened.
4. Acceptance. A decision produced by an authority that did not execute the change it judges.

A successful writer response is never acceptance.

## Authority registry

Add one versioned authority registry under `config/`. Each entry must identify:

- the domain;
- the authoritative repository and path;
- the allowed writer;
- the independent verifier;
- the acceptance authority;
- the evidence schema;
- the lifecycle state.

The registry must reject duplicate authorities for the same domain.

The first registry must include organization policy, repository settings, repository provisioning, Android runtime policy, agent cognition, and legacy Pixel migration state.

## Repository inventory

`config/repositories.json` must account for every repository observed in the `Samwise-OS` organization.

Each repository must be classified as either managed or an explicit exception. An unknown live repository is drift and fails the authenticated owner audit.

An exception must include its immutable repository ID, reason, owner, enforcement method, and expiry or review condition.

The current live inventory includes `agent-cognition`, repository ID `1443124912`, which is not present in the current managed manifest. The foundation work must classify it explicitly before the root can claim complete namespace coverage.

## Namespace rule

The canonical system namespace is `Samwise-OS/*`.

`Samwise-x/pixel` is outside the canonical namespace. ADR-0003 already assigns Android fleet provisioning to `Samwise-OS/android` and forbids per-phone repositories. Treat `Samwise-x/pixel` as a migration source until its unique responsibilities and artifacts have verified destinations. Archive it only after that migration passes.

## Writers

Keep one writer per managed domain.

- `scripts/organization.py` owns declared organization and team fields.
- Safe Settings owns declared repository settings and repository rulesets.
- `scripts/provision.py` owns supported repository creation and adoption.
- Domain repositories own their runtime implementation behind their accepted contracts.

Do not add a second settings app, a second organization reconciler, or a second repository provisioner.

## GitHub enforcement

Keep the existing GitHub-native enforcement.

- Organization Actions remain restricted to selected actions.
- SHA pinning remains required.
- Default workflow permissions remain read-only.
- Managed public repositories keep the active `samwise-default-branch` ruleset.
- Required checks remain revision-bound and independently read back.
- Repository creation remains owner-controlled and must flow through the declared provisioning path for accepted Samwise-OS repositories.

Add deterministic checks that fail with actionable output when the authority registry, repository inventory, generated documentation, namespace, schemas, or live authenticated inventory do not match the accepted contract.

## PStack

Use PStack as the engineering method for changing this control plane.

Do not make PStack an execution dependency of GitHub governance. Any invariant learned through PStack must be encoded in repository structure, schemas, scripts, tests, or required CI before the work is accepted.

## Issues, ADRs, and Projects

GitHub Issues remain the canonical work tracker. ADRs record accepted architectural decisions.

A GitHub Project may present issue state, dependencies, and progress, but it is a derived view. Project fields do not authorize execution or acceptance and must not become a second source of truth.

## Evidence log

Do not create a second event ledger as part of this decision.

First freeze the authority, schema, writer, verifier, and acceptance model. Then define one evidence event schema and one writer for cross-domain receipts. Existing domain ledgers remain in place until migration proves that a unified writer preserves their required behavior.

Git history, GitHub Actions run records, and current revision-bound receipts remain the evidence sources for organization governance.

## Required first implementation slice

1. Complete issue #15 so declared source and generated documentation cannot drift silently.
2. Add and validate the authority registry.
3. Extend repository inventory semantics to classify every live organization repository.
4. Make authenticated audit fail on unknown repositories.
5. Add JSON Schema validation for root declarations and evidence receipts.
6. Emit exact remediation output for every failed foundation check.
7. Re-run the root checks twice and prove the second run performs no managed writes.
8. Reconcile the legacy `Samwise-x/pixel` authority claims against `Samwise-OS/android` before any archive decision.

## Acceptance

The foundation is accepted only when:

- every live organization repository is declared or explicitly excepted;
- every managed domain has exactly one authority, writer, verifier, and acceptance authority;
- the required governance check rejects malformed, duplicate, stale, or undocumented declarations;
- authenticated GitHub readback matches the declared managed state;
- a repeated reconciliation makes zero managed writes;
- generated documentation is byte-stable and matches its source;
- no personal-namespace repository is treated as a current Samwise-OS authority;
- evidence records identify the exact policy revision that judged the execution.
