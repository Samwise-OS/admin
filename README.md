# Samwise-OS organization administration

This repository defines the GitHub organization foundation. Application development,
agent runtimes, external infrastructure and model orchestration are outside its scope.

**Status: bootstrap in progress; live operational acceptance is pending.**
Configuration files do not establish that GitHub is enforcing them.

- [Implementation proposal and owner decisions](docs/baseline-proposal.md)
- [Observed organization state](docs/observed-state.md)
- [Operating and recovery procedure](docs/operations.md)
- [Acceptance tests and evidence requirements](docs/acceptance.md)
- [Official-source research](docs/research/github-organization-baseline.md)

`.github/settings.yml` remains the sole proposed authority for shared repository
settings. It uses JSON syntax, which is also valid YAML, so the independent audit
can read the same document using Python's standard library. Safe-Settings is not
installed or authenticated yet; the App is registered. Organization policies are declared separately
in `config/organization.json`; they do not duplicate repository-setting ownership.

`scripts/audit.py` uses the official GitHub CLI for **GET requests only** and records
unreadable resources as unknown. `scripts/organization.py` reconciles its explicitly
declared organization policies and maintainer grants after verifying the authenticated
owner and target organization. See the operations document for invocation.

Local validation and CI verify the proposed configuration and audit semantics.
They are not a substitute for the organization acceptance tests.
