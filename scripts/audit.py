"""Read-only GitHub baseline comparison. Python 3.11+ and authenticated gh required."""

import argparse
import datetime
import hashlib
import json
import pathlib
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
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
    parser.add_argument("command", choices=("validate", "audit"))
    parser.add_argument("--output", type=pathlib.Path)
    args = parser.parse_args()
    config = load(ROOT / "config/organization.json")
    defaults = load(ROOT / ".github/settings.yml")
    ruleset = load(ROOT / "config/default-branch.ruleset.json")
    validate(config, defaults, ruleset)
    if args.command == "validate":
        print("Configuration valid; owner activation and operational acceptance remain pending.")
        return 0
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
