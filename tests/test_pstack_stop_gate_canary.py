"""Deterministic admission tests for the memory-bound stop canary."""
import unittest

from scripts.pstack_stop_gate_canary import POLICY, Proof, digest, gate


class PStackStopGateCanaryTests(unittest.TestCase):
    def setUp(self):
        self.goal = digest(POLICY)
        self.sha = "a" * 40
        self.good = Proof(self.goal, self.sha, True, True, True)

    def test_exact_verified_proof_admits(self):
        self.assertTrue(gate(self.good, self.goal, self.sha))

    def test_agent_exit_cannot_admit(self):
        self.assertFalse(gate(Proof(self.goal, self.sha, False, True, True),
                              self.goal, self.sha))

    def test_missing_memory_cannot_admit(self):
        self.assertFalse(gate(Proof(self.goal, self.sha, True, False, True),
                              self.goal, self.sha))

    def test_rewritten_goal_cannot_admit(self):
        self.assertFalse(gate(Proof("0" * 64, self.sha, True, True, True),
                              self.goal, self.sha))

    def test_different_target_revision_cannot_admit(self):
        self.assertFalse(gate(Proof(self.goal, "b" * 40, True, True, True),
                              self.goal, self.sha))

    def test_revision_advanced_while_checking_cannot_admit(self):
        self.assertFalse(gate(Proof(self.goal, self.sha, True, True, False),
                              self.goal, self.sha))

    def test_truthy_non_boolean_verifier_result_cannot_admit(self):
        self.assertFalse(gate(Proof(self.goal, self.sha, 1, True, True),
                              self.goal, self.sha))

    def test_truthy_non_boolean_memory_result_cannot_admit(self):
        self.assertFalse(gate(Proof(self.goal, self.sha, True, 1, True),
                              self.goal, self.sha))


if __name__ == "__main__":
    unittest.main()
