import unittest
from core.coordinator import Coordinator

class TestCoordinator(unittest.TestCase):
    def setUp(self):
        self.coordinator = Coordinator()
        
    def test_initialization(self):
        """Test that coordinator initializes correctly"""
        self.assertIsInstance(self.coordinator, Coordinator)
        
    def test_process_task(self):
        """Test task processing"""
        task_spec = {"id": 1, "description": "Test task"}
        result = self.coordinator.process_task(task_spec)
        
        self.assertEqual(result["status"], "enqueued")
        self.assertEqual(result["task_id"], 1)

if __name__ == "__main__":
    unittest.main()