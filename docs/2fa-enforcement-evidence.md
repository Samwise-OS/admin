# Organization two-factor enforcement evidence — 2026-10-30

The authenticated owner API reported Samwise-x personal 2FA enabled. Full member inventory contained Samwise-x and BVEnterprisess; the owner-only noncompliant-member filter returned zero, and outside collaborator inventory was empty.

The principal used the existing authenticated GitHub owner browser session to enable the organization requirement at [authentication security](https://github.com/organizations/Samwise-OS/settings/security). The separate secure-method-only restriction was not selected; it was not part of this declared change. GitHub confirmed saving the requirement.

Independent official CLI API readback returned `two_factor_requirement_enabled: true`. The subsequent member listing still contained both Samwise-x and BVEnterprisess. No member or outside collaborator was removed by this operation.

Personal recovery codes remain private and were neither requested nor inspected. Enrollment/enforcement and retained membership are verified; possession or testing of personal recovery codes is not claimed. The versioned policy declares the requirement, audits it, and treats drift as incomplete; GitHub's supported API does not provide a setter for automatic repair of this particular control.
