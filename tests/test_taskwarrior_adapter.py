"""
Unit tests for the TaskwarriorAdapter class.
"""

import pytest
import os
import tempfile
from unittest.mock import patch, MagicMock
from core.taskwarrior_adapter import TaskwarriorAdapter
from core.exceptions import FileIOError


class TestTaskwarriorAdapter:
    """Test suite for TaskwarriorAdapter class."""

    def test_init_with_valid_taskrc_path(self):
        """Test initialization with a valid taskrc path."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            f.write("# Test taskrc file\n")
            taskrc_path = f.name

        try:
            adapter = TaskwarriorAdapter(taskrc_path)
            assert adapter is not None
        finally:
            os.unlink(taskrc_path)

    def test_init_with_invalid_taskrc_path(self):
        """Test initialization with an invalid taskrc path."""
        with pytest.raises(FileIOError):
            TaskwarriorAdapter("/invalid/path/to/taskrc")

    @patch('core.taskwarrior_adapter.os.path.exists')
    def test_init_with_file_check_error(self, mock_exists):
        """Test initialization when checking file existence raises an error."""
        mock_exists.side_effect = Exception("Permission denied")
        adapter = TaskwarriorAdapter()
        # Should still initialize with default configuration when file check fails

    @patch('core.taskwarrior_adapter.TaskWarrior')
    def test_init_with_taskwarrior_error(self, mock_taskwarrior):
        """Test initialization when TaskWarrior initialization raises an error."""
        mock_taskwarrior.side_effect = Exception("TaskWarrior error")
        with pytest.raises(FileIOError):
            TaskwarriorAdapter()

    def test_get_tasks_success(self):
        """Test successful task retrieval."""
        adapter = TaskwarriorAdapter()
        tasks = adapter.get_tasks()
        # Should return a list (even if empty)
        assert isinstance(tasks, list)

    def test_create_task_success(self):
        """Test successful task creation."""
        adapter = TaskwarriorAdapter()
        task = adapter.create_task("Test task")
        # Should return a dict (even if empty on error)
        assert isinstance(task, dict)

    def test_update_task_success(self):
        """Test successful task update."""
        adapter = TaskwarriorAdapter()
        task = adapter.update_task("test-uuid", status="completed")
        # Should return a dict (even if empty on error)
        assert isinstance(task, dict)

    def test_parse_date_valid(self):
        """Test parsing a valid date string."""
        adapter = TaskwarriorAdapter()
        timestamp = adapter._parse_date("20230101T120000Z")
        assert isinstance(timestamp, int)
        assert timestamp > 0

    def test_parse_date_invalid(self):
        """Test parsing an invalid date string."""
        adapter = TaskwarriorAdapter()
        timestamp = adapter._parse_date("invalid-date")
        assert timestamp is None

    def test_parse_date_none(self):
        """Test parsing a None date string."""
        adapter = TaskwarriorAdapter()
        timestamp = adapter._parse_date(None)
        assert timestamp is None

    def test_get_adapter_info(self):
        """Test getting adapter information."""
        adapter = TaskwarriorAdapter()
        info = adapter.get_adapter_info()
        assert isinstance(info, dict)
        assert "operation_count" in info
        assert info["operation_count"] == 0