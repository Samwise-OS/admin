# Issue tracker: GitHub

Specs and work tickets live in `Samwise-OS/admin` GitHub Issues. Use the connected
GitHub tools or official `gh` CLI; resolve the exact repository before each write.
Use body files for multiline CLI submissions. Fetch the full issue and comments
before implementing it. Record the base commit and acceptance evidence in each ticket.

Specifications and generated tickets are `ready-for-agent`; they do not need triage.
Create native issue blocking dependencies with database IDs, falling back to explicit
`Blocked by` links only if the API is unavailable. Implement the unblocked frontier.
Close only after observed acceptance; retain authentication blockers visibly.

PRs as a request surface: **no**. Incoming issues use the canonical triage roles.
Triage-generated posts start with the installed skill's AI disclaimer. Never triage
an internally generated ticket merely to move it through labels.
