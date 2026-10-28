"""Validate the deliberately small Safe-Settings configuration surface."""

import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
EXPECTED_REPOSITORIES = {"admin", "baseline-canary"}
EXPECTED_RULESET = "samwise-default-branch"


def read_json_yaml(path):
    """Read the JSON-syntax YAML subset used here, without executable YAML tags."""
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ValueError(f"{path}: expected JSON-syntax YAML: {error}") from error
    if not isinstance(value, dict):
        raise ValueError(f"{path}: top-level value must be an object")
    return value


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


def validate_ruleset(path, config):
    allowed_top = {"rulesets"}
    if path.parent.name == "suborgs":
        allowed_top |= {"suborgrepos", "ruleset_scope"}
        if config.get("ruleset_scope") != "repo":
            raise ValueError(f"{path}: suborg rules must explicitly use repository scope")
        if config.get("suborgrepos") != ["baseline-canary"]:
            raise ValueError(f"{path}: suborg must target only baseline-canary")
    if set(config) != allowed_top:
        raise ValueError(f"{path}: unsupported or executable configuration keys")
    rulesets = config.get("rulesets")
    if not isinstance(rulesets, list):
        raise ValueError(f"{path}: rulesets must be a list")
    for ruleset in rulesets:
        if not isinstance(ruleset, dict) or ruleset.get("name") != EXPECTED_RULESET:
            raise ValueError(f"{path}: unexpected ruleset entry")
        if ruleset.get("enforcement") != "disabled":
            raise ValueError(f"{path}: ruleset remains disabled until live acceptance")
        if ruleset.get("bypass_actors") != []:
            raise ValueError(f"{path}: bypass actors are not approved")
        if ruleset.get("target") != "branch" or set(ruleset) - {
            "name", "target", "enforcement", "bypass_actors", "conditions", "rules"
        }:
            raise ValueError(f"{path}: unsupported ruleset shape")


def validate(root=ROOT):
    settings = read_json_yaml(root / ".github/settings.yml")
    validate_settings(settings)
    validate_deployment(read_json_yaml(root / ".github/deployment-settings.yml"))
    for directory in (root / ".github/repos", root / ".github/suborgs"):
        if not directory.exists():
            continue
        for path in sorted(directory.glob("*.yml")):
            if path.stem not in EXPECTED_REPOSITORIES and path.parent.name == "repos":
                raise ValueError(f"{path}: repository override is outside the approved scope")
            validate_ruleset(path, read_json_yaml(path))


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
