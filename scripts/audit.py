"""Read-only GitHub baseline comparison. Python 3.11+ and authenticated gh required."""

import argparse
import datetime
import hashlib
import json
import pathlib
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
API_VERSION = "2022-11-28"


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def validate(config, defaults, ruleset):
    if config.get("schema_version") != 1:
        raise ValueError("Unsupported schema_version")
    if (config.get("organization"), config.get("organization_id")) != (
        "Samwise-OS", 349008063
    ):
        raise ValueError("Organization identity does not match the approved boundary")
    if config.get("admin_repository") != "admin":
        raise ValueError("Unexpected administration repository")
    if type(config.get("admin_repository_id")) is not int or config["admin_repository_id"] <= 0:
        raise ValueError("An immutable admin repository ID is required")
    if (not defaults.get("repository") or
            set(defaults) not in ({"repository"}, {"repository", "additive_plugins"}) or
            defaults.get("additive_plugins", ["rulesets"]) != ["rulesets"]):
        raise ValueError("Expected repository defaults and optional rulesets additive plugin")
    fields = {
        "has_issues", "has_wiki", "allow_squash_merge", "allow_merge_commit",
        "allow_rebase_merge", "delete_branch_on_merge"
    }
    if set(defaults["repository"]) != fields or any(
        type(value) is not bool for value in defaults["repository"].values()
    ):
        raise ValueError("Repository defaults must have exactly the supported boolean fields")
    provisioning = config["provisioning"]
    if provisioning["default_visibility"] not in (None, "public", "private"):
        raise ValueError("Unsupported visibility")
    approvals = provisioning["review_approvals"]
    if approvals is not None and (type(approvals) is not int or not 0 <= approvals <= 6):
        raise ValueError("Invalid review approval count")
    if ruleset["name"] != "samwise-default-branch" or ruleset["enforcement"] != "disabled":
        raise ValueError("The proposal ruleset must remain disabled until activation review")
    if ruleset["bypass_actors"]:
        raise ValueError("An unreviewed bypass actor is present")


def get(endpoint, paginated=False):
    command = [
        "gh", "api", "--hostname", "github.com", "--method", "GET",
        "-H", f"X-GitHub-Api-Version: {API_VERSION}",
        "-H", "Accept: application/vnd.github+json", endpoint
    ]
    if paginated:
        command += ["--paginate", "--slurp"]
    result = subprocess.run(command, capture_output=True, text=True, timeout=120)
    if result.returncode:
        try:
            error = json.loads(result.stdout)
        except json.JSONDecodeError:
            error = {}
        # gh --slurp can wrap an HTTP error object in a page array.
        if isinstance(error, list):
            error = next((item for item in error if isinstance(item, dict)), {})
        if not isinstance(error, dict):
            error = {}
        return {"state": "unknown", "endpoint": endpoint,
                "http_status": error.get("status"),
                "reason": error.get("message", "GitHub CLI request failed")}
    value = json.loads(result.stdout)
    if paginated:
        if not isinstance(value, list) or any(not isinstance(page, list) for page in value):
            raise ValueError(f"Unexpected paginated response from {endpoint}")
        value = [entry for page in value for entry in page]
    return {"state": "observed", "endpoint": endpoint, "value": value}


def compare(observation, desired):
    if observation["state"] != "observed":
        return {"state": "unknown", "differences": []}
    actual = observation["value"]
    differences = []
    for key, expected in sorted(desired.items()):
        if key not in actual or actual[key] != expected:
            differences.append({"field": key, "expected": expected,
                                "observed": actual.get(key), "missing": key not in actual})
    return {"state": "drift" if differences else "match", "differences": differences}


def compare_projection(actual, expected, path=""):
    """Compare only declared fields, while requiring arrays to match exactly."""
    differences = []
    if isinstance(expected, dict):
        if not isinstance(actual, dict):
            return [path or "$" ]
        for key, value in expected.items():
            child = f"{path}.{key}" if path else key
            if key not in actual:
                differences.append(child)
            else:
                differences.extend(compare_projection(actual[key], value, child))
        return differences
    if isinstance(expected, list):
        if not isinstance(actual, list) or len(actual) != len(expected):
            return [path or "$" ]
        for index, (actual_item, expected_item) in enumerate(zip(actual, expected)):
            differences.extend(compare_projection(actual_item, expected_item,
                                                  f"{path}[{index}]"))
        return differences
    return [] if actual == expected else [path or "$" ]


def managed_ruleset_observation(repository, expected, fetch):
    endpoint = f"repos/Samwise-OS/{repository}/rulesets?per_page=100"
    summaries = fetch(endpoint, paginated=True)
    if summaries.get("state") != "observed":
        return {"state": "unknown", "differences": [],
                "http_status": summaries.get("http_status")}
    if (not isinstance(summaries.get("value"), list)
            or any(not isinstance(item, dict) for item in summaries["value"])):
        return {"state": "unknown", "differences": [], "reason": "malformed-list"}
    matches = [item for item in summaries["value"]
               if isinstance(item, dict) and item.get("name") == expected["name"]]
    if len(matches) != 1:
        return {"state": "drift", "differences": ["ruleset.name"]}
    ruleset_id = matches[0].get("id")
    if type(ruleset_id) is not int or ruleset_id <= 0:
        return {"state": "unknown", "differences": [], "reason": "missing-ruleset-id"}
    details = fetch(f"repos/Samwise-OS/{repository}/rulesets/{ruleset_id}")
    if details.get("state") != "observed":
        return {"state": "unknown", "differences": [],
                "http_status": details.get("http_status")}
    if not isinstance(details.get("value"), dict):
        return {"state": "unknown", "differences": [], "reason": "malformed-details"}
    differences = compare_projection(details["value"], expected)
    return {"state": "drift" if differences else "match",
            "differences": differences}


def audit_managed_repositories(config, defaults, fetch=get, root=ROOT):
    """Read back only declared repositories, their defaults, and their named rulesets."""
    from scripts.validate_safe_settings import managed_repositories

    admin, managed = managed_repositories(root)
    root = pathlib.Path(root)
    desired_repository = defaults["repository"]
    observations = {}
    comparisons = {}
    organization = fetch(f"orgs/{config['organization']}")
    observations["organization:identity"] = organization
    if organization.get("state") != "observed":
        comparisons["organization:identity"] = {"state": "unknown", "differences": []}
        return {"scope": "declared-managed-repositories",
                "organization": config["organization"], "admin_repository": admin,
                "comparison_state": "incomplete", "comparisons": comparisons,
                "observations": observations}
    if not isinstance(organization.get("value"), dict) or organization["value"].get("id") != config["organization_id"]:
        comparisons["organization:identity"] = {"state": "drift", "differences": ["organization.id"]}
        return {"scope": "declared-managed-repositories",
                "organization": config["organization"], "admin_repository": admin,
                "comparison_state": "drift", "comparisons": comparisons,
                "observations": observations}
    repository_manifest = json.loads((root / "config/repositories.json").read_text(encoding="utf-8"))
    identities = {entry["name"]: entry.get("id") for entry in repository_manifest["repositories"]}
    identities[admin] = config.get("admin_repository_id")
    for name in managed:
        expected_id = identities.get(name)
        if type(expected_id) is not int or expected_id <= 0:
            observations[f"repository:{name}:identity"] = {"state": "unknown"}
            comparisons[f"repository:{name}:identity"] = {
                "state": "unknown", "differences": ["manifest.id"]
            }
            continue
        details = fetch(f"repos/{config['organization']}/{name}")
        observations[f"repository:{name}"] = details
        if details.get("state") != "observed" or not isinstance(details.get("value"), dict):
            comparisons[f"repository:{name}:identity"] = {"state": "unknown", "differences": []}
            continue
        actual = details["value"]
        owner = actual.get("owner")
        identity_differences = []
        identity_unknown = ("id" not in actual or "full_name" not in actual
                            or not isinstance(owner, dict)
                            or "login" not in owner or "id" not in owner)
        if actual.get("id") != expected_id:
            identity_differences.append("id")
        if actual.get("full_name") != f"{config['organization']}/{name}":
            identity_differences.append("full_name")
        if not isinstance(owner, dict):
            identity_differences.append("owner")
        else:
            if str(owner.get("login", "")).casefold() != config["organization"].casefold():
                identity_differences.append("owner.login")
            if owner.get("id") != config["organization_id"]:
                identity_differences.append("owner.id")
        if identity_differences:
            state = "unknown" if identity_unknown else "drift"
            comparisons[f"repository:{name}:identity"] = {
                "state": state, "differences": identity_differences
            }
            continue
        comparisons[f"repository:{name}:identity"] = {"state": "match", "differences": []}
        comparisons[f"repository:{name}:settings"] = compare(details, desired_repository)
        repo_config_path = root / ".github" / "repos" / f"{name}.yml"
        try:
            repo_config = json.loads(repo_config_path.read_text(encoding="utf-8"))
            expected_rulesets = repo_config["rulesets"]
            if not isinstance(expected_rulesets, list) or len(expected_rulesets) != 1:
                raise ValueError("expected exactly one managed ruleset")
        except (OSError, KeyError, TypeError, json.JSONDecodeError, ValueError):
            raise ValueError(f"Invalid generated ruleset declaration for {name}")
        observation = managed_ruleset_observation(name, expected_rulesets[0], fetch)
        observations[f"repository:{name}:managed_ruleset"] = observation
        comparisons[f"repository:{name}:managed_ruleset"] = {
            "state": observation["state"], "differences": observation["differences"]
        }
    incomplete = any(item["state"] == "unknown" for item in comparisons.values())
    drift = any(item["state"] == "drift" for item in comparisons.values())
    return {
        "scope": "declared-managed-repositories",
        "organization": config["organization"],
        "admin_repository": admin,
        "comparison_state": "incomplete" if incomplete else ("drift" if drift else "match"),
        "comparisons": comparisons,
        "observations": observations,
    }


def sanitized_managed_comparisons(comparisons):
    rows = []
    for key, value in sorted(comparisons.items()):
        if key == "organization:identity":
            rows.append({"name": "Samwise-OS", "control": "organization_identity",
                         "state": value["state"],
                         "difference_paths": value["differences"]})
            continue
        _, _, remainder = key.partition(":")
        repository, separator, control = remainder.partition(":")
        differences = value["differences"]
        paths = [item.get("field", "unknown") if isinstance(item, dict) else item
                 for item in differences]
        rows.append({"name": repository,
                     "control": control if separator else "repository_settings",
                     "state": value["state"],
                     "difference_paths": paths})
    return rows


def audit(config, defaults, fetch=get):
    org = config["organization"]
    observations = {"actor": fetch("user"), "organization": fetch(f"orgs/{org}")}
    identity = observations["organization"]
    if identity["state"] != "observed" or identity["value"].get("id") != config["organization_id"]:
        raise ValueError("Cannot establish target organization identity; audit aborted")
    endpoints = {
        "membership": f"user/memberships/orgs/{org}",
        "repositories": f"orgs/{org}/repos?type=all&per_page=100",
        "teams": f"orgs/{org}/teams?per_page=100",
        "owners": f"orgs/{org}/members?role=admin&per_page=100",
        "members": f"orgs/{org}/members?per_page=100",
        "outside_collaborators": f"orgs/{org}/outside_collaborators?per_page=100",
        "organization_actions": f"orgs/{org}/actions/permissions",
        "organization_selected_actions": f"orgs/{org}/actions/permissions/selected-actions",
        "organization_workflow_permissions": f"orgs/{org}/actions/permissions/workflow",
        "organization_rulesets": f"orgs/{org}/rulesets?per_page=100"
    }
    for key, endpoint in endpoints.items():
        observations[key] = fetch(endpoint, paginated="per_page" in endpoint)
    rulesets = observations["organization_rulesets"]
    if (rulesets["state"] == "unknown" and rulesets.get("http_status") == "403" and
            "upgrade to github team" in rulesets.get("reason", "").lower()):
        rulesets["state"] = "unsupported_plan"
    comparisons = {"organization_settings": compare(identity, config["organization_settings"])}
    for key in ("organization_actions", "organization_selected_actions", "organization_workflow_permissions"):
        comparisons[key] = compare(observations[key], config[key])
    repositories = observations["repositories"]
    if repositories["state"] == "observed":
        for summary in sorted(repositories["value"], key=lambda repo: repo["name"]):
            name = summary["name"]
            full_name = summary["full_name"]
            if summary.get("owner", {}).get("login", "").lower() != org.lower():
                raise ValueError("Repository inventory escaped organization boundary")
            details = fetch(f"repos/{full_name}")
            observations[f"repository:{name}"] = details
            if summary["archived"]:
                comparisons[f"repository:{name}"] = {"state": "excluded-archived", "differences": []}
                continue
            comparisons[f"repository:{name}"] = compare(details, defaults["repository"])
            for suffix, endpoint in (
                ("rulesets", f"repos/{full_name}/rulesets?per_page=100"),
                ("workflow_permissions", f"repos/{full_name}/actions/permissions/workflow"),
            ):
                observation = fetch(endpoint, paginated=suffix == "rulesets")
                observations[f"repository:{name}:{suffix}"] = observation
            comparisons[f"repository:{name}:workflow_permissions"] = compare(
                observations[f"repository:{name}:workflow_permissions"],
                config["organization_workflow_permissions"]
            )
    managed = audit_managed_repositories(config, defaults, fetch)
    observations.update(managed["observations"])
    comparisons.update(managed["comparisons"])
    incomplete = any(value["state"] == "unknown" for value in observations.values())
    drift = any(value["state"] == "drift" for value in comparisons.values())
    return {
        "observed_at_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "api_version": API_VERSION,
        "organization": org,
        "comparison_state": "incomplete" if incomplete else ("drift" if drift else "match"),
        "operationally_accepted": False,
        "acceptance_note": "Readback alone cannot certify enforcement, provisioning or idempotence.",
        "owner_decisions_pending": config["owner_decisions_pending"],
        "unsupported_plan_resources": [key for key, value in observations.items()
                                        if value["state"] == "unsupported_plan"],
        "comparisons": comparisons,
        "observations": observations
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("validate", "audit", "audit-managed"))
    parser.add_argument("--output", type=pathlib.Path)
    args = parser.parse_args()
    config = load(ROOT / "config/organization.json")
    defaults = load(ROOT / ".github/settings.yml")
    ruleset = load(ROOT / "config/default-branch.ruleset.json")
    validate(config, defaults, ruleset)
    if args.command == "validate":
        print("Configuration valid; live reconciliation and functional acceptance are verified separately.")
        return 0
    if args.command == "audit-managed":
        report = audit_managed_repositories(config, defaults)
        report["schema_version"] = 1
        report["observed_at_utc"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
        from scripts.validate_safe_settings import managed_repositories

        report["configuration_sha256"] = hashlib.sha256(json.dumps(
            [config, defaults, ruleset, load(ROOT / "config/repositories.json"),
             [load(ROOT / ".github/repos" / f"{name}.yml")
              for name in managed_repositories(ROOT)[1]]],
            sort_keys=True, separators=(",", ":")
        ).encode()).hexdigest()
        if args.output:
            destination = args.output.resolve()
            local = (ROOT / ".local").resolve()
            if not destination.is_relative_to(local):
                raise ValueError("Audit output must stay under ignored .local/")
            destination.parent.mkdir(parents=True, exist_ok=True)
            receipt = {key: value for key, value in report.items()
                       if key not in ("observations", "comparisons")}
            receipt["repositories"] = sanitized_managed_comparisons(report["comparisons"])
            destination.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
        print(json.dumps({
            "scope": report["scope"], "comparison_state": report["comparison_state"],
            "repositories": sanitized_managed_comparisons(report["comparisons"]),
        }, indent=2))
        return {"match": 0, "drift": 2, "incomplete": 3}[report["comparison_state"]]
    report = audit(config, defaults)
    report["configuration_sha256"] = hashlib.sha256(json.dumps(
        [config, defaults, ruleset], sort_keys=True, separators=(",", ":")
    ).encode()).hexdigest()
    if args.output:
        destination = args.output.resolve()
        local = (ROOT / ".local").resolve()
        if not destination.is_relative_to(local):
            raise ValueError("Audit output must stay under ignored .local/ to avoid publishing access inventory")
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "comparison_state": report["comparison_state"],
        "operationally_accepted": False,
        "drift_resources": [key for key, value in report["comparisons"].items() if value["state"] == "drift"],
        "unknown_resources": [key for key, value in report["observations"].items() if value["state"] == "unknown"]
    }, indent=2))
    return {"match": 0, "drift": 2, "incomplete": 3}[report["comparison_state"]]


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (ValueError, KeyError, OSError, subprocess.TimeoutExpired) as error:
        print(f"Audit failed: {error}", file=sys.stderr)
        sys.exit(4)
