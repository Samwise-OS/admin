"""Exercise the Safe-Settings mutation receipt over real local HTTP/fetch."""

import http.server
import json
import os
import pathlib
import shutil
import subprocess
import threading
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]


class Handler(http.server.BaseHTTPRequestHandler):
    def do_PATCH(self):
        self.send_response(200)
        self.end_headers()

    def do_POST(self):
        self.send_response(201)
        self.end_headers()

    def log_message(self, *_args):
        pass


class SafeSettingsTraceTests(unittest.TestCase):
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
