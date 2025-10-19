"""
Unit tests for the Coordinator class.
"""

import pytest
from core.coordinator import Coordinator


class TestCoordinator:
    """Test suite for Coordinator class."""

    def test_initialization(self):
        """Test that coordinator initializes correctly"""
        coordinator = Coordinator()
        assert isinstance(coordinator, Coordinator)
        
    def test_process_task(self):
        """Test task processing"""
        coordinator = Coordinator()
        task_spec = {"id": 1, "description": "Test task"}
        result = coordinator.process_task(task_spec)
        
        assert result["status"] == "enqueued"
        assert result["task_id"] == 1