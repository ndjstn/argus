"""
Unit tests for the PolicyEngine class.
"""

import pytest
from core.policy import PolicyEngine


class TestPolicyEngine:
    """Test suite for PolicyEngine class."""

    def test_initialization(self):
        policy_engine = PolicyEngine(config_path="tests/test_data/test_policy.yaml")
        assert isinstance(policy_engine, PolicyEngine)
        
    def test_decide(self):
        """Test decision making"""
        policy_engine = PolicyEngine(config_path="tests/test_data/test_policy.yaml")
        task_features = {"project": "demo", "urgency": 5.0}
        env_probes = {"ping_ms": 50, "cpu_load": 0.3}
        
        decision = policy_engine.decide(task_features, env_probes)
        
        assert "agent" in decision
        assert "tool" in decision
        assert "params" in decision