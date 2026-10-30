"""Run the secretless GitHub baseline validators and write a versioned receipt."""

import argparse
import datetime
import json
import os
import pathlib
import platform
import re
import subprocess
import sys
import time

ROOT = pathlib.Path(__file__).resolve().parents[1]
LOCAL = ROOT / ".local"
TIMEOUT_SECONDS = 60
CHECK_VERSION = "2026-10-30.2"
CHECKS = (
    ("configuration", [sys.executable, "scripts/audit.py", "validate"]),
    ("repository_settings", [sys.executable, "scripts/generate_repository_settings.py", "--check"]),
    ("safe_settings", [sys.executable, "scripts/validate_safe_settings.py"]),
    ("unit_tests", [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-v"]),
)


def output_path(value):
    if LOCAL.is_symlink():
        raise ValueError(".local/ must not be a symlink")
    LOCAL.mkdir(exist_ok=True)
    local_root = LOCAL.resolve()
    if local_root.parent != ROOT.resolve() or local_root.name != ".local":
        raise ValueError(".local/ must resolve to this repository's ignored evidence directory")
    candidate = pathlib.Path(value)
    if not candidate.is_absolute():
        candidate = ROOT / candidate
    resolved = candidate.resolve()
    try:
        resolved.relative_to(local_root)
    except ValueError as error:
        raise ValueError("receipt output must stay under ignored .local/") from error
    if resolved == local_root:
        raise ValueError("receipt output must name a file under .local/")
    resolved.parent.mkdir(parents=True, exist_ok=True)
    return resolved


def git_head(run_command):
    result = run_command(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True,
        text=True, timeout=TIMEOUT_SECONDS, check=False,
    )
    if result.returncode != 0:
        return None
    value = result.stdout.strip()
    return value if re.fullmatch(r"[0-9a-f]{40,64}", value) else None


def unittest_summary(output):
    ran = re.search(r"^Ran (\d+) tests?\b", output, re.MULTILINE)
    summary = re.search(r"^OK(?: \(skipped=(\d+)\))?$", output, re.MULTILINE)
    if not ran or not summary:
        return None
    return int(ran.group(1)), int(summary.group(1) or 0)


def write_log(path, stdout, stderr):
    path.write_text(
        "--- stdout ---\n" + stdout + "\n--- stderr ---\n" + stderr,
        encoding="utf-8",
    )


def run_check(name, command, run_command, logs_dir):
    started = time.monotonic()
    timed_out = False
    launch_error = None
    try:
        result = run_command(
            command, cwd=ROOT, capture_output=True, text=True,
            timeout=TIMEOUT_SECONDS, check=False,
        )
        stdout = result.stdout or ""
        stderr = result.stderr or ""
        exit_code = result.returncode
    except subprocess.TimeoutExpired as error:
        timed_out = True
        stdout = error.stdout or ""
        stderr = error.stderr or ""
        if isinstance(stdout, bytes):
            stdout = stdout.decode("utf-8", errors="replace")
        if isinstance(stderr, bytes):
            stderr = stderr.decode("utf-8", errors="replace")
        exit_code = None
    except OSError as error:
        launch_error = type(error).__name__
        stdout, stderr, exit_code = "", "", None

    log_path = logs_dir / f"{name}.txt"
    write_log(log_path, stdout, stderr)
    duration_ms = round((time.monotonic() - started) * 1000)
    status = "pass" if exit_code == 0 else "fail"
    reason = f"command exited with code {exit_code}" if exit_code not in (0, None) else None
    if timed_out:
        status, reason = "fail", f"command timed out after {TIMEOUT_SECONDS}s"
    elif launch_error:
        status, reason = "unknown", f"command could not start ({launch_error})"
    elif name == "unit_tests" and exit_code == 0:
        summary = unittest_summary(stdout + "\n" + stderr)
        if summary is None:
            status, reason = "unknown", "unittest summary missing or malformed"
        elif not summary[0]:
            status, reason = "unknown", "required unittest suite ran zero tests"
        elif summary[1]:
            status, reason = "unknown", f"required unittest suite skipped {summary[1]} test(s)"

    return {
        "name": name,
        "command": command,
        "expected": "exit 0; unit_tests must run at least one test and report zero skips",
        "actual_exit_code": exit_code,
        "actual": ("command timed out" if timed_out else
                   f"process exited with code {exit_code}" if exit_code is not None else
                   "command could not start"),
        "duration_ms": duration_ms,
        "status": status,
        "reason": reason,
        "retry_count": 0,
        "limit_seconds": TIMEOUT_SECONDS,
        "evidence_path": log_path.relative_to(ROOT).as_posix(),
    }


def overall_outcome(checks, head_sha, dirty):
    if not head_sha or dirty is None:
        return "unknown"
    if any(check["status"] == "fail" for check in checks):
        return "fail"
    if (any(check["status"] == "unknown" for check in checks) or
            [check["name"] for check in checks] != [item[0] for item in CHECKS]):
        return "unknown"
    return "pass"


def worktree_dirty(run_command):
    result = run_command(
        ["git", "status", "--porcelain"], cwd=ROOT, capture_output=True,
        text=True, timeout=TIMEOUT_SECONDS, check=False,
    )
    if result.returncode != 0:
        return None
    return bool(result.stdout.strip())


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", default=".local/validation-receipt.json")
    args = parser.parse_args(argv)
    try:
        destination = output_path(args.output)
    except (OSError, ValueError) as error:
        print(f"doctor: {error}", file=sys.stderr)
        return 2

    head_sha = None
    dirty = None
    checks = []
    diagnostics = []
    try:
        head_sha = git_head(subprocess.run)
        if head_sha:
            dirty = worktree_dirty(subprocess.run)
    except (OSError, subprocess.TimeoutExpired):
        head_sha = None
    if head_sha:
        logs_dir = LOCAL / "validation-logs"
        try:
            if logs_dir.is_symlink():
                raise ValueError("validation log directory must not be a symlink")
            logs_dir.mkdir(exist_ok=True)
            logs_dir.resolve().relative_to(LOCAL.resolve())
            checks = [run_check(name, command, subprocess.run, logs_dir) for name, command in CHECKS]
        except (OSError, ValueError) as error:
            diagnostics.append(f"Validation evidence directory unavailable ({type(error).__name__}).")
    else:
        diagnostics.append("Unable to establish a valid Git HEAD SHA; checks were not run.")

    reported_head = (os.environ.get("SAMWISE_PR_HEAD_SHA") or
                     os.environ.get("SAMWISE_GITHUB_SHA") or head_sha)
    if not isinstance(reported_head, str) or not re.fullmatch(r"[0-9a-f]{40,64}", reported_head):
        reported_head = None
    receipt = {
        "schema_version": 1,
        "check_version": CHECK_VERSION,
        "head_sha": reported_head,
        "checkout_sha": head_sha,
        "worktree_dirty": dirty,
        "created_at_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "platform": platform.system().lower(),
        "github": {key: value for key, value in {
            "repository": os.environ.get("GITHUB_REPOSITORY"),
            "run_id": os.environ.get("GITHUB_RUN_ID"),
            "run_attempt": os.environ.get("GITHUB_RUN_ATTEMPT"),
            "event_name": os.environ.get("GITHUB_EVENT_NAME"),
            "ref": os.environ.get("GITHUB_REF"),
            "workflow_sha": os.environ.get("SAMWISE_GITHUB_SHA"),
            "pull_request_number": os.environ.get("SAMWISE_PR_NUMBER"),
            "pull_request_head_sha": os.environ.get("SAMWISE_PR_HEAD_SHA"),
            "pull_request_base_sha": os.environ.get("SAMWISE_PR_BASE_SHA"),
        }.items() if value},
        "outcome": overall_outcome(checks, reported_head, dirty),
        "diagnostics": diagnostics,
        "checks": checks,
    }
    destination.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "schema_version": receipt["schema_version"],
        "head_sha": receipt["head_sha"],
        "outcome": receipt["outcome"],
        "checks": [{"name": c["name"], "status": c["status"], "reason": c["reason"]}
                   for c in checks],
        "receipt": destination.relative_to(ROOT).as_posix(),
    }, separators=(",", ":")))
    return {"pass": 0, "fail": 1, "unknown": 2}[receipt["outcome"]]


if __name__ == "__main__":
    raise SystemExit(main())
