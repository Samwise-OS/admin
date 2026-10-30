import importlib.util
import json
import pathlib
import subprocess
import tempfile
import unittest
from unittest.mock import patch

ROOT = pathlib.Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("organization", ROOT / "scripts/organization.py")
organization = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(organization)


class OrganizationPolicyTests(unittest.TestCase):
    def setUp(self):
        self.config = {"organization": "Samwise-OS", "organization_id": 349008063,
                       "organization_settings": {"default_repository_permission": "none"},
                       "organization_actions": {"allowed_actions": "selected", "sha_pinning_required": True},
                       "organization_selected_actions": {"github_owned_allowed": True, "verified_allowed": False, "patterns_allowed": []},
                       "organization_workflow_permissions": {"default_workflow_permissions": "read", "can_approve_pull_request_reviews": False}}

    def test_plan_includes_only_semantic_drift(self):
        current = {key: {"ok": True, "value": dict(value)} for key, value in {
            "organization_actions": {"allowed_actions": "all", "sha_pinning_required": False},
            "organization_selected_actions": {},
            "organization_workflow_permissions": self.config["organization_workflow_permissions"]}.items()}
        current["organization_selected_actions"] = {"ok": False, "status": 409}
        current["organization_settings"] = {"ok": True, "value": {"default_repository_permission": "read"}}
        result = organization.plan(self.config, {"id": 349008063}, current)
        self.assertEqual(["organization_settings", "organization_actions", "organization_selected_actions"],
                         [item["resource"] for item in result])
        self.assertEqual({"default_repository_permission": "none"}, result[0]["fields"])

    def test_wrong_identity_fails_before_actor_or_policy_reads(self):
        calls = []
        def request(endpoint, method="GET", payload=None):
            calls.append(endpoint)
            return {"ok": True, "value": {"id": 2}}
        with self.assertRaisesRegex(RuntimeError, "identity"):
            organization.reconcile(self.config, request)
        self.assertEqual(["orgs/Samwise-OS"], calls)

    def test_non_owner_actor_fails_before_writes(self):
        calls = []
        def request(endpoint, method="GET", payload=None):
            calls.append((endpoint, method))
            values = {"orgs/Samwise-OS": {"id": 349008063}, "user": {"login": "someone"},
                      "user/memberships/orgs/Samwise-OS": {"role": "admin"}}
            return {"ok": True, "value": values[endpoint]}
        with self.assertRaisesRegex(RuntimeError, "owner"):
            organization.reconcile(self.config, request)
        self.assertEqual(3, len(calls))
        self.assertTrue(all(method == "GET" for _, method in calls))

    def test_unavailable_org_fields_never_create_repeat_writes(self):
        current = {"organization_settings": {"ok": True, "value": {
            "default_repository_permission": "none",
            "members_can_delete_repositories": True, "members_can_change_repo_visibility": True}},
            "organization_actions": {"ok": True, "value": self.config["organization_actions"]},
            "organization_selected_actions": {"ok": True, "value": self.config["organization_selected_actions"]},
            "organization_workflow_permissions": {"ok": True, "value": self.config["organization_workflow_permissions"]}}
        self.assertEqual([], organization.plan(self.config, {"id": 349008063}, current))

    def test_gh_flattens_all_pages_for_get_list_endpoints(self):
        response = subprocess.CompletedProcess(
            [], 0, json.dumps([[{"name": "first"}], [{"name": "second"}]]), "")
        with patch.object(organization.subprocess, "run", return_value=response) as run:
            result = organization.gh("orgs/Samwise-OS/repos?per_page=100")
        self.assertTrue(result["ok"])
        self.assertEqual([{"name": "first"}, {"name": "second"}], result["value"])
        command = run.call_args.args[0]
        self.assertIn("--paginate", command)
        self.assertIn("--slurp", command)
        self.assertEqual("GET", command[command.index("--method") + 1])

    def test_gh_keeps_denied_and_malformed_paginated_reads_not_ok(self):
        denied = subprocess.CompletedProcess(
            [], 1, '{"status":"403","message":"Resource not accessible"}', "")
        malformed = subprocess.CompletedProcess(
            [], 0, '[[{"name":"first"}],{"name":"malformed page"}]', "")
        with patch.object(organization.subprocess, "run", side_effect=[denied, malformed]):
            denied_result = organization.gh("orgs/Samwise-OS/teams?per_page=100")
            malformed_result = organization.gh("orgs/Samwise-OS/repos?per_page=100")
        self.assertFalse(denied_result["ok"])
        self.assertEqual("403", denied_result["status"])
        self.assertFalse(malformed_result["ok"])
        self.assertIn("Unexpected paginated response shape", malformed_result["message"])

    def test_gh_never_paginates_a_mutating_request(self):
        response = subprocess.CompletedProcess([], 0, '{"id":123}', "")
        with patch.object(organization.subprocess, "run", return_value=response) as run:
            result = organization.gh("orgs/Samwise-OS/repos?per_page=100", "POST", {"name": "sample"})
        self.assertTrue(result["ok"])
        self.assertNotIn("--paginate", run.call_args.args[0])
        self.assertNotIn("--slurp", run.call_args.args[0])

    def write_manifests(self, root):
        config_dir = root / "config"
        config_dir.mkdir()
        (config_dir / "organization.json").write_text(json.dumps({
            "organization": "Samwise-OS", "organization_id": 349008063,
            "admin_repository": "admin"}), encoding="utf-8")
        (config_dir / "repositories.json").write_text(json.dumps({
            "organization": "Samwise-OS", "organization_id": 349008063,
            "repositories": [{"name": "future-repo"}]}), encoding="utf-8")

    def team_reconcile_config(self):
        config = dict(self.config)
        config["teams"] = [{"slug": "maintainers", "name": "Maintainers",
                             "privacy": "closed", "maintainers": [],
                             "repository_permission": "maintain"}]
        return config

    def test_scalar_permission_derives_only_manifest_repositories(self):
        with tempfile.TemporaryDirectory() as directory:
            root = pathlib.Path(directory)
            self.write_manifests(root)
            with patch.object(organization, "ROOT", root):
                grants = organization.team_repository_grants(self.team_reconcile_config())
        self.assertEqual({"admin": "maintain", "future-repo": "maintain"},
                         grants["maintainers"])

    def test_missing_declared_repo_is_deferred_and_incomplete(self):
        with tempfile.TemporaryDirectory() as directory:
            root = pathlib.Path(directory)
            self.write_manifests(root)
            config = self.team_reconcile_config()
            team_repo_roles = {"admin": "admin"}
            grants_written = []
            def request(endpoint, method="GET", payload=None):
                values = {
                    "orgs/Samwise-OS": {"id": 349008063},
                    "user": {"login": "samwise-x"},
                    "user/memberships/orgs/Samwise-OS": {"role": "admin"},
                    "orgs/Samwise-OS/actions/permissions": config["organization_actions"],
                    "orgs/Samwise-OS/actions/permissions/selected-actions": config["organization_selected_actions"],
                    "orgs/Samwise-OS/actions/permissions/workflow": config["organization_workflow_permissions"],
                    "orgs/Samwise-OS/teams/maintainers": {"slug": "maintainers"},
                }
                if endpoint == "orgs/Samwise-OS/repos?per_page=100":
                    return {"ok": True, "value": [{"name": "admin"}]}
                if endpoint == "orgs/Samwise-OS/teams/maintainers/repos?per_page=100":
                    return {"ok": True, "value": [
                        {"name": name, "role_name": role}
                        for name, role in team_repo_roles.items()]}
                if endpoint.endswith("/memberships"):
                    return {"ok": True, "value": {"role": "maintainer"}}
                if method == "PUT" and "/teams/maintainers/repos/" in endpoint:
                    repository = endpoint.rsplit("/", 1)[-1]
                    grants_written.append((repository, payload["permission"]))
                    team_repo_roles[repository] = payload["permission"]
                    return {"ok": True, "value": {}}
                value = values.get(endpoint)
                return {"ok": value is not None, "value": value or {}}
            with patch.object(organization, "ROOT", root):
                result = organization.reconcile(config, request)
        deferred = [event for event in result["team_events"]
                    if event.get("repository") == "future-repo"]
        self.assertEqual([{"repository": "future-repo", "team": "maintainers",
                           "result": "deferred-not-created"}], deferred)
        self.assertFalse(result["complete"])
        self.assertEqual([("admin", "maintain")], grants_written)

    def test_permission_fallback_treats_overprivilege_as_strongest_role(self):
        self.assertEqual("admin", organization.observed_team_permission({
            "role_name": "admin", "permissions": {"maintain": True, "push": True, "admin": True}}))
        self.assertEqual("admin", organization.observed_team_permission({
            "permissions": {"maintain": True, "push": True, "admin": True}}))

    def test_grant_readback_mismatch_fails(self):
        with tempfile.TemporaryDirectory() as directory:
            root = pathlib.Path(directory)
            self.write_manifests(root)
            config = self.team_reconcile_config()
            def request(endpoint, method="GET", payload=None):
                values = {
                    "orgs/Samwise-OS": {"id": 349008063},
                    "user": {"login": "samwise-x"},
                    "user/memberships/orgs/Samwise-OS": {"role": "admin"},
                    "orgs/Samwise-OS/actions/permissions": config["organization_actions"],
                    "orgs/Samwise-OS/actions/permissions/selected-actions": config["organization_selected_actions"],
                    "orgs/Samwise-OS/actions/permissions/workflow": config["organization_workflow_permissions"],
                    "orgs/Samwise-OS/teams/maintainers": {"slug": "maintainers"},
                }
                if endpoint == "orgs/Samwise-OS/repos?per_page=100":
                    return {"ok": True, "value": [{"name": "admin"}]}
                if endpoint == "orgs/Samwise-OS/teams/maintainers/repos?per_page=100":
                    return {"ok": True, "value": [{"name": "admin", "role_name": "push"}]}
                if endpoint.endswith("/memberships"):
                    return {"ok": True, "value": {"role": "maintainer"}}
                if method == "PUT" and "/teams/maintainers/repos/" in endpoint:
                    return {"ok": True, "value": {}}
                value = values.get(endpoint)
                return {"ok": value is not None, "value": value or {}}
            with patch.object(organization, "ROOT", root):
                with self.assertRaisesRegex(RuntimeError, "readback mismatch"):
                    organization.reconcile(config, request)

    def test_conflicting_grant_fields_fail_before_any_request(self):
        config = self.team_reconcile_config()
        config["teams"][0]["repository_grants"] = {"admin": "maintain"}
        calls = []
        def request(*args, **kwargs):
            calls.append((args, kwargs))
            return {"ok": False}
        with self.assertRaisesRegex(ValueError, "both"):
            organization.reconcile(config, request)
        self.assertEqual([], calls)


if __name__ == "__main__":
    unittest.main()
