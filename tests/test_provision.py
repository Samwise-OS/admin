import importlib.util
import base64
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("provision", ROOT / "scripts/provision.py")
provision = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(provision)


class ProvisionTests(unittest.TestCase):
    def test_workflow_revision_requires_the_expected_reusable_workflow(self):
        with self.assertRaisesRegex(ValueError, "repository-baseline.yml"):
            provision.validate_workflow_source({"name": "admin"})

    def test_workflow_revision_must_be_reusable(self):
        source = base64.b64encode(b"name: wrong\njobs: {}\n").decode("ascii")
        with self.assertRaisesRegex(ValueError, "not callable"):
            provision.validate_workflow_source({
                "type": "file", "path": provision.WORKFLOW_PATH, "content": source
            })

    def test_existing_wrong_visibility_is_not_silently_converted(self):
        desired = {"name": "baseline-canary", "visibility": "public", "is_template": False, "description": "Canary"}
        observed = {"name": "baseline-canary", "visibility": "private", "is_template": False, "description": "Canary"}
        with self.assertRaisesRegex(ValueError, "visibility"):
            provision.metadata_plan(desired, observed)


if __name__ == "__main__":
    unittest.main()
