import unittest
from core.policy import PolicyEngine

class TestPolicyEngine(unittest.TestCase):
    def setUp(self):
        self.policy_engine = PolicyEngine()
        
    def test_initialization(self):
        """Test that policy engine initializes correctly"""
        self.assertIsInstance(self.policy_engine, PolicyEngine)
        
    def test_decide(self):
        """Test decision making"""
        task_features = {"project": "demo", "urgency": 5.0}
        env_probes = {"ping_ms": 50, "cpu_load": 0.3}
        
        decision = self.policy_engine.decide(task_features, env_probes)
        
        self.assertIn("agent", decision)
        self.assertIn("tool", decision)
        self.assertIn("params", decision)

if __name__ == "__main__":
    unittest.main()