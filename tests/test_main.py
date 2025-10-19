"""
Unit tests for the main application module.
"""

import pytest
import sys
import os
from unittest.mock import patch, MagicMock

# Add the project root to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))


class TestMainApplication:
    """Test suite for main application module."""

    def test_application_manager_initialization(self):
        """Test ApplicationManager initialization"""
        from main import ApplicationManager
        
        # Test creating an application manager
        app_manager = ApplicationManager()
        
        # Verify attributes
        assert hasattr(app_manager, 'services')
        assert hasattr(app_manager, 'shutdown_event')
        assert hasattr(app_manager, 'threads')

    def test_main_module_import(self):
        """Test that the main module can be imported without errors"""
        import main
        
        # Verify key components exist
        assert hasattr(main, 'ApplicationManager')
        assert hasattr(main, 'main')

    @patch('main.sys.exit')
    def test_application_manager_shutdown(self, mock_exit):
        """Test ApplicationManager shutdown functionality"""
        from main import ApplicationManager
        
        # Test creating an application manager
        app_manager = ApplicationManager()
        
        # Test shutdown
        app_manager.shutdown()
        
        # Verify sys.exit was called
        mock_exit.assert_called_once()