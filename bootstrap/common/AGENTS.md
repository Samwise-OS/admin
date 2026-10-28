# Engineering workflow

Use installed `mattpocock-skills` as the canonical engineering workflow. Resolve and
invoke actual fully qualified skill names; keep local engineering conventions in
this repository. Read `CONTEXT.md` and relevant `docs/adr/` when present.

## Agent skills

Specs/tickets live in this repository's GitHub Issues: see `docs/agents/issue-tracker.md`.
Canonical triage roles: see `docs/agents/triage-labels.md`. Domain glossary and ADR
rules: see `docs/agents/domain.md`.

Delegate independent documentation/feasibility investigations to a native Codex
subagent using `mattpocock-skills:research`, with a bounded question, cited primary
sources and a Markdown deliverable. Continue independent work while it executes;
read the artifact before making a dependent decision.

Use `mattpocock-skills:to-spec` and `:to-tickets` for a buildable specification and
dependency-linked vertical slices. Implement ready tickets with `:implement` and
`:tdd`, testing behavior at agreed public seams. Complete separate Standards/Spec
reviews with `:code-review` before committing. Apply `:triage` to incoming requests,
not generated implementation tickets. Record substantive tradeoffs with `:domain-modeling`.

When a TypeScript project introduces package boundaries, use
`mattpocock-skills:setup-ts-deep-modules` and prove forbidden deep imports fail.
Project CI adds real build/test/typechecking on top of the shared organization baseline.
