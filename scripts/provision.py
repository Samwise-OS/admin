"""Bounded, idempotent provisioning using official gh REST. No deletion or visibility conversion."""

import argparse
import base64
import hashlib
import json
import pathlib
import re
import subprocess
import sys
import urllib.parse

ROOT = pathlib.Path(__file__).resolve().parents[1]
WORKFLOW_PATH = ".github/workflows/repository-baseline.yml"
LABELS_PATH = ROOT / "config/labels.json"


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
        encoded = re.sub(r"\s+", "", item["content"])
        content = base64.b64decode(encoded, validate=True).decode("utf-8")
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
        if name == "admin":
            raise ValueError("admin is the reserved controller repository and cannot be provisioned as bootstrap content")
        if name != ".github" and (not isinstance(name, str) or not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", name)):
            raise ValueError(f"Invalid repository name: {name}")
        if desired.get("visibility") != "public" or desired.get("source") not in ("community", "template"):
            raise ValueError(f"{name}: only declared public bootstrap repositories are supported")
        if not isinstance(desired.get("description"), str) or not desired["description"].strip():
            raise ValueError(f"{name}: a description is required")
        if not isinstance(desired.get("is_template"), bool):
            raise ValueError(f"{name}: is_template must be boolean")
        repository_id = desired.get("id")
        if repository_id is not None and (not isinstance(repository_id, int) or isinstance(repository_id, bool) or repository_id <= 0):
            raise ValueError(f"{name}: id must be a positive repository ID")


def validate_labels(labels):
    if not isinstance(labels, list) or not labels:
        raise ValueError("Label manifest must declare at least one label")
    names = [label.get("name") for label in labels if isinstance(label, dict)]
    if len(names) != len(labels) or len(names) != len(set(names)):
        raise ValueError("Label manifest contains malformed or duplicate entries")
    for label in labels:
        if (not isinstance(label.get("name"), str) or not label["name"].strip()
                or not isinstance(label.get("color"), str) or not re.fullmatch(r"[0-9a-fA-F]{6}", label["color"])
                or not isinstance(label.get("description"), str)):
            raise ValueError(f"Invalid label declaration: {label.get('name')}")


def load_labels():
    labels = json.loads(LABELS_PATH.read_text(encoding="utf-8"))["labels"]
    validate_labels(labels)
    return labels


def sync_labels(full_name, desired_labels, apply):
    endpoint = f"repos/{full_name}/labels?per_page=100"

    def current_labels():
        return {label["name"]: label for label in api("GET", endpoint, paginate=True)}

    observed = current_labels()
    changes = []
    for desired in desired_labels:
        current = observed.get(desired["name"])
        if current is None:
            changes.append({"name": desired["name"], "action": "create"})
        elif (current.get("color", "").lower() != desired["color"].lower()
              or current.get("description", "") != desired["description"]):
            changes.append({"name": desired["name"], "action": "update"})
    if apply:
        for change in changes:
            desired = next(item for item in desired_labels if item["name"] == change["name"])
            if change["action"] == "create":
                api("POST", f"repos/{full_name}/labels", desired)
            else:
                label = urllib.parse.quote(change["name"], safe="")
                api("PATCH", f"repos/{full_name}/labels/{label}", {
                    "color": desired["color"], "description": desired["description"]
                })
        if changes:
            observed = current_labels()
            mismatches = [item["name"] for item in desired_labels
                          if (observed.get(item["name"], {}).get("color", "").lower() != item["color"].lower()
                              or observed.get(item["name"], {}).get("description") != item["description"])]
            if mismatches:
                raise ValueError(f"Label readback mismatch for {full_name}: {mismatches}")
    return {"label_changes": changes,
            "label_state": "changes_needed" if changes and not apply else "converged"}


def sync_private_vulnerability_reporting(full_name, repository, apply):
    if repository.get("visibility") != "public":
        raise ValueError(f"Private vulnerability reporting is scoped to declared public repositories: {full_name}")
    endpoint = f"repos/{full_name}/private-vulnerability-reporting"

    def read_status():
        status = api("GET", endpoint)
        if not isinstance(status, dict) or not isinstance(status.get("enabled"), bool):
            raise ValueError(f"Private vulnerability reporting status unavailable for {full_name}")
        return status["enabled"]

    before = read_status()
    changed = False
    after = before
    if not before and apply:
        api("PUT", endpoint)
        after = read_status()
        if not after:
            raise ValueError(f"Private vulnerability reporting readback failed for {full_name}")
        changed = True
    return {"enabled": after, "changed": changed, "state": "enabled" if after else "changes_needed"}


def validate_existing_identities(repositories, observed):
    for desired in repositories:
        name = desired["name"]
        repository = observed.get(name)
        if repository is None:
            continue
        recorded_id = desired.get("id")
        actual_id = repository.get("id")
        if recorded_id is None:
            raise ValueError(
                f"{name} already exists with repository ID {actual_id}; record its ID in the manifest before adoption"
            )
        if actual_id != recorded_id:
            raise ValueError(
                f"{name}: repository identity mismatch (manifest {recorded_id}, observed {actual_id})"
            )


def blob_sha(content):
    payload = content.encode("utf-8")
    return hashlib.sha1(f"blob {len(payload)}\0".encode() + payload).hexdigest()


def desired_content_hash(desired):
    digest = hashlib.sha256()
    for name, content in sorted(desired.items()):
        digest.update(name.encode("utf-8"))
        digest.update(b"\0")
        digest.update(content.encode("utf-8"))
        digest.update(b"\0")
    return digest.hexdigest()


def read_tree(full_name, commit_sha):
    commit = api("GET", f"repos/{full_name}/git/commits/{commit_sha}")
    tree = api("GET", f"repos/{full_name}/git/trees/{commit['tree']['sha']}?recursive=1")
    if tree.get("truncated"):
        raise ValueError("Truncated content inventory; refusing partial reconciliation")
    # Keep every leaf, including symlinks and gitlinks; these are part of the
    # commit snapshot even though only ordinary blobs can satisfy desired files.
    return commit, {entry["path"]: entry for entry in tree["tree"] if entry["type"] != "tree"}


def changed_files(current, desired):
    changes = []
    for name, content in sorted(desired.items()):
        # Git blob object identity is deterministic; no content download is needed.
        expected = blob_sha(content)
        entry = current.get(name, {})
        if (entry.get("type") != "blob" or entry.get("mode") != "100644"
                or entry.get("sha") != expected):
            changes.append((name, content))

    return changes


def provision_branch_name(base_sha, desired):
    fingerprint = hashlib.sha256(f"{base_sha}\0{desired_content_hash(desired)}".encode()).hexdigest()[:16]
    return f"codex/provision-{fingerprint}"


def pull_request_endpoint(full_name, branch):
    head = urllib.parse.quote(f"Samwise-OS:{branch}", safe="")
    return f"repos/{full_name}/pulls?state=open&head={head}&base=main&per_page=100"


def find_open_pull_request(full_name, branch):
    matches = api("GET", pull_request_endpoint(full_name, branch))
    if len(matches) > 1:
        raise ValueError(f"Multiple open provisioning pull requests found for {branch}; refusing ambiguity")
    return matches[0] if matches else None


def validate_provisioning_branch(full_name, branch, branch_sha, base_sha, desired):
    commit, current = read_tree(full_name, branch_sha)
    if [parent.get("sha") for parent in commit.get("parents", [])] != [base_sha]:
        raise ValueError(
            f"Existing provisioning branch {branch} is not based exactly on {base_sha}; refusing overwrite"
        )
    _, base_tree = read_tree(full_name, base_sha)
    expected = {
        path: (entry.get("mode"), entry.get("type"), entry.get("sha"))
        for path, entry in base_tree.items()
    }
    for path, content in desired.items():
        expected[path] = ("100644", "blob", blob_sha(content))
    actual = {
        path: (entry.get("mode"), entry.get("type"), entry.get("sha"))
        for path, entry in current.items()
    }
    if actual != expected:
        raise ValueError(
            f"Existing provisioning branch {branch} does not match the exact base plus desired tree; refusing reuse"
        )


def content_pull_request(full_name, desired, apply):
    """Create or reuse a proposal branch; never updates main or force-pushes."""
    base_ref = api("GET", f"repos/{full_name}/git/ref/heads/main")
    base_head = base_ref["object"]["sha"]
    base_commit, current = read_tree(full_name, base_head)
    changes = changed_files(current, desired)
    if not changes:
        return {"changes": [], "content_pull_request": None, "content_state": "already_converged"}
    if not apply:
        return {"changes": [name for name, _ in changes], "content_pull_request": None,
                "content_state": "changes_needed"}

    branch = provision_branch_name(base_head, desired)
    existing_pr = find_open_pull_request(full_name, branch)
    branch_sha = None
    if existing_pr:
        if (existing_pr["head"]["ref"] != branch
                or existing_pr["head"]["repo"]["full_name"] != full_name
                or existing_pr["base"]["ref"] != "main"
                or existing_pr["base"]["sha"] != base_head):
            raise ValueError(f"Open provisioning pull request for {branch} has a changed base or head; refusing reuse")
        branch_sha = existing_pr["head"]["sha"]
        validate_provisioning_branch(full_name, branch, branch_sha, base_head, desired)
    else:
        matching = api("GET", f"repos/{full_name}/git/matching-refs/heads/{urllib.parse.quote(branch, safe='/')}")
        exact_ref = next((ref for ref in matching if ref["ref"] == f"refs/heads/{branch}"), None)
        if exact_ref:
            branch_sha = exact_ref["object"]["sha"]
            validate_provisioning_branch(full_name, branch, branch_sha, base_head, desired)
        else:
            entries = []
            for name, value in changes:
                blob = api("POST", f"repos/{full_name}/git/blobs", {"content": value, "encoding": "utf-8"})
                entries.append({"path": name, "mode": "100644", "type": "blob", "sha": blob["sha"]})
            updated = api("POST", f"repos/{full_name}/git/trees", {
                "base_tree": base_commit["tree"]["sha"], "tree": entries
            })
            created = api("POST", f"repos/{full_name}/git/commits", {
                "message": "chore: propose canonical organization standards",
                "tree": updated["sha"], "parents": [base_head]
            })
            # Check the exact snapshot again before publishing a branch. Concurrent main
            # changes are handled on rerun with a different deterministic branch name.
            latest = api("GET", f"repos/{full_name}/git/ref/heads/main")["object"]["sha"]
            if latest != base_head:
                raise ValueError(
                    f"{full_name}/main moved from {base_head} to {latest}; rerun to create a fresh proposal"
                )
            api("POST", f"repos/{full_name}/git/refs", {
                "ref": f"refs/heads/{branch}", "sha": created["sha"]
            })
            branch_sha = created["sha"]
            validate_provisioning_branch(full_name, branch, branch_sha, base_head, desired)

    # Do not open a proposal against a base that moved after its snapshot.
    latest = api("GET", f"repos/{full_name}/git/ref/heads/main")["object"]["sha"]
    if latest != base_head:
        raise ValueError(
            f"{full_name}/main moved from {base_head} to {latest}; rerun to create a fresh proposal"
        )
    if not existing_pr:
        try:
            existing_pr = api("POST", f"repos/{full_name}/pulls", {
                "title": "chore: propose canonical organization standards",
                "head": f"Samwise-OS:{branch}", "base": "main",
                "body": ("This proposal was generated from the declared organization baseline. "
                         f"Its exact base snapshot is `{base_head}`. Review and merge through the repository's "
                         "normal pull request controls.")
            })
        except RuntimeError:
            # A simultaneous rerun may have opened the same PR. Reuse only if it
            # now passes the same exact-base and content checks; otherwise preserve error.
            existing_pr = find_open_pull_request(full_name, branch)
            if not existing_pr:
                raise
            if (existing_pr["head"]["ref"] != branch
                    or existing_pr["head"]["repo"]["full_name"] != full_name
                    or existing_pr["base"]["ref"] != "main"
                    or existing_pr["base"]["sha"] != base_head):
                raise ValueError(f"Concurrent pull request for {branch} has an unexpected base or head")
            branch_sha = existing_pr["head"]["sha"]
            validate_provisioning_branch(full_name, branch, branch_sha, base_head, desired)
    return {
        "changes": [name for name, _ in changes],
        "content_state": "pending_pull_request",
        "content_pull_request": {
            "url": existing_pr["html_url"], "state": existing_pr["state"],
            "number": existing_pr["number"], "head_sha": branch_sha, "base_sha": base_head,
        },
    }


def sync_files(full_name, desired, apply):
    return content_pull_request(full_name, desired, apply)


def run(manifest, workflow_sha, apply=False):
    if manifest["organization"] != "Samwise-OS" or manifest["organization_id"] != 349008063:
        raise ValueError("Manifest exceeds organization boundary")
    if not re.fullmatch(r"[0-9a-f]{40}", workflow_sha):
        raise ValueError("An immutable administration workflow commit is required")
    desired_labels = load_labels()
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
    validate_existing_identities(manifest["repositories"], existing)
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
            results.append({
                "repository": full_name, "create": True, "content": "after creation",
                "label_state": "after_creation", "label_changes": None,
                "private_vulnerability_reporting": {"state": "after_creation"},
            })
            continue
        # A template-generated repository can take a moment before refs are available;
        # fail visibly and rerun safely rather than blindly creating it again.
        branch = observed["default_branch"]
        if branch != "main":
            raise ValueError(f"{full_name}: unexpected default branch {branch}")
        content = sync_files(full_name, files_for(desired, workflow_sha), apply)
        labels = sync_labels(full_name, desired_labels, apply)
        reporting = sync_private_vulnerability_reporting(full_name, desired, apply)
        results.append({"repository": full_name, "id": observed["id"], "create": created,
                        "metadata_changes": change, **content, **labels,
                        "private_vulnerability_reporting": reporting})
        if created and desired.get("id") is None:
            results[-1]["adoption_required"] = "record this repository ID in the manifest before the next reconciliation"
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
