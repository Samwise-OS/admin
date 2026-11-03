"""Behavioral tests for the deterministic documentation-parity interface."""

import contextlib
import io
import json
import pathlib
import shutil
import tempfile
import unittest
from unittest.mock import patch

from scripts import docs_sync


ROOT = pathlib.Path(__file__).resolve().parents[1]


class DocumentationParityTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = pathlib.Path(self.temporary.name)
        for name in docs_sync.SOURCES + ("README.md",):
            destination = self.root / name
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / name, destination)
        self.document = self.root / docs_sync.OUTPUT
        self.document.parent.mkdir(parents=True, exist_ok=True)
        self.document.write_text(docs_sync.render(self.root), encoding="utf-8")

    def test_source_derived_projection_accepts_exact_content(self):
        self.assertTrue(docs_sync.verify(self.root))
        self.assertEqual(docs_sync.render(self.root), self.document.read_text(encoding="utf-8"))
        self.assertIn("**Declared managed repository count:** 6", docs_sync.render(self.root))
        self.assertIn("not** observed GitHub", docs_sync.render(self.root))

    def test_changed_organization_setting_without_updated_document_is_rejected(self):
        config_path = self.root / "config/organization.json"
        config = json.loads(config_path.read_text(encoding="utf-8"))
        config["organization_settings"]["members_can_create_repositories"] = True
        config_path.write_text(json.dumps(config, indent=2) + "\n", encoding="utf-8")
        self.assertFalse(docs_sync.verify(self.root))
        self.assertIn("true", docs_sync.render(self.root))

    def test_new_managed_repository_without_updated_document_is_rejected(self):
        path = self.root / "config/repositories.json"
        config = json.loads(path.read_text(encoding="utf-8"))
        config["repositories"].append({
            "name": "new-project",
            "id": 123456789,
            "description": "New governed repository",
        })
        path.write_text(json.dumps(config, indent=2) + "\n", encoding="utf-8")
        self.assertFalse(docs_sync.verify(self.root))
        self.assertIn("**Declared managed repository count:** 7", docs_sync.render(self.root))

    def test_cron_transition_without_updated_document_is_rejected(self):
        path = self.root / ".github/workflows/reconcile.yml"
        text = path.read_text(encoding="utf-8")
        self.assertIn("17 6 * * *", text)
        path.write_text(text.replace("17 6 * * *", "31 7 * * *"), encoding="utf-8")
        self.assertFalse(docs_sync.verify(self.root))
        self.assertIn("31 7 * * *", docs_sync.render(self.root))

    def test_missing_generated_document_is_rejected(self):
        self.document.unlink()
        self.assertFalse(docs_sync.verify(self.root))

    def test_missing_readme_reference_is_rejected(self):
        path = self.root / "README.md"
        path.write_text("# Unrelated introduction\n", encoding="utf-8")
        self.assertFalse(docs_sync.verify(self.root))

    def test_divergent_organization_identity_fails_closed(self):
        path = self.root / "config/repositories.json"
        config = json.loads(path.read_text(encoding="utf-8"))
        config["organization_id"] += 1
        path.write_text(json.dumps(config, indent=2) + "\n", encoding="utf-8")
        with self.assertRaises(ValueError):
            docs_sync.render(self.root)

    def test_cli_rejects_stale_document_then_passes_regeneration(self):
        self.document.write_text("stale\n", encoding="utf-8")
        with patch.object(docs_sync, "ROOT", self.root), contextlib.redirect_stdout(io.StringIO()), \
                contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(1, docs_sync.main(["--check"]))
            self.assertEqual(0, docs_sync.main(["--write"]))
            first = self.document.read_bytes()
            self.assertEqual(0, docs_sync.main(["--write"]))
            self.assertEqual(first, self.document.read_bytes())
            self.assertEqual(0, docs_sync.main(["--check"]))

    def test_repository_version_is_generated_and_current(self):
        self.assertTrue(docs_sync.verify(ROOT))


if __name__ == "__main__":
    unittest.main()
