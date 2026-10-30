import importlib.util
import base64
import pathlib
import unittest
from unittest import mock

ROOT = pathlib.Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("provision", ROOT / "scripts/provision.py")
provision = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(provision)


class GitHubContentApi:
    """Small REST-boundary fixture for provisioning PR behavior."""

    def __init__(self, base_sha="base-1", main_files=None, open_pr=None, branch=None, move_after=None):
        self.base_sha = base_sha
        self.main_files = main_files or {}
        self.open_pr = open_pr
        self.branch = branch
        self.move_after = move_after
        self.base_reads = 0
        self.calls = []
        self.proposal_files = {}

    def __call__(self, method, endpoint, body=None, paginate=False):
        self.calls.append((method, endpoint, body))
        if endpoint == "repos/Samwise-OS/demo/git/ref/heads/main":
            self.base_reads += 1
            current = self.move_after if self.move_after and self.base_reads >= 2 else self.base_sha
            return {"object": {"sha": current}}
        if endpoint == f"repos/Samwise-OS/demo/git/commits/{self.base_sha}":
            return {"tree": {"sha": "tree-base"}, "parents": []}
        if endpoint == "repos/Samwise-OS/demo/git/commits/proposal-1":
            return {"tree": {"sha": "tree-proposal"}, "parents": [{
                "sha": self.base_sha, "url": "https://api.github.com/repos/Samwise-OS/demo/git/commits/base"
            }]}
        if endpoint == "repos/Samwise-OS/demo/git/trees/tree-base?recursive=1":
            return {"truncated": False, "tree": self.main_files}
        if endpoint == "repos/Samwise-OS/demo/git/trees/tree-proposal?recursive=1":
            return {"truncated": False, "tree": self.proposal_files}
        if endpoint.startswith("repos/Samwise-OS/demo/pulls?"):
            return [self.open_pr] if self.open_pr else []
        if endpoint.startswith("repos/Samwise-OS/demo/git/matching-refs/"):
            return ([{"ref": f"refs/heads/{self.branch['name']}",
                      "object": {"sha": self.branch["sha"]}}] if self.branch else [])
        if method == "POST" and endpoint == "repos/Samwise-OS/demo/git/blobs":
            return {"sha": provision.blob_sha(body["content"])}
        if method == "POST" and endpoint == "repos/Samwise-OS/demo/git/trees":
            self.proposal_files = list(self.main_files)
            for entry in body["tree"]:
                self.proposal_files = [item for item in self.proposal_files if item["path"] != entry["path"]]
                self.proposal_files.append({"path": entry["path"], "mode": entry["mode"],
                                            "type": "blob", "sha": entry["sha"]})
            return {"sha": "tree-proposal"}
        if method == "POST" and endpoint == "repos/Samwise-OS/demo/git/commits":
            self.assertions(body["parents"] == [self.base_sha], "proposal must use the observed base snapshot")
            return {"sha": "proposal-1"}
        if method == "POST" and endpoint == "repos/Samwise-OS/demo/git/refs":
            self.assertions(body["ref"].startswith("refs/heads/codex/provision-"), "branch must be namespaced")
            return {"ref": body["ref"], "object": {"sha": body["sha"]}}
        if method == "POST" and endpoint == "repos/Samwise-OS/demo/pulls":
            branch = body["head"].split(":", 1)[1]
            return {"html_url": "https://github.com/Samwise-OS/demo/pull/7", "number": 7,
                    "state": "open", "head": {"ref": branch, "sha": "proposal-1",
                                                  "repo": {"full_name": "Samwise-OS/demo"}},
                    "base": {"ref": "main", "sha": self.base_sha}}
        raise AssertionError(f"Unexpected fixture call: {method} {endpoint}")

    @staticmethod
    def assertions(condition, message):
        if not condition:
            raise AssertionError(message)


class GitHubSettingsApi:
    def __init__(self, labels=None, reporting=True, denied=None, reporting_readback=None):
        self.labels = [dict(label) for label in (labels or [])]
        self.reporting = reporting
        self.denied = denied
        self.reporting_readback = reporting_readback
        self.calls = []
        self.reporting_reads = 0

    def __call__(self, method, endpoint, body=None, paginate=False):
        self.calls.append((method, endpoint, body))
        if endpoint == "repos/Samwise-OS/demo/labels?per_page=100":
            if self.denied == endpoint:
                raise RuntimeError("labels read denied")
            return [dict(label) for label in self.labels]
        if endpoint == "repos/Samwise-OS/demo/private-vulnerability-reporting":
            if self.denied == endpoint:
                raise RuntimeError("private reporting read denied")
            if method == "GET":
                self.reporting_reads += 1
                enabled = (self.reporting_readback if self.reporting_readback is not None
                           and self.reporting_reads > 1 else self.reporting)
                return {"enabled": enabled}
            if method == "PUT":
                if self.reporting_readback is None:
                    self.reporting = True
                return None
        if method == "POST" and endpoint == "repos/Samwise-OS/demo/labels":
            self.labels.append(dict(body))
            return dict(body)
        if method == "PATCH" and endpoint.startswith("repos/Samwise-OS/demo/labels/"):
            name = endpoint.rsplit("/", 1)[1]
            label = next(item for item in self.labels if item["name"] == name)
            label.update(body)
            return dict(label)
        raise AssertionError(f"Unexpected fixture call: {method} {endpoint}")


class ProvisionTests(unittest.TestCase):
    def test_labels_create_missing_update_only_differences_and_preserve_unrelated(self):
        desired = [
            {"name": "bug", "color": "d73a4a", "description": "Something isn't working"},
            {"name": "needs-triage", "color": "d4c5f9", "description": "New issue awaiting classification"},
        ]
        unrelated = {"name": "custom", "color": "123456", "description": "Keep me"}
        fixture = GitHubSettingsApi(labels=[
            {"name": "bug", "color": "ffffff", "description": "old"}, unrelated
        ])
        with mock.patch.object(provision, "api", side_effect=fixture):
            result = provision.sync_labels("Samwise-OS/demo", desired, apply=True)
        self.assertEqual(result["label_state"], "converged")
        self.assertEqual(result["label_changes"], [
            {"name": "bug", "action": "update"}, {"name": "needs-triage", "action": "create"}
        ])
        self.assertEqual(next(label for label in fixture.labels if label["name"] == "custom"), unrelated)
        self.assertEqual([method for method, _, _ in fixture.calls], ["GET", "PATCH", "POST", "GET"])

    def test_canonical_labels_rerun_is_read_only(self):
        desired = [{"name": "bug", "color": "d73a4a", "description": "Something isn't working"}]
        fixture = GitHubSettingsApi(labels=desired)
        with mock.patch.object(provision, "api", side_effect=fixture):
            result = provision.sync_labels("Samwise-OS/demo", desired, apply=True)
        self.assertEqual(result, {"label_changes": [], "label_state": "converged"})
        self.assertEqual([method for method, _, _ in fixture.calls], ["GET"])

    def test_label_readback_mismatch_fails_after_write(self):
        desired = [{"name": "bug", "color": "d73a4a", "description": "Something isn't working"}]
        fixture = GitHubSettingsApi(labels=[])
        original = fixture.__call__

        def wrong_readback(method, endpoint, body=None, paginate=False):
            result = original(method, endpoint, body, paginate)
            if method == "GET" and fixture.calls.count((method, endpoint, body)) > 1:
                return [{"name": "bug", "color": "ffffff", "description": "wrong"}]
            return result

        with mock.patch.object(provision, "api", side_effect=wrong_readback):
            with self.assertRaisesRegex(ValueError, "Label readback mismatch"):
                provision.sync_labels("Samwise-OS/demo", desired, apply=True)
        self.assertTrue(any(method == "POST" for method, _, _ in fixture.calls))

    def test_denied_reads_fail_before_any_settings_write(self):
        for endpoint in ("repos/Samwise-OS/demo/labels?per_page=100",
                         "repos/Samwise-OS/demo/private-vulnerability-reporting"):
            with self.subTest(endpoint=endpoint):
                fixture = GitHubSettingsApi(denied=endpoint)
                with mock.patch.object(provision, "api", side_effect=fixture):
                    with self.assertRaisesRegex(RuntimeError, "read denied"):
                        if "labels" in endpoint:
                            provision.sync_labels("Samwise-OS/demo", [
                                {"name": "bug", "color": "d73a4a", "description": "x"}
                            ], apply=True)
                        else:
                            provision.sync_private_vulnerability_reporting(
                                "Samwise-OS/demo", {"visibility": "public"}, apply=True
                            )
                self.assertEqual([method for method, _, _ in fixture.calls], ["GET"])

    def test_private_reporting_is_idempotent_and_readback_gated(self):
        public_repo = {"visibility": "public"}
        already_enabled = GitHubSettingsApi(reporting=True)
        with mock.patch.object(provision, "api", side_effect=already_enabled):
            result = provision.sync_private_vulnerability_reporting("Samwise-OS/demo", public_repo, apply=True)
        self.assertEqual(result, {"enabled": True, "changed": False, "state": "enabled"})
        self.assertEqual([method for method, _, _ in already_enabled.calls], ["GET"])

        not_enabled = GitHubSettingsApi(reporting=False)
        with mock.patch.object(provision, "api", side_effect=not_enabled):
            result = provision.sync_private_vulnerability_reporting("Samwise-OS/demo", public_repo, apply=True)
        self.assertEqual(result, {"enabled": True, "changed": True, "state": "enabled"})
        self.assertEqual([method for method, _, _ in not_enabled.calls], ["GET", "PUT", "GET"])

    def test_private_reporting_readback_mismatch_fails_closed(self):
        fixture = GitHubSettingsApi(reporting=False, reporting_readback=False)
        with mock.patch.object(provision, "api", side_effect=fixture):
            with self.assertRaisesRegex(ValueError, "readback failed"):
                provision.sync_private_vulnerability_reporting(
                    "Samwise-OS/demo", {"visibility": "public"}, apply=True
                )
        self.assertEqual([method for method, _, _ in fixture.calls], ["GET", "PUT", "GET"])

    def test_private_reporting_rejects_non_public_target_without_api_calls(self):
        fixture = GitHubSettingsApi()
        with mock.patch.object(provision, "api", side_effect=fixture):
            with self.assertRaisesRegex(ValueError, "declared public repositories"):
                provision.sync_private_vulnerability_reporting(
                    "Samwise-OS/demo", {"visibility": "private"}, apply=True
                )
        self.assertEqual(fixture.calls, [])

    def test_identical_main_content_is_already_converged_without_writes(self):
        desired = {"README.md": "baseline\n"}
        fixture = GitHubContentApi(main_files=[{
            "path": "README.md", "mode": "100644", "type": "blob",
            "sha": provision.blob_sha("baseline\n")
        }])
        with mock.patch.object(provision, "api", side_effect=fixture):
            result = provision.sync_files("Samwise-OS/demo", desired, apply=True)
        self.assertEqual(result, {"changes": [], "content_pull_request": None,
                                  "content_state": "already_converged"})
        self.assertFalse(any(method != "GET" for method, _, _ in fixture.calls))

    def test_changed_files_are_proposed_on_exact_base_without_direct_main_write(self):
        desired = {"README.md": "canonical\n"}
        fixture = GitHubContentApi(main_files=[{
            "path": "README.md", "mode": "100644", "type": "blob", "sha": provision.blob_sha("old\n")
        }])
        with mock.patch.object(provision, "api", side_effect=fixture):
            result = provision.sync_files("Samwise-OS/demo", desired, apply=True)
        self.assertEqual(result["content_state"], "pending_pull_request")
        self.assertEqual(result["content_pull_request"]["url"], "https://github.com/Samwise-OS/demo/pull/7")
        self.assertEqual(result["content_pull_request"]["base_sha"], "base-1")
        self.assertEqual(result["changes"], ["README.md"])
        self.assertTrue(any(method == "POST" and endpoint == "repos/Samwise-OS/demo/pulls"
                            for method, endpoint, _ in fixture.calls))
        self.assertFalse(any(method == "PATCH" for method, _, _ in fixture.calls))

    def test_rerun_reuses_matching_open_pull_request_without_writes(self):
        desired = {"README.md": "canonical\n"}
        branch = provision.provision_branch_name("base-1", desired)
        fixture = GitHubContentApi(
            open_pr={"html_url": "https://github.com/Samwise-OS/demo/pull/7", "number": 7,
                     "state": "open", "head": {"ref": branch, "sha": "proposal-1",
                                                   "repo": {"full_name": "Samwise-OS/demo"}},
                     "base": {"ref": "main", "sha": "base-1"}},
            main_files=[{"path": "README.md", "mode": "100644", "type": "blob",
                         "sha": provision.blob_sha("old\n")}],
        )
        fixture.proposal_files = [{"path": "README.md", "mode": "100644", "type": "blob",
                                   "sha": provision.blob_sha("canonical\n")}]
        with mock.patch.object(provision, "api", side_effect=fixture):
            result = provision.sync_files("Samwise-OS/demo", desired, apply=True)
        self.assertEqual(result["content_pull_request"]["number"], 7)
        self.assertFalse(any(method != "GET" for method, _, _ in fixture.calls))

    def test_changed_main_snapshot_changes_deterministic_branch_name(self):
        desired = {"README.md": "canonical\n"}
        self.assertNotEqual(
            provision.provision_branch_name("base-1", desired),
            provision.provision_branch_name("base-2", desired),
        )
        fixture = GitHubContentApi(
            main_files=[{"path": "README.md", "mode": "100644", "type": "blob",
                         "sha": provision.blob_sha("old\n")}],
            move_after="base-2",
        )
        with mock.patch.object(provision, "api", side_effect=fixture):
            with self.assertRaisesRegex(ValueError, "moved from base-1 to base-2"):
                provision.sync_files("Samwise-OS/demo", desired, apply=True)
        self.assertFalse(any(method == "POST" and endpoint == "repos/Samwise-OS/demo/git/refs"
                            for method, endpoint, _ in fixture.calls))

    def test_stale_existing_provision_branch_is_never_overwritten(self):
        desired = {"README.md": "canonical\n"}
        branch = provision.provision_branch_name("base-1", desired)
        fixture = GitHubContentApi(
            main_files=[{"path": "README.md", "mode": "100644", "type": "blob",
                         "sha": provision.blob_sha("old\n")}],
            branch={"name": branch, "sha": "proposal-1"},
        )
        fixture.proposal_files = [{"path": "README.md", "mode": "100644", "type": "blob",
                                   "sha": provision.blob_sha("stale\n")}]
        with mock.patch.object(provision, "api", side_effect=fixture):
            with self.assertRaisesRegex(ValueError, "exact base plus desired tree"):
                provision.sync_files("Samwise-OS/demo", desired, apply=True)
        self.assertFalse(any(method != "GET" for method, _, _ in fixture.calls))

    def test_open_pr_branch_with_unexpected_file_is_refused(self):
        desired = {"README.md": "canonical\n"}
        branch = provision.provision_branch_name("base-1", desired)
        license_entry = {"path": "LICENSE", "mode": "100644", "type": "blob",
                         "sha": provision.blob_sha("license\n")}
        fixture = GitHubContentApi(
            open_pr={"html_url": "https://github.com/Samwise-OS/demo/pull/7", "number": 7,
                     "state": "open", "head": {"ref": branch, "sha": "proposal-1",
                                                   "repo": {"full_name": "Samwise-OS/demo"}},
                     "base": {"ref": "main", "sha": "base-1"}},
            main_files=[{"path": "README.md", "mode": "100644", "type": "blob",
                         "sha": provision.blob_sha("old\n")}, license_entry],
        )
        fixture.proposal_files = [
            {"path": "README.md", "mode": "100644", "type": "blob",
             "sha": provision.blob_sha("canonical\n")},
            license_entry,
            {"path": "unexpected.txt", "mode": "100644", "type": "blob",
             "sha": provision.blob_sha("unrequested\n")},
        ]
        with mock.patch.object(provision, "api", side_effect=fixture):
            with self.assertRaisesRegex(ValueError, "exact base plus desired tree"):
                provision.sync_files("Samwise-OS/demo", desired, apply=True)
        self.assertFalse(any(method != "GET" for method, _, _ in fixture.calls))

    def test_open_pr_branch_with_unrelated_mode_and_content_change_is_refused(self):
        desired = {"README.md": "canonical\n"}
        branch = provision.provision_branch_name("base-1", desired)
        fixture = GitHubContentApi(
            open_pr={"html_url": "https://github.com/Samwise-OS/demo/pull/7", "number": 7,
                     "state": "open", "head": {"ref": branch, "sha": "proposal-1",
                                                   "repo": {"full_name": "Samwise-OS/demo"}},
                     "base": {"ref": "main", "sha": "base-1"}},
            main_files=[
                {"path": "README.md", "mode": "100644", "type": "blob",
                 "sha": provision.blob_sha("old\n")},
                {"path": "LICENSE", "mode": "100644", "type": "blob",
                 "sha": provision.blob_sha("license\n")},
            ],
        )
        fixture.proposal_files = [
            {"path": "README.md", "mode": "100644", "type": "blob",
             "sha": provision.blob_sha("canonical\n")},
            {"path": "LICENSE", "mode": "100755", "type": "blob",
             "sha": provision.blob_sha("changed\n")},
        ]
        with mock.patch.object(provision, "api", side_effect=fixture):
            with self.assertRaisesRegex(ValueError, "exact base plus desired tree"):
                provision.sync_files("Samwise-OS/demo", desired, apply=True)
        self.assertFalse(any(method != "GET" for method, _, _ in fixture.calls))

    def test_existing_repository_name_with_replacement_id_fails_preflight(self):
        with self.assertRaisesRegex(ValueError, "repository identity mismatch"):
            provision.validate_existing_identities(
                [{"name": "baseline-canary", "id": 1436487640}],
                {"baseline-canary": {"id": 999999999}},
            )

    def test_existing_repository_without_manifest_id_requires_explicit_adoption(self):
        with self.assertRaisesRegex(ValueError, "record its ID.*before adoption"):
            provision.validate_existing_identities(
                [{"name": "future-repository"}],
                {"future-repository": {"id": 12345}},
            )

    def test_workflow_revision_requires_the_expected_reusable_workflow(self):
        with self.assertRaisesRegex(ValueError, "repository-baseline.yml"):
            provision.validate_workflow_source({"name": "admin"})

    def test_workflow_revision_must_be_reusable(self):
        source = base64.b64encode(b"name: wrong\njobs: {}\n").decode("ascii")
        with self.assertRaisesRegex(ValueError, "not callable"):
            provision.validate_workflow_source({
                "type": "file", "path": provision.WORKFLOW_PATH, "content": source
            })

    def test_published_github_base64_line_wrapping_is_accepted(self):
        body = base64.b64encode(b"name: baseline\non:\n  workflow_call:\n").decode("ascii")
        wrapped = body[:12] + "\n" + body[12:]
        provision.validate_workflow_source({
            "type": "file", "path": provision.WORKFLOW_PATH, "content": wrapped
        })

    def test_existing_wrong_visibility_is_not_silently_converted(self):
        desired = {"name": "baseline-canary", "visibility": "public", "is_template": False, "description": "Canary"}
        observed = {"name": "baseline-canary", "visibility": "private", "is_template": False, "description": "Canary"}
        with self.assertRaisesRegex(ValueError, "visibility"):
            provision.metadata_plan(desired, observed)


if __name__ == "__main__":
    unittest.main()
