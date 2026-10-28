"""Bounded, idempotent provisioning using official gh REST. No deletion or visibility conversion."""

import argparse
import base64
import hashlib
import json
import pathlib
import re
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
WORKFLOW_PATH = ".github/workflows/repository-baseline.yml"


def api(method, endpoint, body=None, paginate=False):
    command = ["gh", "api", "--hostname", "github.com", "--method", method,
               "-H", "X-GitHub-Api-Version: 2022-11-28", endpoint]
    if paginate:
        command += ["--paginate", "--slurp"]
    if body is not None:
        command += ["--input", "-"]
    result = subprocess.run(command, input=json.dumps(body) if body is not None else None,
                            text=True, capture_output=True, timeout=120)
    if result.returncode:
        raise RuntimeError(f"{method} {endpoint} failed: {result.stdout[:700]}")
    value = json.loads(result.stdout) if result.stdout.strip() else None
    return [item for page in value for item in page] if paginate else value


def metadata_plan(desired, observed):
    if observed is None:
        return {"create": True}
    if observed["visibility"] != desired["visibility"]:
        raise ValueError(f"{desired['name']}: visibility mismatch requires explicit migration")
    if observed.get("archived"):
        raise ValueError(f"{desired['name']}: archived repository requires explicit lifecycle decision")
    return {key: desired[key] for key in ("description", "is_template") if desired[key] != observed.get(key)}


def validate_workflow_source(item):
    if item.get("type") != "file" or item.get("path") != WORKFLOW_PATH:
        raise ValueError(f"Pinned admin revision must contain {WORKFLOW_PATH}")
    try:
        content = base64.b64decode(item["content"], validate=True).decode("utf-8")
    except (KeyError, ValueError, UnicodeDecodeError) as error:
        raise ValueError(f"Pinned {WORKFLOW_PATH} is not readable UTF-8") from error
    if "workflow_call:" not in content:
        raise ValueError(f"Pinned {WORKFLOW_PATH} is not callable as a reusable workflow")


def files_for(repo, workflow_sha):
    files = {}
    for folder in (ROOT / "bootstrap/common", ROOT / "bootstrap" / repo["source"]):
        for path in sorted(folder.rglob("*")):
            if path.is_file():
                name = path.relative_to(folder).as_posix()
                value = path.read_text(encoding="utf-8")
                for token, replacement in (("__REPO__", repo["name"]), ("__ADMIN_SHA__", workflow_sha)):
                    value = value.replace(token, replacement)
                files[name] = value
    for name in (".editorconfig", ".gitattributes"):
        files[name] = (ROOT / name).read_text(encoding="utf-8")
    return files


def validate_repositories(repositories):
    if not isinstance(repositories, list) or not repositories:
        raise ValueError("Manifest must declare at least one repository")
    names = [item.get("name") for item in repositories if isinstance(item, dict)]
    if len(names) != len(repositories) or len(set(names)) != len(names):
        raise ValueError("Manifest contains malformed or duplicate repository entries")
    for desired in repositories:
        name = desired.get("name")
        if name != ".github" and (not isinstance(name, str) or not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", name)):
            raise ValueError(f"Invalid repository name: {name}")
        if desired.get("visibility") != "public" or desired.get("source") not in ("community", "template"):
            raise ValueError(f"{name}: only declared public bootstrap repositories are supported")
        if not isinstance(desired.get("description"), str) or not desired["description"].strip():
            raise ValueError(f"{name}: a description is required")
        if not isinstance(desired.get("is_template"), bool):
            raise ValueError(f"{name}: is_template must be boolean")


def sync_files(full_name, branch, desired, apply):
    reference = api("GET", f"repos/{full_name}/git/ref/heads/{branch}")
    head = reference["object"]["sha"]
    commit = api("GET", f"repos/{full_name}/git/commits/{head}")
    tree = api("GET", f"repos/{full_name}/git/trees/{commit['tree']['sha']}?recursive=1")
    if tree.get("truncated"):
        raise ValueError("Truncated content inventory; refusing partial reconciliation")
    current = {entry["path"]: entry for entry in tree["tree"] if entry["type"] == "blob"}
    changes = []
    for name, content in sorted(desired.items()):
        # Git blob object identity is deterministic; no content download is needed.
        payload = content.encode("utf-8")
        expected = hashlib.sha1(f"blob {len(payload)}\0".encode() + payload).hexdigest()
        if name not in current or current[name]["sha"] != expected:
            changes.append((name, content))
    if not changes or not apply:
        return [name for name, _ in changes]
    entries = []
    for name, content in changes:
        blob = api("POST", f"repos/{full_name}/git/blobs", {"content": content, "encoding": "utf-8"})
        entries.append({"path": name, "mode": "100644", "type": "blob", "sha": blob["sha"]})
    updated = api("POST", f"repos/{full_name}/git/trees", {"base_tree": commit["tree"]["sha"], "tree": entries})
    created = api("POST", f"repos/{full_name}/git/commits", {
        "message": "chore: provision canonical organization standards", "tree": updated["sha"], "parents": [head]
    })
    # A concurrent unrelated update makes this non-fast-forward and fails, preserving it.
    api("PATCH", f"repos/{full_name}/git/refs/heads/{branch}", {"sha": created["sha"], "force": False})
    remaining = sync_files(full_name, branch, desired, False)
    if remaining:
        raise ValueError(f"Content readback mismatch: {remaining}")
    return [name for name, _ in changes]


def run(manifest, workflow_sha, apply=False):
    if manifest["organization"] != "Samwise-OS" or manifest["organization_id"] != 349008063:
        raise ValueError("Manifest exceeds organization boundary")
    if not re.fullmatch(r"[0-9a-f]{40}", workflow_sha):
        raise ValueError("An immutable administration workflow commit is required")
    org = api("GET", "orgs/Samwise-OS")
    if org["id"] != manifest["organization_id"]:
        raise ValueError("Organization identity mismatch")
    membership = api("GET", "user/memberships/orgs/Samwise-OS")
    if membership["role"] != "admin" or membership["state"] != "active":
        raise ValueError("Provisioning requires the authorized active owner")
    api("GET", f"repos/Samwise-OS/admin/commits/{workflow_sha}")
    workflow_source = api("GET", f"repos/Samwise-OS/admin/contents/{WORKFLOW_PATH}?ref={workflow_sha}")
    validate_workflow_source(workflow_source)
    validate_repositories(manifest.get("repositories"))
    inventory = api("GET", "orgs/Samwise-OS/repos?type=all&per_page=100", paginate=True)
    existing = {repo["name"]: repo for repo in inventory}
    results = []
    for desired in manifest["repositories"]:
        name = desired["name"]
        full_name = f"Samwise-OS/{name}"
        observed = api("GET", f"repos/{full_name}") if name in existing else None
        change = metadata_plan(desired, observed)
        created = bool(change.get("create"))
        if created and apply:
            if name == "baseline-canary":
                observed = api("POST", "repos/Samwise-OS/repository-template/generate", {
                    "owner": "Samwise-OS", "name": name, "description": desired["description"], "private": False
                })
            else:
                observed = api("POST", "orgs/Samwise-OS/repos", {
                    "name": name, "description": desired["description"], "private": False,
                    "auto_init": True, "is_template": desired["is_template"]
                })
            change = metadata_plan(desired, observed)
        if not created and change and apply:
            api("PATCH", f"repos/{full_name}", change)
        if observed is None:
            results.append({"repository": full_name, "create": True, "content": "after creation"})
            continue
        # A template-generated repository can take a moment before refs are available;
        # fail visibly and rerun safely rather than blindly creating it again.
        branch = observed["default_branch"]
        if branch != "main":
            raise ValueError(f"{full_name}: unexpected default branch {branch}")
        changes = sync_files(full_name, branch, files_for(desired, workflow_sha), apply)
        results.append({"repository": full_name, "id": observed["id"], "create": created,
                        "metadata_changes": change, "content_changes": changes})
    return results


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workflow-sha", required=True)
    parser.add_argument("--apply", action="store_true")
    arguments = parser.parse_args()
    try:
        manifest = json.loads((ROOT / "config/repositories.json").read_text(encoding="utf-8"))
        print(json.dumps(run(manifest, arguments.workflow_sha, arguments.apply), indent=2))
    except (ValueError, RuntimeError, OSError, subprocess.TimeoutExpired) as error:
        print(str(error), file=sys.stderr)
        sys.exit(1)
