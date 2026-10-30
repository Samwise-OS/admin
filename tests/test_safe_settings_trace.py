"""Exercise the Safe-Settings mutation receipt over real local HTTP/fetch."""

import http.server
import json
import os
import pathlib
import shutil
import shutil
import subprocess
import tempfile
import threading
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]


class Handler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()

    def do_PATCH(self):
        self.send_response(200)
        self.end_headers()

    def do_POST(self):
        self.send_response(201)
        self.end_headers()

    def log_message(self, *_args):
        pass


class SafeSettingsTraceTests(unittest.TestCase):
    def run_trace(self, source, expected_origin):
        completed = subprocess.run(
            [shutil.which("node"), "--require", str(ROOT / "scripts/trace_safe_settings.cjs"), "-e", source],
            capture_output=True, text=True, timeout=20,
            env={**os.environ, "SAFE_SETTINGS_TRACE_API_ORIGIN": expected_origin},
        )
        receipts = [line.removeprefix("SAFE_SETTINGS_HTTP_RECEIPT ")
                    for line in completed.stdout.splitlines()
                    if line.startswith("SAFE_SETTINGS_HTTP_RECEIPT ")]
        self.assertEqual(len(receipts), 1, completed.stderr)
        return completed, json.loads(receipts[0])

    @unittest.skipUnless(shutil.which("node"), "Node.js is not installed")
    def test_unrelated_origin_request_does_not_support_trace(self):
        expected_server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        unrelated_server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        threads = [threading.Thread(target=server.serve_forever, daemon=True)
                   for server in (expected_server, unrelated_server)]
        for thread in threads:
            thread.start()
        try:
            origin = f"http://127.0.0.1:{expected_server.server_port}"
            unrelated_origin = f"http://127.0.0.1:{unrelated_server.server_port}"
            source = f"fetch('{unrelated_origin}/unrelated');"
            completed, receipt = self.run_trace(source, origin)
        finally:
            for server, thread in zip((expected_server, unrelated_server), threads):
                server.shutdown()
                thread.join(timeout=5)
                server.server_close()
        self.assertFalse(receipt["supported"])
        self.assertNotEqual(completed.returncode, 0)

    @unittest.skipUnless(shutil.which("node"), "Node.js is not installed")
    def test_expected_origin_unmanaged_repository_request_does_not_support_trace(self):
        server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            origin = f"http://127.0.0.1:{server.server_port}"
            source = "fetch(process.env.SAFE_SETTINGS_TRACE_API_ORIGIN + '/repos/Samwise-OS/other').catch(() => {});"
            completed, receipt = self.run_trace(source, origin)
        finally:
            server.shutdown()
            thread.join(timeout=5)
            server.server_close()
        self.assertFalse(receipt["supported"])
        self.assertNotEqual(completed.returncode, 0)

    @unittest.skipUnless(shutil.which("node"), "Node.js is not installed")
    def test_managed_repository_read_supports_zero_mutation_receipt(self):
        server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            origin = f"http://127.0.0.1:{server.server_port}"
            source = "fetch(process.env.SAFE_SETTINGS_TRACE_API_ORIGIN + '/repos/Samwise-OS/admin').catch(() => {});"
            completed, receipt = self.run_trace(source, origin)
        finally:
            server.shutdown()
            thread.join(timeout=5)
            server.server_close()
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertTrue(receipt["supported"])
        self.assertEqual(receipt["managed_config_mutation_requests"], 0)

    @unittest.skipUnless(shutil.which("node"), "Node.js is not installed")
    def test_trace_scope_includes_manifest_repository_names(self):
        server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            origin = f"http://127.0.0.1:{server.server_port}"
            source = "fetch(process.env.SAFE_SETTINGS_TRACE_API_ORIGIN + '/repos/Samwise-OS/repository-template').catch(() => {});"
            completed, receipt = self.run_trace(source, origin)
        finally:
            server.shutdown()
            thread.join(timeout=5)
            server.server_close()
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertTrue(receipt["supported"])

    @unittest.skipUnless(shutil.which("node"), "Node.js is not installed")
    def test_trace_rejects_malformed_manifest_names(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            (root / "scripts").mkdir()
            (root / "config").mkdir()
            shutil.copy(ROOT / "scripts/trace_safe_settings.cjs", root / "scripts/trace_safe_settings.cjs")
            organization = json.loads((ROOT / "config/organization.json").read_text())
            repositories = json.loads((ROOT / "config/repositories.json").read_text())
            repositories["repositories"][0]["name"] = "../outside"
            (root / "config/organization.json").write_text(json.dumps(organization), encoding="utf-8")
            (root / "config/repositories.json").write_text(json.dumps(repositories), encoding="utf-8")
            completed = subprocess.run(
                [shutil.which("node"), "--require", str(root / "scripts/trace_safe_settings.cjs"), "-e", ""],
                capture_output=True, text=True, timeout=20,
            )
        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("invalid or duplicate managed names", completed.stderr)

    @unittest.skipUnless(shutil.which("node"), "Node.js is not installed")
    def test_trace_rejects_authority_identity_changes(self):
        for file_name, field, value in (
            ("repositories.json", "organization", "Other-Org"),
            ("organization.json", "organization_id", 1),
        ):
            with self.subTest(file_name=file_name), tempfile.TemporaryDirectory() as tmp:
                root = pathlib.Path(tmp)
                (root / "scripts").mkdir()
                (root / "config").mkdir()
                shutil.copy(ROOT / "scripts/trace_safe_settings.cjs", root / "scripts/trace_safe_settings.cjs")
                for manifest_name in ("organization.json", "repositories.json"):
                    manifest = json.loads((ROOT / "config" / manifest_name).read_text())
                    if manifest_name == file_name:
                        manifest[field] = value
                    (root / "config" / manifest_name).write_text(json.dumps(manifest), encoding="utf-8")
                completed = subprocess.run(
                    [shutil.which("node"), "--require", str(root / "scripts/trace_safe_settings.cjs"), "-e", ""],
                    capture_output=True, text=True, timeout=20,
                )
                self.assertNotEqual(completed.returncode, 0)
                self.assertIn("authorized Samwise-OS organization", completed.stderr)

    @unittest.skipUnless(shutil.which("node"), "Node.js is not installed")
    def test_trace_rejects_symlinked_authority_manifest(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            (root / "scripts").mkdir()
            (root / "config").mkdir()
            shutil.copy(ROOT / "scripts/trace_safe_settings.cjs", root / "scripts/trace_safe_settings.cjs")
            shutil.copy(ROOT / "config/organization.json", root / "config/organization.json")
            target = root / "repositories-outside.json"
            shutil.copy(ROOT / "config/repositories.json", target)
            (root / "config/repositories.json").symlink_to(target)
            completed = subprocess.run(
                [shutil.which("node"), "--require", str(root / "scripts/trace_safe_settings.cjs"), "-e", ""],
                capture_output=True, text=True, timeout=20,
            )
        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("must not be a symlink", completed.stderr)

    @unittest.skipUnless(shutil.which("node"), "Node.js is not installed")
    def test_counts_config_write_excludes_reporting_and_never_logs_headers(self):
        server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            origin = f"http://127.0.0.1:{server.server_port}"
            source = """
              const origin = process.env.SAFE_SETTINGS_TRACE_API_ORIGIN;
              const headers = { authorization: 'Bearer fixture-secret-token' };
              (async () => {
                await fetch(origin + '/repos/Samwise-OS/baseline-canary/rulesets', { method: 'POST', headers });
                await fetch(origin + '/repos/Samwise-OS/admin/check-runs', { method: 'POST', headers });
                await fetch(origin + '/repos/Samwise-OS/admin', { method: 'PATCH', headers });
              })().catch(() => { process.exitCode = 1; });
            """
            completed = subprocess.run(
                [shutil.which("node"), "--require", str(ROOT / "scripts/trace_safe_settings.cjs"), "-e", source],
                capture_output=True, text=True, timeout=20,
                env={**os.environ, "SAFE_SETTINGS_TRACE_API_ORIGIN": origin},
            )
        finally:
            server.shutdown()
            thread.join(timeout=5)
            server.server_close()
        receipts = [line.removeprefix("SAFE_SETTINGS_HTTP_RECEIPT ")
                    for line in completed.stdout.splitlines()
                    if line.startswith("SAFE_SETTINGS_HTTP_RECEIPT ")]
        self.assertEqual(len(receipts), 1, completed.stderr)
        receipt = json.loads(receipts[0])
        self.assertTrue(receipt["supported"])
        self.assertEqual(receipt["managed_config_mutation_requests"], 2)
        self.assertEqual(receipt["unclassified_managed_writes"], 0)
        self.assertNotIn("fixture-secret-token", completed.stdout + completed.stderr)


if __name__ == "__main__":
    unittest.main()
