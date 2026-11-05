# Independent acceptance gate: SAI institutional state

Status: REQUIRED BEFORE MERGE. Implementation author is not acceptance authority.

## Acceptance authority
An independently delegated evaluator must design and execute acceptance tests from the principal's original goal, not from the implementation author's success claims. Evaluator identity, execution environment, exact commands, raw stdout/stderr, exit codes, commit SHAs and resulting GitHub artifacts must be recorded. The author must not edit the evaluator's test definitions or acceptance evidence. Existing Samwise-OS governance retains final merge authority.

## Mandatory adversarial tests
- Fresh checkout and independently executed bootstrap; demonstrate persistence across separate processes.
- Detect modified record content, broken parent hash, duplicate ID, malformed JSON and missing evidence in a verified claim.
- Reject self-asserted 'verified' evidence when no independent reproduction is supplied.
- Demonstrate two concurrent writers cannot silently lose either record.
- Demonstrate deterministic replay/idempotence and preservation of frozen principal decisions.
- Demonstrate a second agent consumes prior state in a fresh session and its execution demonstrably changes because of it.
- Demonstrate full conversational capture without selectively dropping consequential corrections and decisions.
- Demonstrate recovery from interrupted writes and provenance of source conversations.

## Decision rule
Until independent evaluator evidence exists, label this implementation AUTHOR-TESTED / NOT INDEPENDENTLY ACCEPTED. A failed test is a mandatory implementation input and must be rerun independently after correction. No merge or production rollout on self-attestation.

## Current observations
Author executed Git clone, append and bootstrap on GTX1660 and observed record_count=1. These observations are not independent acceptance. The initial contract and executable were authored before this gate was established; that sequence is explicitly noncompliant with the requested governance-before-implementation order. This document records the correction without retroactively claiming compliance.
