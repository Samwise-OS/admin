import importlib.util
import json
import pathlib
import shutil
import subprocess
import tempfile
import unittest
from unittest.mock import patch

ROOT = pathlib.Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("audit", ROOT / "scripts/audit.py")
audit = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(audit)


class AuditTests(unittest.TestCase):
    def managed_fixture(self, mutate=None, denied=None):
        config = audit.load(ROOT / "config/organization.json")
        defaults = audit.load(ROOT / ".github/settings.yml")
        from scripts.validate_safe_settings import managed_repositories
        admin, repositories = managed_repositories(ROOT)
        identity_manifest = audit.load(ROOT / "config/repositories.json")
        ids = {entry["name"]: entry["id"] for entry in identity_manifest["repositories"]}
        ids[admin] = config["admin_repository_id"]
        expected = {
            name: audit.load(ROOT / ".github/repos" / f"{name}.yml")["rulesets"][0]
            for name in repositories
        }
        denied = denied or set()

        def fetch(endpoint, **kwargs):
            if endpoint in denied:
                return {"state": "unknown", "http_status": "403"}
            if endpoint == "orgs/Samwise-OS":
                return {"state": "observed", "value": {"id": config["organization_id"]}}
            for name in repositories:
                if endpoint == f"repos/Samwise-OS/{name}":
                    return {"state": "observed", "value": {
                        **defaults["repository"], "id": ids[name],
                        "full_name": f"Samwise-OS/{name}",
                        "owner": {"login": "Samwise-OS", "id": config["organization_id"]},
                    }}
                if endpoint == f"repos/Samwise-OS/{name}/rulesets?per_page=100":
                    return {"state": "observed", "value": [
                        {"id": 500 + index, "name": expected[name]["name"]}
                        for index, candidate in enumerate(repositories) if candidate == name
                    ] + [{"id": 900, "name": "unmanaged-extra"}]}
                if endpoint.startswith(f"repos/Samwise-OS/{name}/rulesets/"):
                    detail = dict(expected[name])
                    detail.update({"id": 500 + repositories.index(name),
                                   "source": f"Samwise-OS/{name}"})
                    if mutate:
                        mutate(name, detail)
                    return {"state": "observed", "value": detail}
            self.fail(f"Unexpected audit endpoint: {endpoint}")

        return config, defaults, fetch

    def test_managed_audit_compares_repository_defaults_and_exact_named_ruleset(self):
        config, defaults, fetch = self.managed_fixture()
        result = audit.audit_managed_repositories(config, defaults, fetch)
        self.assertEqual("match", result["comparison_state"])
        self.assertEqual("declared-managed-repositories", result["scope"])
        self.assertTrue(all(item["state"] == "match"
                            for item in result["comparisons"].values()))

    def test_managed_audit_detects_missing_rule_and_check_app_mismatch(self):
        def mismatch_check_app(name, detail):
            check = detail["rules"][-1]["parameters"]["required_status_checks"][0]
            check["integration_id"] = 999

        config, defaults, fetch = self.managed_fixture(mutate=mismatch_check_app)
        result = audit.audit_managed_repositories(config, defaults, fetch)
        differences = result["comparisons"]["repository:admin:managed_ruleset"]["differences"]
        self.assertIn("rules[4].parameters.required_status_checks[0].integration_id", differences)

        def missing_rule(name, detail):
            detail["rules"].pop(0)

        config, defaults, fetch = self.managed_fixture(mutate=missing_rule)
        result = audit.audit_managed_repositories(config, defaults, fetch)
        self.assertEqual("drift", result["comparison_state"])
        differences = result["comparisons"]["repository:admin:managed_ruleset"]["differences"]
        self.assertIn("rules", differences)

    def test_managed_audit_detects_inactive_ruleset_and_preserves_unrelated_rulesets(self):
        def mutate(_name, detail):
            detail["enforcement"] = "disabled"

        config, defaults, fetch = self.managed_fixture(mutate=mutate)
        result = audit.audit_managed_repositories(config, defaults, fetch)
        self.assertEqual("drift", result["comparisons"][
            "repository:baseline-canary:managed_ruleset"]["state"])
        self.assertNotIn("unmanaged-extra", str(result["comparisons"]))

    def test_managed_audit_unknown_on_denied_ruleset_details(self):
        config, defaults, fetch = self.managed_fixture(
            denied={"repos/Samwise-OS/admin/rulesets/501"})
        result = audit.audit_managed_repositories(config, defaults, fetch)
        self.assertEqual("incomplete", result["comparison_state"])
        self.assertEqual("unknown", result["comparisons"][
            "repository:admin:managed_ruleset"]["state"])

    def test_managed_audit_treats_hidden_repository_settings_as_unknown(self):
        config, defaults, fetch = self.managed_fixture()

        def missing_setting(endpoint, **kwargs):
            result = fetch(endpoint, **kwargs)
            if endpoint == "repos/Samwise-OS/admin":
                result["value"].pop("allow_merge_commit")
            return result

        result = audit.audit_managed_repositories(config, defaults, missing_setting)
        comparison = result["comparisons"]["repository:admin:settings"]
        self.assertEqual("unknown", comparison["state"])
        self.assertEqual(["allow_merge_commit"], comparison["missing_fields"])
        receipt = audit.sanitized_managed_comparisons(result["comparisons"])
        row = next(item for item in receipt
                   if item["name"] == "admin" and item["control"] == "settings")
        self.assertEqual("required-fields-not-visible", row["reason"])
        self.assertEqual(["allow_merge_commit"], row["missing_fields"])

    def test_managed_audit_treats_hidden_ruleset_bypass_as_unknown(self):
        config, defaults, fetch = self.managed_fixture()

        def missing_bypass(endpoint, **kwargs):
            result = fetch(endpoint, **kwargs)
            if endpoint.startswith("repos/Samwise-OS/admin/rulesets/"):
                result["value"].pop("bypass_actors")
            return result

        result = audit.audit_managed_repositories(config, defaults, missing_bypass)
        comparison = result["comparisons"]["repository:admin:managed_ruleset"]
        self.assertEqual("unknown", comparison["state"])
        self.assertEqual(["bypass_actors"], result["observations"][
            "repository:admin:managed_ruleset"]["missing_fields"])
        receipt = audit.sanitized_managed_comparisons(result["comparisons"])
        row = next(item for item in receipt
                   if item["name"] == "admin" and item["control"] == "managed_ruleset")
        self.assertEqual(["bypass_actors"], row["missing_fields"])

    def test_managed_audit_treats_malformed_ruleset_details_as_unknown(self):
        config, defaults, fetch = self.managed_fixture()

        def malformed(endpoint, **kwargs):
            result = fetch(endpoint, **kwargs)
            if endpoint.startswith("repos/Samwise-OS/admin/rulesets/"):
                return {"state": "observed", "value": []}
            return result

        result = audit.audit_managed_repositories(config, defaults, malformed)
        self.assertEqual("unknown", result["comparisons"][
            "repository:admin:managed_ruleset"]["state"])

    def test_managed_audit_stops_before_rulesets_when_repository_identity_differs(self):
        config, defaults, fetch = self.managed_fixture()
        calls = []

        def wrong_identity(endpoint, **kwargs):
            calls.append(endpoint)
            result = fetch(endpoint, **kwargs)
            if endpoint == "repos/Samwise-OS/admin":
                result["value"]["id"] = 1
            return result

        result = audit.audit_managed_repositories(config, defaults, wrong_identity)
        self.assertEqual("drift", result["comparisons"]["repository:admin:identity"]["state"])
        self.assertNotIn("repos/Samwise-OS/admin/rulesets?per_page=100", calls)

    def test_managed_audit_reports_unknown_for_manifest_without_id(self):
        config, defaults, fetch = self.managed_fixture()
        calls = []

        def observed(endpoint, **kwargs):
            calls.append(endpoint)
            return fetch(endpoint, **kwargs)

        with tempfile.TemporaryDirectory() as temporary:
            root = pathlib.Path(temporary)
            (root / "config").mkdir()
            (root / ".github/repos").mkdir(parents=True)
            shutil.copy(ROOT / "config/organization.json", root / "config/organization.json")
            manifest = audit.load(ROOT / "config/repositories.json")
            manifest["repositories"][0].pop("id")
            (root / "config/repositories.json").write_text(
                json.dumps(manifest), encoding="utf-8")
            for path in (ROOT / ".github/repos").glob("*.yml"):
                shutil.copy(path, root / ".github/repos" / path.name)
            result = audit.audit_managed_repositories(config, defaults, observed, root=root)

        self.assertEqual("incomplete", result["comparison_state"])
        self.assertEqual("unknown", result["comparisons"]["repository:.github:identity"]["state"])
        self.assertNotIn("repos/Samwise-OS/.github/rulesets?per_page=100", calls)

    def test_managed_receipt_contains_paths_without_observed_values(self):
        receipt = audit.sanitized_managed_comparisons({
            "repository:admin:settings": {
                "state": "drift",
                "differences": [{"field": "has_wiki", "expected": False,
                                 "observed": True, "missing": False}],
            },
        })
        self.assertEqual(["has_wiki"], receipt[0]["difference_paths"])
        self.assertNotIn("expected", str(receipt))
        self.assertNotIn("observed", str(receipt))

    def test_denied_read_is_unknown_not_compliant_or_absent(self):
        response = subprocess.CompletedProcess([], 1, '{"status":"403","message":"Denied"}', "")
        with patch.object(audit.subprocess, "run", return_value=response):
            observed = audit.get("orgs/Samwise-OS/actions/permissions")
        self.assertEqual("unknown", observed["state"])
        self.assertEqual("unknown", audit.compare(observed, {"enabled": True})["state"])

    def test_every_page_is_flattened_and_command_is_explicit_get(self):
        response = subprocess.CompletedProcess([], 0, '[[{"name":"a"}],[{"name":"b"}]]', "")
        with patch.object(audit.subprocess, "run", return_value=response) as run:
            observed = audit.get("orgs/Samwise-OS/repos?per_page=100", paginated=True)
        self.assertEqual(["a", "b"], [repo["name"] for repo in observed["value"]])
        command = run.call_args.args[0]
        self.assertEqual("GET", command[command.index("--method") + 1])
        self.assertIn("--paginate", command)

    def test_paginated_denial_stays_unknown(self):
        response = subprocess.CompletedProcess([], 1, '[{"status":"404","message":"Not Found"}]', "")
        with patch.object(audit.subprocess, "run", return_value=response):
            observed = audit.get("orgs/Samwise-OS/rulesets?per_page=100", paginated=True)
        self.assertEqual("unknown", observed["state"])
        self.assertEqual("404", observed["http_status"])

    def test_missing_null_and_false_are_different(self):
        result = audit.compare({"state": "observed", "value": {"a": False}}, {"a": False, "b": None})
        self.assertEqual("drift", result["state"])
        self.assertTrue(result["differences"][0]["missing"])

    def test_unmanaged_fields_do_not_create_false_drift(self):
        result = audit.compare({"state": "observed", "value": {"id": 1, "has_wiki": False}}, {"has_wiki": False})
        self.assertEqual("match", result["state"])

    def test_identity_mismatch_stops_before_further_reads(self):
        calls = []

        def fetch(endpoint, **kwargs):
            calls.append(endpoint)
            return {"state": "observed", "value": {"id": 999}}

        config = audit.load(ROOT / "config/organization.json")
        with self.assertRaisesRegex(ValueError, "identity"):
            audit.audit(config, {}, fetch)
        self.assertEqual(["user", "orgs/Samwise-OS"], calls)

    def test_configuration_cannot_target_another_organization(self):
        config = audit.load(ROOT / "config/organization.json")
        config["organization_id"] = 1
        with self.assertRaisesRegex(ValueError, "identity"):
            audit.validate(config, audit.load(ROOT / ".github/settings.yml"),
                           audit.load(ROOT / "config/default-branch.ruleset.json"))

    def test_unauthorized_ruleset_activation_rejected(self):
        ruleset = audit.load(ROOT / "config/default-branch.ruleset.json")
        ruleset["enforcement"] = "active"
        with self.assertRaisesRegex(ValueError, "disabled"):
            audit.validate(audit.load(ROOT / "config/organization.json"),
                           audit.load(ROOT / ".github/settings.yml"), ruleset)


if __name__ == "__main__":
    unittest.main()
