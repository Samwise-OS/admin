# Native reconciliation evidence — 2026-10-30

Scope: organization `349008063`, selected App installation `176024067`, managed
repositories `admin` and `baseline-canary`. Configuration revision:
`e8484407cdd456c1af3f6b3bcd377008e78c9020` (merged PR #7).

| Operation | Observed result | Evidence |
| --- | --- | --- |
| Reviewed preview | Success; six planned changes; zero managed mutation requests; supported trace | [run 41008940440](https://github.com/Samwise-OS/admin/actions/runs/41008940440) |
| First real apply | Success; three managed mutation requests; zero unclassified writes or trace errors | [run 41008996205](https://github.com/Samwise-OS/admin/actions/runs/41008996205) |
| Second real apply | Success; zero managed mutation requests; supported trace; zero failed installation syncs | [run 41009078745](https://github.com/Samwise-OS/admin/actions/runs/41009078745) |
| Independent repository readback | Both repositories disable merge/rebase merges, enable head-branch deletion, and disable wiki | Official REST `GET /repos/Samwise-OS/{admin,baseline-canary}` |
| Independent ruleset readback | Canary ruleset `26186884` active; no bypass actors; required `baseline / standards` from Actions App `15368` | Official REST `GET /repos/Samwise-OS/baseline-canary/rulesets/26186884` |
| Reporting check | `Safe-Settings` check `123910722258` succeeded, published by `samwise-os-safe-settings` | Official REST `GET /repos/Samwise-OS/admin/commits/e8484407cdd456c1af3f6b3bcd377008e78c9020/check-runs` |

The zero-write claim concerns managed repository configuration. Intentional check-run
reporting requests are excluded. This proves the bounded two-repository reconciliation
path; it does not claim all four repositories have converged or that functional canary
acceptance has completed. Subsequent expansion requires fresh evidence.

Prior PR #7 reviews found and corrected an overly permissive trace-support test and
inconsistent documentation of installation scope. The correction was committed at
`8708cc159841f1983eaa8cfe24fbdf407a91b21a` and its own governance run
[41008895239](https://github.com/Samwise-OS/admin/actions/runs/41008895239) succeeded
before merge. Local trace fixtures covered unrelated-origin rejection, unmanaged
repository rejection, managed reads with zero mutations, and write classification.
