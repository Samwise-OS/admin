# SAI Institutional State Contract — executable handoff specification
Status: PROPOSED; branch-only; no deployment or Muzz/Pixel execution asserted.
Date: 2026-11-05
Owner of sovereign decisions: Principal.
Purpose: make verified state from one agent session actionable in the next, with a minimal Git-native contract.

## Canonical records
- `state/intent.json`: immutable principal-approved intent and frozen invariants; changes require explicit principal authorization.
- `state/capabilities.jsonl`: append-only evidence-backed capability claims, with source, tool, observation, test and commit.
- `state/handoffs.jsonl`: append-only completed work and pending handoffs, keyed by unique id, owner and next action.
- `state/receipts.jsonl`: append-only verification receipts with input state revision, test, result and output commit.

## Minimal JSONL record
{"id":"unique-id","kind":"capability|handoff|receipt","source":"agent/session","observed_at":"ISO-8601","input_revision":"git-sha","claim":"one testable statement","evidence":{"uri":"https://...","test":"reproducible command or check","result":"observed result"},"next_action":"specific machine-actionable action or null","status":"observed|verified|pending"}

## Required execution contract
1. Before any task, fetch latest authorized intent and relevant verified records; record input commit SHA.
2. Execute within already-authorized scope; distinguish observation, inference and aspiration.
3. Validate claims with independent readback or test evidence; never promote untested claims to verified.
4. Append a unique receipt and any resulting capability or handoff record on a branch; preserve prior records.
5. Publish commit SHA and a machine-readable next action; do not require principal to restate prior context.
6. Subsequent agents ingest verified records and select the next eligible action; avoid redoing already-verified work.
7. Merge/promote only through existing Samwise-OS governance and branch protection.

## First cross-agent acceptance test
A principal-approved invariant is recorded at revision A; a separate Muzz session reads A, quotes the exact invariant, applies it to a concrete operation, and writes a verifiable receipt at revision B; a subsequent independent session reads B and proceeds without re-prompting. Acceptance requires readback of both SHAs and the executed effect, not a narrative assertion.

## Scope discipline
This is the smallest proposed common contract; existing Samwise-OS governance remains authoritative. GitHub is the persistence transport, not an added scheduler. Pixel's November 3 capability report establishes Git, SQLite, SSH, Termux:Boot, runit and MacroDroid surfaces, but does not itself prove Muzz integration. Do not modify machines or deploy new infrastructure until separately authorized.

## Compounding criterion
A newly verified capability must be consumed by a later independent task and demonstrably improve or expand accepted execution. Merely adding entries to the log does not count.
