from typing import Dict, Any
import logging
import yaml
import os
import time

class PolicyEngine:
    """Policy engine for decision making"""
    
    def __init__(self, config_path: str):
        self.logger = logging.getLogger(__name__)
        self.decision_count = 0
        self.logger.info("Initializing Policy Engine")
        
        # Load policies from configuration file
        self.policies = self._load_policies(config_path)
        
    def _load_policies(self, config_path: str) -> Dict[str, Any]:
        """Load policies from YAML configuration file"""
        start_time = time.time()
        try:
            config_full_path = os.path.join(os.path.dirname(__file__), "..", config_path)
            with open(config_full_path, 'r') as file:
                policies = yaml.safe_load(file)
            load_time = time.time() - start_time
            self.logger.info("Policy configuration loaded successfully", extra={
                "event": "policy_config_loaded",
                "config_path": config_path,
                "load_time_ms": round(load_time * 1000, 2),
                "policy_keys": list(policies.keys()) if policies else []
            })
            return policies
        except Exception as e:
            load_time = time.time() - start_time
            self.logger.error("Failed to load policy configuration", extra={
                "event": "policy_config_load_failed",
                "config_path": config_path,
                "error": str(e),
                "load_time_ms": round(load_time * 1000, 2)
            })
            # Return default policies if loading fails
            default_policies = {
                "routing": {
                    "max_latency_ms": 12000,
                    "min_success_prior": 0.55,
                    "prefer_cached_when_ping_ms_gt": 120
                },
                "agents": {
                    "browser": {
                        "default_timeout_s": 15,
                        "max_retries": 2,
                        "headed_on_flake_rate_gt": 0.25
                    },
                    "research": {
                        "searxng_url": "http://localhost:8080"
                    }
                },
                "fallbacks": {
                    "captcha": "block_and_notify"
                },
                "learning": {
                    "enabled": True,
                    "min_samples": 200,
                    "retrain_every_runs": 200
                }
            }
            self.logger.info("Using default policies due to config load failure", extra={
                "event": "using_default_policies",
                "config_path": config_path
            })
            return default_policies
        
    def decide(self, task_features: Dict[str, Any], env_probes: Dict[str, Any]) -> Dict[str, Any]:
        """Make a routing decision based on task features and environment probes"""
        start_time = time.time()
        self.decision_count += 1
        
        # Log input features for debugging
        self.logger.debug("Making decision for task", extra={
            "event": "policy_decision_start",
            "task_features": task_features,
            "env_probes": env_probes,
            "decision_count": self.decision_count
        })
        
        # Simple routing logic based on policies
        # In a real implementation, this would be more sophisticated
        agent = "browser"
        tool = "playwright"
        
        # Check if we should prefer cached results based on network conditions
        ping_ms = env_probes.get("ping_ms", 0)
        prefer_cached = ping_ms > self.policies["routing"]["prefer_cached_when_ping_ms_gt"]
        if prefer_cached:
            self.logger.info("Preferring cached results due to high network latency", extra={
                "event": "prefer_cached_results",
                "ping_ms": ping_ms,
                "threshold": self.policies["routing"]["prefer_cached_when_ping_ms_gt"]
            })
            # In a real implementation, we would check for cached results here
            
        # Set parameters based on agent policies
        params = {}
        if agent in self.policies["agents"]:
            agent_policy = self.policies["agents"][agent]
            params["timeout"] = agent_policy.get("default_timeout_s", 15)
            params["retries"] = agent_policy.get("max_retries", 2)
            
            # Check if we should use headed mode based on flake rate
            flake_rate = env_probes.get("flake_rate", 0)
            headed_threshold = agent_policy.get("headed_on_flake_rate_gt", 0.25)
            use_headed = flake_rate > headed_threshold
            if use_headed:
                params["headed"] = True
                self.logger.info("Using headed mode due to high flake rate", extra={
                    "event": "headed_mode_activated",
                    "flake_rate": flake_rate,
                    "threshold": headed_threshold
                })
        
        decision_time = time.time() - start_time
        decision = {
            "agent": agent,
            "tool": tool,
            "params": params
        }
        
        self.logger.info("Policy decision completed", extra={
            "event": "policy_decision_completed",
            "decision_time_ms": round(decision_time * 1000, 2),
            "decision": decision,
            "prefer_cached": prefer_cached,
            "decision_count": self.decision_count
        })
        
        return decision

    def get_policy_info(self) -> Dict[str, Any]:
        """Get information about the policy engine for monitoring"""
        return {
            "decision_count": self.decision_count,
            "policy_keys": list(self.policies.keys()) if self.policies else []
        }

if __name__ == "__main__":
    # For testing purposes
    policy_engine = PolicyEngine(config_path="configs/policy.yaml")
    decision = policy_engine.decide(
        {"project": "demo", "urgency": 5.0},
        {"ping_ms": 50, "cpu_load": 0.3, "flake_rate": 0.1}
    )
    print(decision)