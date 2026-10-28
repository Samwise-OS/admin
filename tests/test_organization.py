import importlib.util
import pathlib
import unittest

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


if __name__ == "__main__":
    unittest.main()
