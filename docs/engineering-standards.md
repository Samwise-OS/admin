# Engineering standards proposed for new repositories

Use a purpose description, explicit visibility and lifecycle status, a named owning
team/person, a main default branch, and lower-case kebab-case names. Reserve `.github`
and `admin` for organization infrastructure. Document prerequisites and validation
commands. Record repository-specific CI requirements before making checks mandatory.

Commit `.editorconfig`, `.gitattributes`, appropriate ignore rules, repository-local
CODEOWNERS, a PR template and the approved license decision in templates. This is an
organization foundation, so language-specific application tooling is chosen per project.
Do not invent a universal application build command.

The proposed public `.github` repository supplies CONTRIBUTING, CODE_OF_CONDUCT,
SUPPORT, SECURITY, issue forms and PR guidance. Keep its contents public-safe because
they may be displayed for private repositories too. An approved private security
reporting contact is a publication gate. No default license or inherited CODEOWNERS
is assumed. Local guidance overrides inherited defaults; verify overrides deliberately.

Reusable workflows must declare a narrow `workflow_call` contract, minimum permissions,
explicit secrets, timeouts and immutable dependencies. Publish one only when a canary
consumer demonstrates the real shared task. A workflow template is a discovery aid;
it is not enforced adoption or an upgrade channel. Language/build/test workflows and
specification-driven application development belong to subsequent engineering slices.

Every change to access, workflows, required checks or configuration ownership receives
documented review appropriate to the selected bootstrap model. Secret values never
belong in issues, PRs, source files or audit artifacts. Keep privileged reconciliation
separate from untrusted contribution validation.
