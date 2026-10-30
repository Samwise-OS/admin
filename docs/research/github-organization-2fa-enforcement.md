# GitHub organization 2FA enforcement: consequences and preflight

Research checked against GitHub primary documentation on 2026-10-30. No live organization state was queried or changed; the checklist below describes evidence to capture before any enforcement change.

## Consequences

- Enabling required 2FA affects organization members, outside collaborators, and billing managers. Members and billing managers without 2FA retain membership (and members continue consuming seats) but cannot access organization resources until compliant.
- Outside collaborators without 2FA, including bot/service accounts, are removed and lose access to organization repositories and private-repository forks. Their former privileges/settings can be reinstated for three months if an owner invites them back after they enable 2FA. An outside collaborator who later disables 2FA is removed automatically.
- A sole organization owner must keep personal 2FA enabled, or first disable the organization requirement to turn off personal 2FA.
- Requiring secure methods is a separate, stricter policy: secure methods are passkeys, security keys, authenticator apps, and GitHub Mobile. Users with no secure method or any insecure method (such as SMS) lose resource access; outside collaborators using SMS are removed.

Sources: [Require 2FA](https://docs.github.com/en/organizations/keeping-your-organization-secure/managing-two-factor-authentication-for-your-organization/requiring-two-factor-authentication-in-your-organization); [Reinstate outside collaborator](https://docs.github.com/en/organizations/managing-user-access-to-your-organizations-repositories/managing-outside-collaborators/reinstating-a-former-outside-collaborators-access-to-your-organization).

## Safe preflight evidence

1. Confirm the exact organization and current `two_factor_requirement_enabled` value using authenticated `GET /orgs/{org}` as an organization owner. This field reports whether the requirement is already enabled. [Organization REST endpoint](https://docs.github.com/en/rest/orgs/orgs#get-an-organization).
2. Capture complete, paginated owner-authenticated results/counts for `GET /orgs/{org}/members?filter=2fa_disabled` and `GET /orgs/{org}/outside_collaborators?filter=2fa_disabled`. The first filter is owner-only; both APIs paginate, so record that all pages were read. For a secure-method policy, also capture `filter=2fa_insecure` for each population. [Members API](https://docs.github.com/en/rest/orgs/members#list-organization-members); [Outside collaborators API](https://docs.github.com/en/rest/orgs/outside-collaborators#list-outside-collaborators-for-an-organization).
3. Reconcile API counts with the organization People and Outside collaborators 2FA status views, including billing managers, and identify bot/service accounts and access they would lose. The API members filter documents role filters as admin/member; do not treat it alone as a complete billing-manager impact list. [Viewing 2FA status](https://docs.github.com/en/organizations/keeping-your-organization-secure/managing-two-factor-authentication-for-your-organization/viewing-whether-users-in-your-organization-have-2fa-enabled).
4. Verify the acting owner has 2FA enabled. Notify members, outside collaborators, and billing managers at least one week before enforcement, and record the notice date and any outstanding exceptions. [Preparation guidance](https://docs.github.com/en/organizations/keeping-your-organization-secure/managing-two-factor-authentication-for-your-organization/preparing-to-require-two-factor-authentication-in-your-organization).
5. Write down expected effects before confirming the setting: number of members/billing managers who would be locked out until setup, outside collaborators (including bots) who would be removed, and private forks/repositories affected. Preserve timestamped sanitized counts/results as evidence.
6. After an authorized change, verify the organization flag with `GET /orgs/{org}` and inspect the organization audit log for `action:org.remove_outside_collaborator`; GitHub documents that this event identifies 2FA-noncompliant removals. These are post-change checks, not substitutes for preflight.

This research establishes platform behavior and a preflight method; it does not establish the live organization’s current 2FA state, member inventory, auth readiness, or readiness to enforce.
