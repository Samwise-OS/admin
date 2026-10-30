"""Validate the deliberately small Safe-Settings configuration surface."""

import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
EXPECTED_REPOSITORIES = {"admin", "baseline-canary"}
EXPECTED_RULESET = "samwise-default-branch"
EXPECTED_CHECK_CONTEXT = "baseline / standards"
EXPECTED_CHECK_APP_ID = 15368
ALLOWED_REPO_CONFIGS = {"baseline-canary.yml"}


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


def expected_ruleset():
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
                    "context": EXPECTED_CHECK_CONTEXT,
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


def validate_deployment(config):
    if set(config) != {"restrictedRepos"}:
        raise ValueError("deployment-settings.yml may contain only restrictedRepos")
    scope = config["restrictedRepos"]
    if not isinstance(scope, dict) or set(scope) != {"include"}:
        raise ValueError("restrictedRepos must use an include-only allowlist")
    if scope["include"] != sorted(EXPECTED_REPOSITORIES):
        raise ValueError("deployment allowlist must be exactly admin and baseline-canary")


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
    validate_settings(read_json_yaml(github / "settings.yml", root))
    validate_deployment(read_json_yaml(github / "deployment-settings.yml", root))

    repos = github / "repos"
    scan_config_directory(repos, ALLOWED_REPO_CONFIGS)
    scan_config_directory(github / "suborgs", set())
    repo_config = repos / "baseline-canary.yml"
    config = read_json_yaml(repo_config, root)
    if set(config) != {"rulesets"}:
        raise ValueError("baseline-canary.yml may contain only the repo-scoped rulesets key")
    if config["rulesets"] != [expected_ruleset()]:
        raise ValueError("baseline-canary ruleset differs from the exact reviewed payload")


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
