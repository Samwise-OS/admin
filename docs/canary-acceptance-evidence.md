# Canary enforcement acceptance evidence

Observed 2026-10-30 through authenticated `gh` operations as `Samwise-x`. Scope was
`Samwise-OS/baseline-canary`; no admin repository was mutated. Repository ruleset
`26186884` read back as active on `~DEFAULT_BRANCH`, with no bypass actors, required
check `baseline / standards` bound to GitHub Actions App `15368`, and pull-request,
deletion, non-fast-forward and linear-history rules. GitHub reported
`current_user_can_bypass: never`. The owner can still edit repository policy; that
administrative capability is separate from a declared ruleset bypass actor.

## Live canary results

- **Failing check blocks PR merge.** PR #1 initially had a failed `baseline / standards`
  run (`40618226036`). `gh pr merge 1 --squash` without `--admin` exited 1 because the
  base branch policy prohibited the merge. After restoring `.editorconfig`, run
  `41009613542` passed the required check. A subsequent Git refs API fast-forward to
  the exact open PR head returned HTTP 200, and PR #1 became merged at that same commit.
  Read-only inspection confirms this was GitHub's PR merge path, not an unreviewed
  direct update: PR #1 is `MERGED`, and ruleset suite `4809172370` records both
  `pull_request` and `required_status_checks` as pass. This API operation therefore is
  not counted as evidence that direct pushes are allowed or blocked.
- **Unassociated direct update is blocked.** Created an unreferenced candidate commit
  `5d3ce1635e45e2ccebe6d1bcf8347bf386c16c2d` with parent equal to current canary main
  and a harmless probe file. PATCH of `refs/heads/main` to it with `force=false` was
  rejected (HTTP 422): “Changes must be made through a pull request” and required
  check `baseline / standards` was expected. Rule suite `4809191196` records active
  `pull_request` and `required_status_checks` failures. The main ref did not move.
- **Force update is blocked.** PATCH of main back to prior commit
  `7494407377bcf4dc89805528b9d7a04d4154d57e` with `force=true` was rejected (HTTP
  422): “Cannot force-push to this branch” and “Changes must be made through a pull
  request.” Rule suite `4809192437` records active `non_fast_forward` and
  `pull_request` failures. Main remained at `4c30b3e7172114f68911a1ac11edafe678fdc205`.
- **Missing required check blocks merge.** PR #2 changed the canary workflow to run a
  successful `fixture` job without emitting `baseline / standards`. Run `41009847094`
  succeeded for `fixture`; `gh pr merge 2 --squash` without `--admin` was rejected by
  base branch policy. PR #2 was rebased to current main for a second source test and
  closed unmerged.
- **A same-name user status did not satisfy the required check.** On rebased PR #2
  head `95078e0859909de3da2f040139a7853e29d6c57f`, Actions run `41010212569` produced
  only the successful `fixture` check from App `15368`. A separate successful legacy
  commit status with context `baseline / standards` was posted as `Samwise-x` (status
  ID `57646748399`). The combined PR status view showed that user-created status and
  the `fixture` check, but `gh pr merge 2 --squash` without `--admin` remained blocked
  by base-branch policy. PR #2 was closed unmerged. The result supports the configured
  App binding rejecting a same-name status from a user; the merge command returned a
  generic policy message, so no dedicated rule-suite evaluation was available for
  this PR-only attempt.
- **A same-name Actions workflow can substitute the check.** PR #3 used an alternate
  workflow whose only job echoed a success message and emitted exactly
  `baseline / standards`, without running the reusable standards contract. Run
  `41009986856` produced a successful check with that exact name from GitHub Actions
  App `15368`. PR #3 was closed unmerged. App binding identifies the Actions App and
  check context, but does not bind the check to an immutable workflow source or
  implementation. This remains a trust limitation.
- **Normal successful PR path works.** PR #4 added only a canary acceptance marker.
  The real reusable `baseline / standards` workflow passed in run `41010044859`; a
  normal `gh pr merge 4 --squash` without `--admin` succeeded. Ruleset suite
  `4809227785` records all configured rules as pass and merge commit
  `5e64e46780ae885d488f3a28730e0eb56742364d`.
- **Deletion enforcement was tested on an isolated disposable branch.** Created
  branch `codex/acceptance-delete` at current main, then temporarily installed active
  repository ruleset `26187318`, named `samwise-acceptance-delete-fixture`, scoped only
  to that exact ref and containing only the `deletion` rule with no bypass actors.
  DELETE of that branch was rejected with HTTP 422, “Cannot delete this branch.” Rule
  suite `4809265937` records that exact temporary ruleset's active deletion rule as
  failed. The temporary ruleset was removed by exact ID after verifying its name,
  repository source and branch scope; then the disposable branch was deleted. A final
  ruleset inventory showed only the original baseline ruleset `26186884`. That live
  baseline ruleset independently reads back with its own deletion rule active. The
  isolated test proves GitHub's deletion rule works for a matching branch; it does not
  attempt to delete the real default branch.

## Limits

Protected default-branch deletion was not attempted because deleting real branch
history is unsafe. The isolated disposable-branch test avoids that destructive action.
No application or platform implementation was added.
