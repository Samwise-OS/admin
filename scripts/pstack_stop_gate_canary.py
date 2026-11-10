#!/usr/bin/env python3
import hashlib
import json
import os
import re
import subprocess
import sys
from dataclasses import dataclass

LAUNCH = os.environ.get("PSTACK_MCP_LAUNCH", os.path.expanduser("~/.config/yantrikdb-mcp/launch.sh"))
GH = os.environ.get("PSTACK_GH_BIN", "/mnt/c/Program Files/GitHub CLI/gh.exe")
REPO = os.environ.get("PSTACK_REPOSITORY", "Samwise-OS/admin")
NAMESPACE = "pstack-completion-governance"
POLICY = (
    "PStack completion governance: a user-owned goal and acceptance test remain "
    "unchanged across autonomous iterations. Process exit, agent self-report, "
    "plateau, and time elapsed do not authorize DONE. Only an independent "
    "verifier operating on the target revision may establish the predicate; "
    "its evidence must match an exact, directly read-back durable memory "
    "witness and the GitHub revision before completion is authorized. "
    "Unfinished work remains OPEN and eligible for recovery."
)

def digest(value):
    return hashlib.sha256(value.encode("utf-8")).hexdigest()

def gh_head():
    r = subprocess.run([GH, "api", f"repos/{REPO}/commits/main", "--jq", ".sha"],
                       capture_output=True, text=True, timeout=15)
    if r.returncode or re.fullmatch(r"[a-f0-9]{40}", r.stdout.strip()) is None:
        raise RuntimeError("GitHub authoritative commit lookup failed")
    return r.stdout.strip()

@dataclass(frozen=True)
class Proof:
    goal_hash: str
    head_sha: str
    verifier_passed: bool
    memory_exact: bool
    fresh_head: bool

def gate(proof, expected_goal_hash, expected_head_sha):
    return (proof.goal_hash == expected_goal_hash
            and proof.head_sha == expected_head_sha
            and proof.verifier_passed is True
            and proof.memory_exact is True
            and proof.fresh_head is True)

class MCP:
    def __init__(self):
        self.proc = subprocess.Popen(
            ["/bin/sh", LAUNCH], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL, text=True, bufsize=1
        )
        self.seq = 0
        self.request("initialize", {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {"name": "pstack-stop-gate", "version": "0.1"}
        })
        self.send({"jsonrpc": "2.0", "method": "notifications/initialized"})

    def send(self, obj):
        self.proc.stdin.write(json.dumps(obj, separators=(",", ":")) + "\n")
        self.proc.stdin.flush()

    def request(self, method, params=None):
        self.seq += 1
        rid = self.seq
        self.send({"jsonrpc": "2.0", "id": rid, "method": method, "params": params or {}})
        for _ in range(100):
            line = self.proc.stdout.readline()
            if not line:
                raise RuntimeError("MCP closed stdout")
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                continue
            if obj.get("id") == rid:
                if "error" in obj:
                    raise RuntimeError(str(obj["error"]))
                return obj.get("result", {})
        raise RuntimeError("MCP response missing")

    def call(self, name, args):
        result = self.request("tools/call", {"name": name, "arguments": args})
        if result.get("isError"):
            raise RuntimeError("MCP " + name + " failed: " + str(result.get("content"))[:300])
        raw = result.get("structuredContent", {}).get("result")
        if isinstance(raw, str):
            return json.loads(raw)
        return raw if raw is not None else result

    def close(self):
        self.proc.terminate()
        self.proc.wait(timeout=3)

def walk(value):
    if isinstance(value, dict):
        yield value
        for child in value.values():
            yield from walk(child)
    elif isinstance(value, list):
        for child in value:
            yield from walk(child)

def test_policy():
    goal = digest(POLICY)
    sha = "a" * 40
    good = Proof(goal, sha, True, True, True)
    cases = {
        "verified": gate(good, goal, sha),
        "worker_exit_not_done": gate(Proof(goal, sha, False, True, True), goal, sha),
        "memory_absent": gate(Proof(goal, sha, True, False, True), goal, sha),
        "goal_replaced": gate(Proof("0" * 64, sha, True, True, True), goal, sha),
        "stale_head": gate(Proof(goal, sha, True, True, False), goal, sha),
        "wrong_revision": gate(Proof(goal, "b" * 40, True, True, True), goal, sha),
    }
    assert cases == {"verified": True, "worker_exit_not_done": False,
                     "memory_absent": False, "goal_replaced": False,
                     "stale_head": False, "wrong_revision": False}, cases
    return cases

def main(argv):
    cases = test_policy()
    print(json.dumps({"local_gate_cases": cases, "passed": len(cases)}))
    if argv == ["selftest"]:
        return 0
    head = gh_head()
    m = MCP()
    try:
        health = m.call("stats", {"action": "health"})
        assert health.get("status") == "ok", health
        if argv == ["probe"]:
            print(json.dumps({"mcp": "live", "github": "live", "repo": REPO, "sha": head,
                              "memory_health": health.get("status")}))
            return 0
        if argv and argv[0] == "judge" and len(argv) in (2, 3):
            retrieved = m.call("memory", {"action": "get", "rid": argv[1]})
            exact = any(d.get("text") == POLICY for d in walk(retrieved))
            proof = Proof(digest(POLICY), head, True, exact, gh_head() == head)
            if len(argv) == 3 and argv[2] not in ("forged-goal", "worker-stopped"):
                raise ValueError("Unknown fault-injection scenario")
            if len(argv) == 3 and argv[2] == "forged-goal":
                proof = Proof("0" * 64, head, True, exact, proof.fresh_head)
            if len(argv) == 3 and argv[2] == "worker-stopped":
                proof = Proof(digest(POLICY), head, False, exact, proof.fresh_head)
            authorized = gate(proof, digest(POLICY), head)
            print(json.dumps({"memory_readback": exact, "mode": argv[-1],
                              "stop_authorized": authorized, "state": "DONE" if authorized else "OPEN"}))
            return 0 if authorized else 75
        if argv != ["bind"]:
            raise ValueError("usage: selftest | probe | bind | judge RID [forged-goal|worker-stopped]")
        remember = m.call("remember", {
            "text": POLICY, "namespace": NAMESPACE, "domain": "architecture",
            "memory_type": "procedural", "importance": 0.95,
            "source": "user", "certainty": 1.0
        })
        rids = [d["rid"] for d in walk(remember) if isinstance(d.get("rid"), str)]
        if not rids:
            print(json.dumps({"remember_result_shape": remember})[:1500])
            raise RuntimeError("No confirmed rid in remember response")
        rid = rids[0]
        retrieved = m.call("memory", {"action": "get", "rid": rid})
        exact = any(d.get("text") == POLICY for d in walk(retrieved))
        proof = Proof(digest(POLICY), head, True, exact, gh_head() == head)
        allowed = gate(proof, digest(POLICY), head)
        print(json.dumps({"record_rid": rid, "memory_exact": exact, "git_revision_stable": proof.fresh_head,
                          "policy_canary_stop_authorized": allowed}))
        return 0 if allowed else 75
    finally:
        m.close()

if __name__ == "__main__":
    try:
        sys.exit(main(sys.argv[1:]))
    except (OSError, ValueError, AssertionError, RuntimeError, subprocess.TimeoutExpired) as err:
        print(json.dumps({"state": "OPEN", "error_class": type(err).__name__,
                          "reason": str(err)[:500]}), file=sys.stderr)
        sys.exit(75)
