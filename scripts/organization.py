"""Idempotent organization policy reconciler using the official gh REST client."""
import argparse
import json
import pathlib
import subprocess
import sys

from scripts.validate_safe_settings import managed_repositories

ROOT = pathlib.Path(__file__).resolve().parents[1]
API_VERSION = "2022-11-28"
ORG_API_WRITABLE_FIELDS = {
    "default_repository_permission", "members_can_create_repositories",
    "members_can_create_public_repositories", "members_can_create_private_repositories"
}
TEAM_REPOSITORY_PERMISSIONS = {"maintain", "push", "pull", "triage", "admin"}
TEAM_PERMISSION_STRENGTH = {"pull": 1, "triage": 2, "push": 3, "maintain": 4, "admin": 5}


def observed_team_permission(repository):
    """Return the strongest reported role when older fixtures omit role_name."""
    role_name = repository.get("role_name")
    if role_name is not None:
        return role_name if role_name in TEAM_PERMISSION_STRENGTH else None
    permissions = repository.get("permissions", {})
    if not isinstance(permissions, dict):
        return None
    granted = [name for name in TEAM_PERMISSION_STRENGTH
               if permissions.get(name) is True]
    return max(granted, key=TEAM_PERMISSION_STRENGTH.get) if granted else None


def team_repository_grants(config, root=None):
    """Resolve team grants only within the repository authority manifests."""
    teams = config.get("teams", [])
    if not teams:
        return {}
    _, managed = managed_repositories(ROOT if root is None else root)
    allowed_repositories = set(managed)
    result = {}
    for team in teams:
        slug = team.get("slug")
        if not isinstance(slug, str) or not slug:
            raise ValueError("Team configuration requires a non-empty slug")
        if slug in result:
            raise ValueError(f"Duplicate team configuration for {slug}")
        has_permission = "repository_permission" in team
        has_grants = "repository_grants" in team
        if has_permission and has_grants:
            raise ValueError(f"Team {slug} cannot define both repository_permission and repository_grants")
        if has_permission:
            permission = team["repository_permission"]
            if not isinstance(permission, str) or permission not in TEAM_REPOSITORY_PERMISSIONS:
                raise ValueError(f"Team {slug} has an unsupported repository permission")
            grants = {repository: permission for repository in managed}
        else:
            grants = team.get("repository_grants", {})
            if not isinstance(grants, dict):
                raise ValueError(f"Team {slug} repository_grants must be an object")
            if set(grants) - allowed_repositories:
                raise ValueError(f"Team {slug} repository_grants include unmanaged repositories")
            if any(not isinstance(permission, str) or permission not in TEAM_REPOSITORY_PERMISSIONS
                   for permission in grants.values()):
                raise ValueError(f"Team {slug} has an unsupported repository permission")
        result[slug] = grants
    return result


def gh(endpoint, method="GET", payload=None):
    paginate = method.upper() == "GET" and "per_page=" in endpoint
    command = ["gh", "api", "--hostname", "github.com", "--method", method,
               "-H", f"X-GitHub-Api-Version: {API_VERSION}",
               "-H", "Accept: application/vnd.github+json", endpoint]
    if paginate:
        command += ["--paginate", "--slurp"]
    if payload is not None:
        command += ["--input", "-"]
    result = subprocess.run(command, input=None if payload is None else json.dumps(payload),
                            capture_output=True, text=True, timeout=120)
    if result.returncode:
        try:
            error = json.loads(result.stdout or result.stderr)
        except json.JSONDecodeError:
            error = {}
        return {"ok": False, "status": error.get("status"),
                "message": error.get("message", result.stderr.strip() or "GitHub request failed")}
    try:
        value = json.loads(result.stdout) if result.stdout.strip() else {}
    except json.JSONDecodeError:
        return {"ok": False, "message": f"Invalid JSON response from {endpoint}"}
    if paginate:
        if not isinstance(value, list) or any(not isinstance(page, list) for page in value):
            return {"ok": False, "message": f"Unexpected paginated response shape from {endpoint}"}
        value = [item for page in value for item in page]
    return {"ok": True, "value": value}


def plan(config, organization, current):
    if organization.get("id") != config["organization_id"]:
        raise ValueError("Organization ID mismatch; refusing to plan writes")
    writes = []
    priority = ["organization_settings", "organization_actions", "organization_selected_actions", "organization_workflow_permissions"]
    for resource in priority:
        endpoint = current[resource]
        desired = config[resource]
        observed = endpoint.get("value") if endpoint.get("ok") else None
        if observed is None:
            # A 409 is expected for selected-actions while policy is currently 'all'.
            if resource == "organization_selected_actions" and current["organization_actions"].get("value", {}).get("allowed_actions") == "all":
                observed = {}
            else:
                raise RuntimeError(f"Cannot determine {resource}: {endpoint}")
        changed = {k: v for k, v in desired.items() if observed.get(k) != v}
        if resource == "organization_settings":
            # The documented Update an organization body has no delete/visibility controls.
            changed = {k: v for k, v in changed.items() if k in ORG_API_WRITABLE_FIELDS}
        if changed:
            writes.append({"resource": resource, "fields": changed})
    return writes


def reconcile(config, request=gh):
    # Validate all requested access before any API read or write.
    resolved_team_grants = team_repository_grants(config)
    org = config["organization"]
    identity = request(f"orgs/{org}")
    if not identity.get("ok") or identity["value"].get("id") != config["organization_id"]:
        raise RuntimeError("Cannot establish target organization identity")
    actor = request("user")
    membership = request(f"user/memberships/orgs/{org}")
    if not actor.get("ok") or not membership.get("ok"):
        raise RuntimeError("Cannot establish authenticated actor and organization role")
    if actor["value"].get("login", "").lower() != "samwise-x" or membership["value"].get("role") != "admin":
        raise RuntimeError("Authenticated actor is not the verified organization owner")
    resources = {
        "organization_settings": (f"orgs/{org}", "PATCH", config["organization_settings"]),
        "organization_actions": (f"orgs/{org}/actions/permissions", "PUT", config["organization_actions"]),
        "organization_selected_actions": (f"orgs/{org}/actions/permissions/selected-actions", "PUT", config["organization_selected_actions"]),
        "organization_workflow_permissions": (f"orgs/{org}/actions/permissions/workflow", "PUT", config["organization_workflow_permissions"]),
    }
    observations = {name: request(endpoint) for name, (endpoint, _, _) in resources.items()}
    writes = plan(config, identity["value"], observations)
    # Actions must enter selected mode before its selected-actions settings can be applied.
    order = ["organization_settings", "organization_actions", "organization_selected_actions", "organization_workflow_permissions"]
    events = []
    for name in order:
        item = next((w for w in writes if w["resource"] == name), None)
        if not item:
            events.append({"resource": name, "result": "already-matching"})
            continue
        endpoint, method, _ = resources[name]
        # PUT endpoints require their full request object even when only one field drifted.
        payload = resources[name][2] if method == "PUT" else item["fields"]
        response = request(endpoint, method, payload)
        events.append({"resource": name, "result": "written" if response.get("ok") else "failed",
                       "status": response.get("status"), "message": response.get("message")})
        if not response.get("ok"):
            break
    final = {name: request(endpoint) for name, (endpoint, _, _) in resources.items()}
    comparisons = {}
    for name, (_, _, desired) in resources.items():
        value = final[name].get("value", {}) if final[name].get("ok") else {}
        comparisons[name] = {key: value.get(key) == expected for key, expected in desired.items()}
    manual_only = {key: {"expected": expected, "observed": final["organization_settings"].get("value", {}).get(key)}
                   for key, expected in config["organization_settings"].items()
                   if key not in ORG_API_WRITABLE_FIELDS and
                   final["organization_settings"].get("value", {}).get(key) != expected}
    team_events = []
    repository_inventory = request(f"orgs/{org}/repos?per_page=100")
    if not repository_inventory.get("ok"):
        raise RuntimeError("Cannot establish repository inventory for team grants")
    repository_names = {repo["name"] for repo in repository_inventory["value"]}
    for team_spec in config.get("teams", []):
        slug = team_spec["slug"]
        team_endpoint = f"orgs/{org}/teams/{slug}"
        team_result = request(team_endpoint)
        if not team_result.get("ok"):
            team_result = request(f"orgs/{org}/teams", "POST", {
                "name": team_spec["name"], "description": "Repository maintainers for Samwise-OS",
                "privacy": team_spec["privacy"]})
            if not team_result.get("ok"):
                raise RuntimeError(f"Cannot ensure team {slug}: {team_result}")
            team_events.append({"team": slug, "result": "created"})
        else:
            team_events.append({"team": slug, "result": "already-present"})
        for username in team_spec["maintainers"]:
            membership_endpoint = f"orgs/{org}/teams/{slug}/memberships/{username}"
            membership = request(membership_endpoint)
            if membership.get("ok") and membership.get("value", {}).get("role") == "maintainer":
                team_events.append({"membership": f"{slug}/{username}", "result": "already-matching"})
                continue
            membership = request(membership_endpoint, "PUT", {"role": "maintainer"})
            if not membership.get("ok"):
                raise RuntimeError(f"Cannot ensure maintainer {username} in {slug}: {membership}")
            team_events.append({"membership": f"{slug}/{username}", "result": "written"})
        team_repositories = request(f"orgs/{org}/teams/{slug}/repos?per_page=100")
        if not team_repositories.get("ok"):
            raise RuntimeError(f"Cannot read team repository grants for {slug}")
        grants = {repo["name"]: repo
                  for repo in team_repositories["value"]}
        for repository, permission in resolved_team_grants[slug].items():
            if repository not in repository_names:
                team_events.append({"repository": repository, "team": slug, "result": "deferred-not-created"})
                continue
            if observed_team_permission(grants.get(repository, {})) == permission:
                team_events.append({"repository": repository, "team": slug, "result": "already-matching"})
                continue
            grant_endpoint = f"orgs/{org}/teams/{slug}/repos/{org}/{repository}"
            grant = request(grant_endpoint, "PUT", {"permission": permission})
            if not grant.get("ok"):
                raise RuntimeError(f"Cannot grant {permission} to {slug} on {repository}: {grant}")
            readback = request(f"orgs/{org}/teams/{slug}/repos?per_page=100")
            if not readback.get("ok"):
                raise RuntimeError(f"Cannot verify repository grant for {slug} on {repository}")
            observed = next((item for item in readback["value"]
                             if item.get("name") == repository), {})
            if observed_team_permission(observed) != permission:
                raise RuntimeError(f"Repository grant readback mismatch for {slug} on {repository}: expected {permission}")
            team_events.append({"repository": repository, "team": slug, "result": "written"})
    return {"actor": actor["value"].get("login"), "organization_id": identity["value"]["id"],
            "planned_writes": writes, "events": events, "readback": final,
            "matches": comparisons, "manual_only_drift": manual_only, "team_events": team_events,
            "complete": (all(all(x.values()) for x in comparisons.values())
                         and not any(event.get("result") == "deferred-not-created"
                                     for event in team_events))}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("plan", "apply"))
    args = parser.parse_args()
    config = json.loads((ROOT / "config/organization.json").read_text(encoding="utf-8"))
    if args.command == "plan":
        # Planning is performed by reconcile's semantic reads; this command never writes.
        org = gh(f"orgs/{config['organization']}")
        current = {name: gh(endpoint) for name, endpoint in {
            "organization_settings": f"orgs/{config['organization']}",
            "organization_actions": f"orgs/{config['organization']}/actions/permissions",
            "organization_selected_actions": f"orgs/{config['organization']}/actions/permissions/selected-actions",
            "organization_workflow_permissions": f"orgs/{config['organization']}/actions/permissions/workflow"}.items()}
        print(json.dumps(plan(config, org["value"], current), indent=2))
        return 0
    result = reconcile(config)
    print(json.dumps({k: result[k] for k in ("actor", "organization_id", "planned_writes", "events", "matches", "manual_only_drift", "team_events", "complete")}, indent=2))
    return 0 if result["complete"] else 2


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (ValueError, KeyError, OSError, RuntimeError, subprocess.TimeoutExpired) as error:
        print(f"Organization reconciliation failed: {error}", file=sys.stderr)
        sys.exit(4)
