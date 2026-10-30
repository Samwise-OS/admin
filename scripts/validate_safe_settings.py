"""Validate the deliberately small Safe-Settings configuration surface."""

import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
EXPECTED_ORGANIZATION = "Samwise-OS"
EXPECTED_ORGANIZATION_ID = 349008063
EXPECTED_ADMIN_REPOSITORY = "admin"
EXPECTED_RULESET = "samwise-default-branch"
EXPECTED_CHECK_APP_ID = 15368


def managed_repositories(root=ROOT):
    """Load the sole repository scope from organization and repository manifests."""
    root = pathlib.Path(root).resolve(strict=True)
    config_dir = root / "config"
    if config_dir.is_symlink() or not config_dir.is_dir():
        raise ValueError("config must be a real directory inside the checkout")
    organization = read_json_yaml(config_dir / "organization.json", root)
    repositories = read_json_yaml(config_dir / "repositories.json", root)
    admin = organization.get("admin_repository")
    entries = repositories.get("repositories")
    if (organization.get("organization") != EXPECTED_ORGANIZATION
        or repositories.get("organization") != EXPECTED_ORGANIZATION
        or organization.get("organization_id") != EXPECTED_ORGANIZATION_ID
        or repositories.get("organization_id") != EXPECTED_ORGANIZATION_ID
        or admin != EXPECTED_ADMIN_REPOSITORY):
        raise ValueError("Repository authority manifests must identify the authorized Samwise-OS organization and admin repository")
    if not isinstance(entries, list):
        raise ValueError("Repository authority manifests contain invalid repository declarations")
    names = [entry.get("name") for entry in entries if isinstance(entry, dict)]
    if len(names) != len(entries) or any(not valid_repository_name(name) for name in names):
        raise ValueError("Repository authority manifests contain an invalid repository name")
    if len(set(names)) != len(names) or admin in names:
        raise ValueError("Repository authority manifests contain duplicate managed names")
    return admin, sorted([admin, *names])


def valid_repository_name(name):
    return isinstance(name, str) and (name == ".github" or re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", name))


def read_json_yaml(path, root):
    """Read the JSON-syntax YAML subset and reject links or escapes."""
    root = root.resolve(strict=True)
    if path.is_symlink():
        raise ValueError(f"{path}: symlinked configuration is forbidden")
    try:
        resolved = path.resolve(strict=True)
        resolved.relative_to(root)
        value = json.loads(resolved.read_text(encoding="utf-8"))
    except (OSError, ValueError, json.JSONDecodeError) as error:
        raise ValueError(f"{path}: expected in-root JSON-syntax YAML: {error}") from error
    if not isinstance(value, dict):
        raise ValueError(f"{path}: top-level value must be an object")
    return value


def expected_ruleset(context):
    return {
        "name": EXPECTED_RULESET,
        "target": "branch",
        "enforcement": "active",
        "bypass_actors": [],
        "conditions": {"ref_name": {
            "include": ["~DEFAULT_BRANCH"],
            "exclude": [],
        }},
        "rules": [
            {"type": "deletion"},
            {"type": "non_fast_forward"},
            {"type": "required_linear_history"},
            {"type": "pull_request", "parameters": {
                "required_approving_review_count": 0,
                "dismiss_stale_reviews_on_push": True,
                "require_code_owner_review": False,
                "require_last_push_approval": False,
                "required_review_thread_resolution": True,
                "allowed_merge_methods": ["squash"],
            }},
            {"type": "required_status_checks", "parameters": {
                "strict_required_status_checks_policy": True,
                "do_not_enforce_on_create": False,
                "required_status_checks": [{
                    "context": context,
                    "integration_id": EXPECTED_CHECK_APP_ID,
                }],
            }},
        ],
    }


def validate_settings(settings):
    if set(settings) != {"repository", "additive_plugins"}:
        raise ValueError("settings.yml must contain only repository and additive_plugins")
    if settings["additive_plugins"] != ["rulesets"]:
        raise ValueError("additive_plugins must preserve unrelated rulesets")
    fields = {
        "has_issues", "has_wiki", "allow_squash_merge", "allow_merge_commit",
        "allow_rebase_merge", "delete_branch_on_merge",
    }
    repository = settings["repository"]
    if not isinstance(repository, dict) or set(repository) != fields:
        raise ValueError("repository must contain exactly the approved boolean defaults")
    if any(type(value) is not bool for value in repository.values()):
        raise ValueError("repository defaults must be booleans")


def validate_deployment(config, managed):
    if set(config) != {"restrictedRepos"}:
        raise ValueError("deployment-settings.yml may contain only restrictedRepos")
    scope = config["restrictedRepos"]
    if not isinstance(scope, dict) or set(scope) != {"include"}:
        raise ValueError("restrictedRepos must use an include-only allowlist")
    if scope["include"] != managed:
        raise ValueError("deployment allowlist must exactly match the sorted managed repository set")


def scan_config_directory(directory, allowed_files):
    """Reject alternate extensions, nested paths, aliases, and symlink entries."""
    if directory.is_symlink():
        raise ValueError(f"{directory}: symlinked configuration directory is forbidden")
    if not directory.exists():
        return
    if not directory.is_dir():
        raise ValueError(f"{directory}: expected a configuration directory")
    for entry in directory.iterdir():
        if entry.is_symlink():
            raise ValueError(f"{entry}: symlinked configuration is forbidden")
        if not entry.is_file() or entry.name not in allowed_files:
            raise ValueError(f"{entry}: configuration path is outside the approved set")


def validate(root=ROOT):
    root = root.resolve(strict=True)
    github = root / ".github"
    if github.is_symlink() or not github.is_dir():
        raise ValueError(".github must be a real directory inside the checkout")
    admin, managed = managed_repositories(root)
    validate_settings(read_json_yaml(github / "settings.yml", root))
    validate_deployment(read_json_yaml(github / "deployment-settings.yml", root), managed)

    repos = github / "repos"
    expected_files = {f"{name}.yml" for name in managed}
    scan_config_directory(repos, expected_files)
    scan_config_directory(github / "suborgs", set())
    for name in managed:
        repo_config = repos / f"{name}.yml"
        config = read_json_yaml(repo_config, root)
        if set(config) != {"rulesets"}:
            raise ValueError(f"{repo_config.name} may contain only the repo-scoped rulesets key")
        context = "governance" if name == admin else "baseline / standards"
        if config["rulesets"] != [expected_ruleset(context)]:
            raise ValueError(f"{repo_config.name} ruleset differs from the exact reviewed payload")


def main():
    try:
        validate()
    except ValueError as error:
        print(error, file=sys.stderr)
        return 1
    print("Safe-Settings configuration is within the reviewed bounded schema.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
