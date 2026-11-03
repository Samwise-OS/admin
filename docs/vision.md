# Samwise-OS — canonical future-state vision

**Contract:** `SAMWISE-VISION-001` · **Revision:** `1` · **Recorded:** `2026-11-03`  
**Status:** Target architecture (not deployed or accepted)  
**Control-plane owner:** `Samwise-OS/admin`  
**Reference architecture:** [Microsoft HVE Core — Agentic Workflows](https://microsoft.github.io/hve-core/docs/architecture/agentic-workflows/)

## 1. Vision

**I express intent. Samwise converts that intent into an accepted architectural decision, orchestrates its implementation, independently verifies the outcome, and compounds validated operational knowledge into the next execution.**

The user operates as a visionary and decision-maker, not as a prerequisite programmer or workflow operator. Once an architectural decision and its acceptance criteria are approved, the remainder of the execution path is event-driven, observable, and governed.

**North-star outcome:** A newly created Samwise-OS repository is born with the organization's preconfigured engineering standards, verification gates, acceptance contracts, and reusable agentic workflow conventions. Accepted execution outcomes improve the organizational knowledge base without rewriting the criteria that judged them.

## 2. Human interface and immutable handoff

The visible human-facing interface is deliberately small:

1. **State intent:** Express the desired outcome in natural language; the capture channel is interchangeable.
2. **Approve a decision:** Review the canonical architecture decision record (ADR), its invariants, scope, and acceptance criteria.
3. **Inspect acceptance:** Receive an evidence-backed result, including implementation links and the recorded acceptance decision.

**Canonical execution trigger:** An **accepted ADR revision**. The accepted ADR is the authorization and requirements record for downstream work; subsequent issues, plans, code changes, and evidence refer to that exact revision.

An ADR is accepted only through the explicit project governance decision process. A material change to its objectives or acceptance criteria requires a newly reviewed revision rather than reinterpretation during execution.

## 3. End-to-end operating contract

```text
Natural-language intent
       |
       v
Canonical ADR + frozen acceptance contract
       |
       v  [ADR acceptance event]
Deterministic issue creation / classification / dependencies
       |
       v
Research -> Plan -> Independent critique -> Implementation
       |
       v
Pull request + code/documentation changes
       |
       v
Deterministic CI + security + executable documentation checks
       |
       v
Independent verification / acceptance decision
       |
       v
Governed merge and, where relevant, deployed-state verification
       |
       v
Execution telemetry + provenance + append-only evidence receipt
       |
       v  [accepted evidence only]
Knowledge distillation -> reviewed docs / skills / reusable contracts
       |
       v
Next execution inherits accepted organizational knowledge
```

The orchestrator is a **deep module** behind the accepted-ADR interface. GitHub events and state transitions carry work between stages; human intent does not require manually orchestrating GitHub issues, PRs, and runners.

## 4. Enforcement architecture

| Plane | Responsibility | Status as of this revision |
| --- | --- | --- |
| **Organization control** | Declare, provision, protect, reconcile, and audit repositories | Existing GitHub-native baseline; see [acceptance](acceptance.md) |
| **Agentic workflow** | Accepted ADR -> issue triage -> research/plan -> implementation PR -> review | Target; reference HVE Core and GitHub Agentic Workflows |
| **Deterministic verification** | Compile/validate workflow definitions, run required checks, enforce source/documentation parity and acceptance contracts | Organization-level baseline exists; future agentic and project checks are target work |
| **Evidence and observability** | Correlate ADR revision, issue/PR, commit, run, tool execution, telemetry, assertions, and acceptance outcome | Existing governance receipts are the seed; generalized execution traces are target work |
| **Knowledge compounding** | Distill independently accepted traces into reviewed, versioned documentation, skills, and reusable policy | Target |

Use **GitHub Actions** for reproducible checks and state transitions, and **GitHub Agentic Workflows (`gh-aw`)** where interpretation or generation is required. Agentic Markdown sources compile to generated `*.lock.yml` workflows; generated lock files are not independent policy authorities. Separate agent proposals from permission-controlled GitHub writes.

Preserve the existing repository-settings writer (`Safe-Settings`), organization-policy controller, manifest authority, and CI checks. Extend their existing seams rather than create competing writers.

## 5. Acceptance and telemetry contract

Each execution is traceable to:

- `intent_id`, `adr_id`, and accepted `adr_revision`;
- linked issue(s), PR(s), immutable source commit(s), workflow revision(s), and execution run IDs;
- frozen requirements, expected state transitions, mandatory checks, and their observed outcomes;
- sanitized telemetry/traces, provenance, artifact identities, timestamps, and evidence locations;
- an independent `PASS` / `FAIL` / `UNKNOWN` acceptance outcome and its authority.

**Evidence is data, never authority to change the acceptance standard.** Failed, incomplete, or unverified executions remain available for diagnosis but do not become accepted organizational knowledge.

A learning candidate identifies the accepted execution(s) from which it was derived, the concrete reusable lesson, affected documentation/skill/contract, and verification required for adoption. Only after review and passing gates does that lesson enter the canonical knowledge base.

## 6. First vertical-slice success contract

The first agentic factory slice is complete when one approved ADR can produce the following evidence without manual engineering orchestration:

1. A GitHub event creates or advances a correctly linked issue with explicit acceptance criteria.
2. A ready issue invokes a specialized implementation workflow and produces a reviewable PR.
3. The PR includes applicable code/documentation updates and runs required deterministic checks.
4. A separate acceptance step records a revision-bound, independently verifiable decision.
5. Accepted execution evidence produces a traceable knowledge-improvement proposal.
6. That proposal undergoes the same governed review and validation before becoming reusable.

**Organization inheritance test:** A new canary repository provisioned through the existing `admin` authority receives the approved default contract and demonstrates its required acceptance path.

## 7. Source of truth and change procedure

- **Current operational facts:** `admin/config/`, `admin/scripts/`, `admin/.github/workflows/`, and current authenticated GitHub readback.
- **Current demonstrated acceptance:** `admin/docs/acceptance.md` and linked evidence.
- **Future destination:** This vision contract until superseded by a reviewed revision.
- **Terminology:** `admin/CONTEXT.md` is the glossary only.
- **Architectural decisions:** `admin/docs/adr/` holds actual decisions and tradeoffs, not speculative implementation status.
- **Engineering process:** Follow `admin/AGENTS.md` and the installed Matt Pocock Skills workflow.

No implementation milestone upgrades a target claim into an operational claim without its recorded acceptance evidence. Preserve historical evidence when updating current-state summaries.

## 8. Primary architecture references

- [Microsoft HVE Core — Agentic Workflows](https://microsoft.github.io/hve-core/docs/architecture/agentic-workflows/): issue triage, issue implementation, PR review, documentation drift, label-driven handoffs, and interactive research/plan/implement/review stages.
- [Microsoft HVE Core — Build Workflows](https://microsoft.github.io/hve-core/docs/architecture/workflows/): native CI, validation, security, and automation pipelines.
- [GitHub Agentic Workflows — About](https://github.github.com/gh-aw/about/): Markdown source, compilation, deterministic vs. agentic execution.
- [GitHub Agentic Workflows — Safe Outputs](https://github.github.io/gh-aw/reference/safe-outputs/): scoped, permission-controlled mutations independent of the agent's reasoning job.
