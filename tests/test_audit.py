import importlib.util
import pathlib
import subprocess
import unittest
from unittest.mock import patch

ROOT = pathlib.Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("audit", ROOT / "scripts/audit.py")
audit = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(audit)


class AuditTests(unittest.TestCase):
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
