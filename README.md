# Samwise-OS organization administration

This repository defines the GitHub organization foundation. Application development,
agent runtimes, external infrastructure and model orchestration are outside its scope.

**Status: proposed baseline; owner decisions and live acceptance are pending.**
Configuration files do not establish that GitHub is enforcing them.

- [Implementation proposal and owner decisions](docs/baseline-proposal.md)
- [Observed organization state](docs/observed-state.md)
- [Operating and recovery procedure](docs/operations.md)
- [Acceptance tests and evidence requirements](docs/acceptance.md)
- [Official-source research](docs/research/github-organization-baseline.md)

`.github/settings.yml` remains the sole proposed authority for shared repository
settings. It uses JSON syntax, which is also valid YAML, so the independent audit
can read the same document using Python's standard library. Safe-Settings is not
installed or activated by this change. Organization policies are declared separately
in `config/organization.json`; they do not duplicate repository-setting ownership.

`scripts/audit.py` uses the official GitHub CLI for **GET requests only**. It never
refreshes credentials, creates resources, changes settings or schedules work. It
records unreadable resources as unknown. See the operations document for invocation.

Local validation and CI verify the proposed configuration and audit semantics.
They are not a substitute for the organization acceptance tests.
