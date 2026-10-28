"""Idempotent organization policy reconciler using the official gh REST client."""
import argparse
import json
import pathlib
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
API_VERSION = "2022-11-28"
ORG_API_WRITABLE_FIELDS = {
    "default_repository_permission", "members_can_create_repositories",
    "members_can_create_public_repositories", "members_can_create_private_repositories"
}


def gh(endpoint, method="GET", payload=None):
    command = ["gh", "api", "--hostname", "github.com", "--method", method,
               "-H", f"X-GitHub-Api-Version: {API_VERSION}",
               "-H", "Accept: application/vnd.github+json", endpoint]
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
    return {"ok": True, "value": json.loads(result.stdout) if result.stdout.strip() else {}}


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
    return {"actor": actor["value"].get("login"), "organization_id": identity["value"]["id"],
            "planned_writes": writes, "events": events, "readback": final,
            "matches": comparisons, "manual_only_drift": manual_only,
            "complete": all(all(x.values()) for x in comparisons.values())}


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
    print(json.dumps({k: result[k] for k in ("actor", "organization_id", "planned_writes", "events", "matches", "manual_only_drift", "complete")}, indent=2))
    return 0 if result["complete"] else 2


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (ValueError, KeyError, OSError, RuntimeError, subprocess.TimeoutExpired) as error:
        print(f"Organization reconciliation failed: {error}", file=sys.stderr)
        sys.exit(4)
