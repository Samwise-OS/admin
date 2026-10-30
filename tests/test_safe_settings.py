"""Behavior checks for the public bounded Safe-Settings config seam."""

import json
import os
import pathlib
import tempfile
import unittest

from scripts import validate_safe_settings as safe
from scripts import generate_repository_settings as generator


class SafeSettingsValidationTests(unittest.TestCase):
    def valid_tree(self, root):
        (root / "config").mkdir()
        (root / "config/repositories.json").write_text(json.dumps({
            "organization": "Samwise-OS", "organization_id": 349008063,
            "repositories": [{"name": "alpha"}, {"name": "baseline-canary"}],
        }), encoding="utf-8")
        (root / "config/organization.json").write_text(json.dumps({
            "organization": "Samwise-OS", "organization_id": 349008063,
            "admin_repository": "admin",
        }), encoding="utf-8")
        github = root / ".github"
        github.mkdir()
        (github / "settings.yml").write_text(json.dumps({
            "repository": {
                "has_issues": True,
                "has_wiki": False,
                "allow_squash_merge": True,
                "allow_merge_commit": False,
                "allow_rebase_merge": False,
                "delete_branch_on_merge": True,
            },
            "additive_plugins": ["rulesets"],
        }), encoding="utf-8")
        (github / "deployment-settings.yml").write_text(json.dumps({
            "restrictedRepos": {"include": ["admin", "alpha", "baseline-canary"]}
        }), encoding="utf-8")
        repos = github / "repos"
        repos.mkdir()
        for name in ("alpha", "baseline-canary"):
            (repos / f"{name}.yml").write_text(json.dumps({
                "rulesets": [safe.expected_ruleset("baseline / standards")]
            }), encoding="utf-8")
        (root / ".github/repos/admin.yml").write_text(json.dumps({
            "rulesets": [safe.expected_ruleset("governance")]
        }), encoding="utf-8")

    def test_accepts_approved_canary_ruleset_and_live_check_identity(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            self.valid_tree(root)
            safe.validate(root)

    def test_rejects_executable_validator_in_remote_settings(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            self.valid_tree(root)
            settings_path = root / ".github/settings.yml"
            settings = json.loads(settings_path.read_text())
            settings["validators"] = {"repository": "process.exit(0)"}
            settings_path.write_text(json.dumps(settings))
            with self.assertRaisesRegex(ValueError, "only repository and additive_plugins"):
                safe.validate(root)

    def test_rejects_remote_scope_override_and_unknown_deployment_keys(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            self.valid_tree(root)
            path = root / ".github/deployment-settings.yml"
            path.write_text(json.dumps({
                "restrictedRepos": {"include": ["admin", "baseline-canary"]},
                "validators": {"deployment": "arbitrary code"},
            }))
            with self.assertRaisesRegex(ValueError, "only restrictedRepos"):
                safe.validate(root)

    def test_rejects_wrong_check_context_or_app_id(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            self.valid_tree(root)
            path = root / ".github/repos/baseline-canary.yml"
            config = json.loads(path.read_text())
            check = config["rulesets"][0]["rules"][-1]["parameters"]["required_status_checks"][0]
            check["context"] = "governance"
            path.write_text(json.dumps(config))
            with self.assertRaisesRegex(ValueError, "exact reviewed payload"):
                safe.validate(root)

    def test_rejects_wrong_check_app_id(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            self.valid_tree(root)
            path = root / ".github/repos/alpha.yml"
            config = json.loads(path.read_text())
            check = config["rulesets"][0]["rules"][-1]["parameters"]["required_status_checks"][0]
            check["integration_id"] = 7
            path.write_text(json.dumps(config), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "exact reviewed payload"):
                safe.validate(root)

    def test_rejects_missing_managed_ruleset_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            self.valid_tree(root)
            (root / ".github/repos/alpha.yml").unlink()
            with self.assertRaisesRegex(ValueError, "in-root JSON-syntax YAML"):
                safe.validate(root)

    def test_rejects_wrong_authority_organization_or_id(self):
        for field, value in (("organization", "Other-Org"), ("organization_id", 1)):
            with self.subTest(field=field), tempfile.TemporaryDirectory() as tmp:
                root = pathlib.Path(tmp)
                self.valid_tree(root)
                path = root / "config/repositories.json"
                manifest = json.loads(path.read_text())
                manifest[field] = value
                path.write_text(json.dumps(manifest), encoding="utf-8")
                with self.assertRaisesRegex(ValueError, "authorized Samwise-OS organization"):
                    safe.validate(root)

    def test_rejects_symlinked_authority_manifest(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            self.valid_tree(root)
            path = root / "config/organization.json"
            target = root / "outside.json"
            target.write_text(path.read_text(), encoding="utf-8")
            path.unlink()
            try:
                os.symlink(target, path)
            except (OSError, NotImplementedError):
                self.skipTest("host does not permit creating file symlinks")
            with self.assertRaisesRegex(ValueError, "symlinked configuration is forbidden"):
                safe.validate(root)

    def test_rejects_symlinked_authority_directory(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            self.valid_tree(root)
            config = root / "config"
            target = root / "config-target"
            config.rename(target)
            try:
                config.symlink_to(target, target_is_directory=True)
            except (OSError, NotImplementedError):
                self.skipTest("host does not permit creating directory symlinks")
            with self.assertRaisesRegex(ValueError, "config must be a real directory"):
                safe.validate(root)

    def test_generator_writes_exact_sorted_scope_and_rulesets_idempotently(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            (root / "config").mkdir()
            (root / "config/repositories.json").write_text(json.dumps({
                "organization": "Samwise-OS", "organization_id": 349008063,
                "repositories": [{"name": "zeta"}, {"name": "alpha"}],
            }), encoding="utf-8")
            (root / "config/organization.json").write_text(json.dumps({
                "organization": "Samwise-OS", "organization_id": 349008063,
                "admin_repository": "admin",
            }), encoding="utf-8")
            generator.generate(root)
            first = {path.relative_to(root).as_posix(): path.read_bytes()
                     for path in (root / ".github").rglob("*.yml")}
            generator.generate(root)
            second = {path.relative_to(root).as_posix(): path.read_bytes()
                      for path in (root / ".github").rglob("*.yml")}
            self.assertEqual(first, second)
            self.assertEqual(json.loads((root / ".github/deployment-settings.yml").read_text()), {
                "restrictedRepos": {"include": ["admin", "alpha", "zeta"]}
            })
            self.assertEqual(json.loads((root / ".github/repos/admin.yml").read_text())[
                "rulesets"][0]["rules"][-1]["parameters"]["required_status_checks"][
                    0]["context"], "governance")
            self.assertEqual(json.loads((root / ".github/repos/alpha.yml").read_text())[
                "rulesets"][0]["rules"][-1]["parameters"]["required_status_checks"][
                    0]["context"], "baseline / standards")

    def test_generator_check_detects_drift_and_refuses_unknown_repo_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            self.valid_tree(root)
            path = root / ".github/repos/alpha.yml"
            path.write_text("{}", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "drift"):
                generator.generate(root, check=True)
            (root / ".github/repos/unknown.yml").write_text("{}", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "outside the generated repository set"):
                generator.generate(root)

    def test_rejects_yaml_alias_and_unknown_repo_config_path(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            self.valid_tree(root)
            (root / ".github/repos/baseline-canary.yaml").write_text("{}");
            with self.assertRaisesRegex(ValueError, "outside the approved set"):
                safe.validate(root)

    def test_rejects_symlinked_ruleset_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            self.valid_tree(root)
            repo_dir = root / ".github/repos"
            config = repo_dir / "baseline-canary.yml"
            target = root / "outside.yml"
            target.write_text(config.read_text())
            config.unlink()
            try:
                os.symlink(target, config)
            except (OSError, NotImplementedError):
                self.skipTest("host does not permit creating file symlinks")
            with self.assertRaisesRegex(ValueError, "symlink"):
                safe.validate(root)


if __name__ == "__main__":
    unittest.main()
