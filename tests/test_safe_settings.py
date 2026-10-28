"""Behavior checks for the public bounded Safe-Settings config seam."""

import json
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

    def test_accepts_reviewed_allowlist_and_additive_ruleset_mode(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            self.valid_tree(root)
            safe.validate(root)

    def test_rejects_executable_validator_in_remote_settings(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            self.valid_tree(root)
            settings = json.loads((root / ".github/settings.yml").read_text())
            settings["validators"] = {"repository": "process.exit(0)"}
            (root / ".github/settings.yml").write_text(json.dumps(settings))
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

    def test_rejects_non_additive_ruleset_configuration(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            self.valid_tree(root)
            repos = root / ".github/repos"
            repos.mkdir()
            (repos / "baseline-canary.yml").write_text(json.dumps({
                "rulesets": [{
                    "name": "samwise-default-branch",
                    "target": "branch",
                    "enforcement": "active",
                    "bypass_actors": [],
                }]
            }))
            with self.assertRaisesRegex(ValueError, "remains disabled"):
                safe.validate(root)

    def test_rejects_allowlist_expansion(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            self.valid_tree(root)
            path = root / ".github/deployment-settings.yml"
            path.write_text(json.dumps({
                "restrictedRepos": {"include": ["admin", "github"]}
            }))
            with self.assertRaisesRegex(ValueError, "allowlist must be exactly"):
                safe.validate(root)


if __name__ == "__main__":
    unittest.main()
