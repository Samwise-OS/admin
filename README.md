# Samwise-OS organization governance

**Purpose:** The GitHub-native organization control plane for Samwise-OS. This repository declares organization and repository policy, provisions governed repositories, validates configuration, reconciles managed settings, and records operational acceptance evidence.

**Verified baseline (2026-11-03):** Six managed repositories have passed independently recorded managed-state readback after the Android repository's adoption ([apply and audit run](https://github.com/Samwise-OS/admin/actions/runs/41561843117)). The daily scheduled Safe-Settings reconciliation subsequently [completed successfully on November 3](https://github.com/Samwise-OS/admin/actions/runs/41653620878). The public baseline's canary PR, check-enforcement, drift-repair, and zero-write idempotence tests are recorded in [acceptance](docs/acceptance.md). Android device-side execution acceptance remains a separate pending gate.

## What is implemented

| Responsibility | Canonical source |
| --- | --- |
| Organization policy, owner/maintainer declaration, schedule | [`config/organization.json`](config/organization.json) |
| Managed repositories and immutable GitHub IDs | [`config/repositories.json`](config/repositories.json) |
| Shared repository settings | [`.github/settings.yml`](.github/settings.yml) |
| Derived per-repository rulesets and allowlist | [`.github/repos/`](.github/repos/) and [`.github/deployment-settings.yml`](.github/deployment-settings.yml) |
| Repository provisioning and reviewable content PRs | [`scripts/provision.py`](scripts/provision.py) |
| Owner-authenticated organization policy reconciliation | [`scripts/organization.py`](scripts/organization.py) |
| Read-only state comparison | [`scripts/audit.py`](scripts/audit.py) |
| Required secretless validation and receipts | [`scripts/doctor.py`](scripts/doctor.py) and [`validate.yml`](.github/workflows/validate.yml) |
| Safe-Settings reconciliation and readback | [`reconcile.yml`](.github/workflows/reconcile.yml) |
| Reusable repository standards check | [`repository-baseline.yml`](.github/workflows/repository-baseline.yml) |

The managed scope is `admin`, `.github`, `repository-template`, `baseline-canary`, `bootstrap-acceptance-20261030`, and `android`. New repositories are declared and adopted through the existing manifest/provisioning process.

## Validate the declared baseline

From this repository's root, with Python 3.11+:

```bash
python3 scripts/audit.py validate
python3 scripts/generate_repository_settings.py --check
python3 scripts/validate_safe_settings.py
python3 scripts/doctor.py --output .local/validation-receipt.json
```

These are secretless declaration checks. Authenticated GitHub readback, operational reconciliation, and functional enforcement have separate procedures and evidence.

## Operating documentation

- [Organization automation contract](docs/org-automation-contract.md): writers, authorities, reconciliation, and verification.
- [Operations](docs/operations.md): invocation, recovery, and evidence handling.
- [Operational acceptance](docs/acceptance.md): exercised behavior, provenance, and remaining acceptance gates.
- [Observed state](docs/observed-state.md): dated authenticated observations; historical sections remain historical.
- [Domain language](CONTEXT.md) and [architectural decisions](docs/adr/): existing vocabulary and binding decisions.
- [Engineering instructions](AGENTS.md): canonical Matt Pocock Skills methodology.

## Intended future state

[**Samwise-OS vision: intent-to-verified-execution and knowledge compounding**](docs/vision.md) defines the target architecture. It draws on [Microsoft HVE Core's agentic workflows](https://microsoft.github.io/hve-core/docs/architecture/agentic-workflows/) and GitHub Agentic Workflows. **The target architecture is a specification, not a claim that its issue-to-PR agent factory or telemetry-to-knowledge loop has been deployed.**

Organization governance stays here. Repository-specific applications, Android host/device execution, and future agentic implementation live behind their own approved contracts and acceptance evidence.
