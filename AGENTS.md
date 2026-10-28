# Samwise-OS organization engineering

Scope is GitHub organization infrastructure. Read `CONTEXT.md` and relevant `docs/adr/`
before changing the baseline. Verify through actual authenticated GitHub operations;
configuration presence and green local tests do not establish live enforcement.

## Agent skills

Use the installed `mattpocock-skills` plugin as the canonical engineering workflow.
Invoke its fully qualified names (`mattpocock-skills:research`, `:to-spec`, `:to-tickets`,
`:implement`, `:tdd`, `:code-review`, `:domain-modeling`, `:triage`) rather than inventing
similarly named skills. Resolve an installed skill's actual name before invocation.

### Issue tracker

Use this repository's GitHub Issues. Read `docs/agents/issue-tracker.md` before publishing
specifications, tickets or triage outcomes. Read `docs/agents/triage-labels.md` for roles.

### Domain docs

This is a single context: glossary in `CONTEXT.md`, decisions in `docs/adr/`.
Read `docs/agents/domain.md` when adding terms or recording a substantive tradeoff.

### Research and implementation

Delegate independent documentation/feasibility research to a native Codex subagent
using `mattpocock-skills:research`. Give it a bounded question, Markdown deliverable
and primary-source citation requirement. Continue independent work; await its artifact
where a decision depends on it. Keep short dependent operations in the principal.

Implement a ready ticket in vertical slices with red/green checks at the declared
GitHub API/CLI or workflow boundary. Finish with the skill's separate Standards and
Spec reviews against the ticket's recorded base. Record evidence before closing.

For future TypeScript repositories, apply `mattpocock-skills:setup-ts-deep-modules`
when TypeScript package boundaries exist; prove pass/fail/pass on a forbidden deep
import. Do not introduce a TypeScript application to this organization-only repository.

## Authority

The owner authorized completing this bootstrap with public repositories on GitHub Free
and autonomous routine decisions. Choose and document workable solo-owner defaults.
Request human interaction for authentication when required. Preserve credentials in
approved secret stores and publish sanitized evidence. Operate within the user's
scope; application/platform implementation remains a subsequent slice.
