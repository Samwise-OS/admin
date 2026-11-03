# Govern Android provisioning before device mutation

Status: Proposed, pending repository acceptance and deployment-gate verification.

## Decision

Adopt `Samwise-OS/android` as the single canonical source for Android fleet
provisioning manifests, device profiles, execution policy, verifiers and
evidence schemas. Use the existing `Samwise-OS/admin` repository provisioner
and Safe-Settings reconciliation to create, adopt and protect the repository.
One repository governs all phone profiles; do not create per-phone repositories.

The assistant is an untrusted requester of provisioning actions, not a policy
authority or acceptance judge. On-device mutation is executable only through
a host-resident, fail-closed provisioning interface enforcing a frozen release
manifest and an explicit operation allowlist. No assertion by an agent, test
runner, or log producer is sufficient to mark its own work accepted.

## Frozen bootstrap invariants

1. Initial phone transport is authorized USB ADB; Wi-Fi must be positively
   observed disabled throughout the offline provisioning phase.
2. Before any phone mutation, verify the exact expected USB serial, Android
   shell identity, device profile, approved operation, prerequisite state,
   signed/pinned artifacts, and immutable policy revision.
3. Each managed operation has a unique ID, declared dependencies, bounded
   timeout, expected state transition, independently checked postconditions
   and durable evidence receipt. Unlisted operations return DENY without
   invoking a shell or Android write.
4. The host gate records an append-only plan/decision/attempt/result ledger.
   Unknown, missing, inconsistent and stale evidence all fail closed.
5. Acceptance is a separate function from execution and requires independently
   observed on-device outcomes, complete mandatory checks, immutable release
   identity, and code/documentation parity.
6. No execution result may alter the previously approved expected outcomes.
   A changed criterion requires a new reviewed policy revision.
7. Apply, reboot, repeat apply, repair, and induced-fault recovery must each
   generate receipts. A second identical apply must make no uncontrolled changes.
8. Android's operating-system authority is explicitly modeled: ADB shell,
   Shizuku/Rish, Device Owner and Termux are not interchangeable authorities.
9. The offline GTX recovery kit is reproducible, verified by SHA-256/signature,
   and carries the exact release and policy identifiers.
10. Phone Wi-Fi activation is a separately authorized transition after the
    USB-only acceptance suite. Until that gate, the phone is not modified
    by this Android provisioning project.

## Acceptance boundary

The public seam is `plan / apply / verify / accept`, with `apply`
requiring a prior signed, exact-snapshot authorization receipt.
Testing exercises the actual host-to-device interface; policy unit tests
exercise the same parser and decision function. The required negative
tests include wrong serial, revoked ADB, altered artifact, undeclared
action, unmet dependency, changed frozen criterion, missing receipt,
documentation drift, wrong shell UID, Wi-Fi enabled, process crash,
duplicate apply, interrupted telemetry and interrupted USB.

The project CI must report a pinned commit SHA, test identities, zero
skipped mandatory tests, generated-document parity, and a non-ambiguous
PASS/FAIL/UNKNOWN decision. GitHub passing CI authorizes a candidate release;
only independent real-device evidence can certify a phone.

## Ownership and sequencing

Organization repository policies stay in `Samwise-OS/admin`.
Android runtime implementation belongs in `Samwise-OS/android`.
First create/adopt/protect that repo using the established administrator
workflow; then implement and red-team the host policy gate; only then
authorize initial Motorola device writes. Documentation of the real
installation follows verified state changes and cannot preclaim success.
