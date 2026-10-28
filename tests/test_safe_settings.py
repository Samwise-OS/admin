"""Behavior checks for the public bounded Safe-Settings config seam."""

import json
import os
import pathlib
import tempfile
import unittest

from scripts import validate_safe_settings as safe


class SafeSettingsValidationTests(unittest.TestCase):
    def valid_tree(self, root):
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
            "restrictedRepos": {"include": ["admin", "baseline-canary"]}
        }), encoding="utf-8")
        repos = github / "repos"
        repos.mkdir()
        (repos / "baseline-canary.yml").write_text(json.dumps({
            "rulesets": [safe.expected_ruleset()]
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
