# Repository provisioning evidence

Read-only GitHub API observations retrieved on 2026-10-28 for the retained canary
`Samwise-OS/baseline-canary` (repository ID `1436487640`). The versioned manifest
records repository IDs for `.github` (`1436487227`), `repository-template`
(`1436487455`) and `baseline-canary` (`1436487640`). The same-name identity preflight
compared all three recorded IDs with the authenticated organization inventory and
found exact matches. A mismatch now fails before any metadata or content reconciliation;
an existing repository with no manifest ID requires an explicit adoption edit first.
Newly created entries without an ID return an adoption-required result so their ID can
be recorded before the next run.

## Community profile API

`GET /repos/Samwise-OS/baseline-canary/community/profile` returned health percentage
87 and these inherited defaults, with canonical GitHub HTML URLs pointing to `.github`:

| Default | URL reported by GitHub |
| --- | --- |
| Code of Conduct | https://github.com/Samwise-OS/.github/blob/main/CODE_OF_CONDUCT.md |
| Contributing guide | https://github.com/Samwise-OS/.github/blob/main/CONTRIBUTING.md |
| Pull request template | https://github.com/Samwise-OS/.github/blob/main/.github/PULL_REQUEST_TEMPLATE.md |

The response reported `issue_template: null`; no issue-template inheritance claim is
made from this endpoint. Its README URL points to the canary's own README. The API
response demonstrates GitHub's community-profile URL resolution; it does not establish
that a person saw or used these defaults in the browser UI.

## Issue form UI check

On 2026-10-28, the authenticated GitHub issue chooser at
https://github.com/Samwise-OS/baseline-canary/issues/new/choose displayed **Bug report**
and **Feature request** forms. Opening each form showed these required prompts:

- **Bug report**: “Reproduction and actual behavior” (with the hint to include version
  and minimal steps and redact secrets/personal data), and “Expected behavior”. The form
  preselected `bug` and `needs-triage`.
- **Feature request**: “Problem and desired outcome”, and “Observable acceptance
  criteria”. The form preselected `enhancement` and `needs-triage`.

No issue was created. This browser observation verifies the user-facing chooser and
form prompts. The Community Profile endpoint's `issue_template: null` did not enumerate
these YAML forms in `.github/ISSUE_TEMPLATE/`; for this multiple-form setup that field
is not a substitute for checking the chooser UI. This UI check does not prove that
every unauthenticated or alternate client sees identical behavior.

## Template origin and workflow

`GET /repos/Samwise-OS/baseline-canary` returned `template_repository.id` equal to
`1436487455`, matching the manifest ID of `Samwise-OS/repository-template`. This is
GitHub's repository metadata evidence for the template relationship.

The canary's standards workflow completed successfully on the provisioned main head
`7494407377bcf4dc89805528b9d7a04d4154d57e` in run
[40618028804](https://github.com/Samwise-OS/baseline-canary/actions/runs/40618028804).
The current acceptance PR #1 is open at head
`f7ea529b5775af6bb1b073448c8a58239d927710`; its run
[40618226036](https://github.com/Samwise-OS/baseline-canary/actions/runs/40618226036)
failed on the deliberately malformed PR fixture. No canary content was changed while
that acceptance PR was pending.
