"""
Unit tests for the ErrorNotificationManager class and related functions.
"""

import pytest
import smtplib
import subprocess
from unittest.mock import Mock, patch, MagicMock
from core.error_notifications import (
    ErrorNotificationManager,
    initialize_notification_manager,
    get_notification_manager,
    send_critical_failure_notification,
    send_warning_notification,
    send_info_notification,
    AgenticError
)


class TestErrorNotificationManager:
    """Test suite for ErrorNotificationManager class."""

    def test_init_with_defaults(self):
        """Test initialization with default parameters."""
        manager = ErrorNotificationManager()
        assert manager.smtp_host is None
        assert manager.smtp_port is None
        assert manager.smtp_username is None
        assert manager.smtp_password is None
        assert manager.from_email is None
        assert manager.to_emails == []
        assert manager.notification_commands == []

    def test_init_with_custom_params(self):
        """Test initialization with custom parameters."""
        manager = ErrorNotificationManager(
            smtp_host="smtp.example.com",
            smtp_port=587,
            smtp_username="user",
            smtp_password="pass",
            from_email="sender@example.com",
            to_emails=["recipient1@example.com", "recipient2@example.com"],
            notification_commands=["echo {message}", "logger {message}"]
        )
        assert manager.smtp_host == "smtp.example.com"
        assert manager.smtp_port == 587
        assert manager.smtp_username == "user"
        assert manager.smtp_password == "pass"
        assert manager.from_email == "sender@example.com"
        assert manager.to_emails == ["recipient1@example.com", "recipient2@example.com"]
        assert manager.notification_commands == ["echo {message}", "logger {message}"]

    @patch('smtplib.SMTP')
    def test_send_email_notification_success(self, mock_smtp):
        """Test successful email notification."""
        # Configure mock SMTP
        mock_server = Mock()
        mock_smtp.return_value = mock_server
        
        manager = ErrorNotificationManager(
            smtp_host="smtp.example.com",
            smtp_port=587,
            smtp_username="user",
            smtp_password="pass",
            from_email="sender@example.com",
            to_emails=["recipient@example.com"]
        )
        
        result = manager.send_email_notification("Test Subject", "Test Message")
        
        assert result is True
        mock_smtp.assert_called_once_with("smtp.example.com", 587)
        mock_server.starttls.assert_called_once()
        mock_server.login.assert_called_once_with("user", "pass")
        mock_server.sendmail.assert_called_once()
        mock_server.quit.assert_called_once()

    @patch('smtplib.SMTP')
    def test_send_email_notification_without_auth(self, mock_smtp):
        """Test email notification without authentication."""
        # Configure mock SMTP
        mock_server = Mock()
        mock_smtp.return_value = mock_server
        
        manager = ErrorNotificationManager(
            smtp_host="smtp.example.com",
            smtp_port=587,
            from_email="sender@example.com",
            to_emails=["recipient@example.com"]
        )
        
        result = manager.send_email_notification("Test Subject", "Test Message")
        
        assert result is True
        mock_smtp.assert_called_once_with("smtp.example.com", 587)
        mock_server.starttls.assert_not_called()
        mock_server.login.assert_not_called()
        mock_server.sendmail.assert_called_once()
        mock_server.quit.assert_called_once()

    @patch('smtplib.SMTP')
    def test_send_email_notification_incomplete_config(self, mock_smtp):
        """Test email notification with incomplete configuration."""
        manager = ErrorNotificationManager()
        
        result = manager.send_email_notification("Test Subject", "Test Message")
        
        assert result is False
        mock_smtp.assert_not_called()

    @patch('smtplib.SMTP')
    def test_send_email_notification_smtp_error(self, mock_smtp):
        """Test email notification with SMTP error."""
        # Configure mock SMTP to raise an exception
        mock_smtp.side_effect = smtplib.SMTPException("SMTP error")
        
        manager = ErrorNotificationManager(
            smtp_host="smtp.example.com",
            smtp_port=587,
            from_email="sender@example.com",
            to_emails=["recipient@example.com"]
        )
        
        result = manager.send_email_notification("Test Subject", "Test Message")
        
        assert result is False

    @patch('subprocess.run')
    def test_send_command_notification_success(self, mock_run):
        """Test successful command notification."""
        # Configure mock subprocess
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stderr = ""
        mock_run.return_value = mock_result
        
        manager = ErrorNotificationManager(
            notification_commands=["echo {message}", "logger {message}"]
        )
        
        result = manager.send_command_notification("Test Message")
        
        assert result is True
        assert mock_run.call_count == 2

    @patch('subprocess.run')
    def test_send_command_notification_command_failure(self, mock_run):
        """Test command notification with command failure."""
        # Configure mock subprocess to return non-zero exit code
        mock_result = Mock()
        mock_result.returncode = 1
        mock_result.stderr = "Command failed"
        mock_run.return_value = mock_result
        
        manager = ErrorNotificationManager(
            notification_commands=["echo {message}"]
        )
        
        result = manager.send_command_notification("Test Message")
        
        assert result is False

    @patch('subprocess.run')
    def test_send_command_notification_timeout(self, mock_run):
        """Test command notification with timeout."""
        # Configure mock subprocess to raise TimeoutExpired
        mock_run.side_effect = subprocess.TimeoutExpired("echo {message}", 30)
        
        manager = ErrorNotificationManager(
            notification_commands=["echo {message}"]
        )
        
        result = manager.send_command_notification("Test Message")
        
        assert result is False

    @patch('subprocess.run')
    def test_send_command_notification_no_commands(self, mock_run):
        """Test command notification with no commands configured."""
        manager = ErrorNotificationManager()
        
        result = manager.send_command_notification("Test Message")
        
        assert result is False
        mock_run.assert_not_called()

    @patch.object(ErrorNotificationManager, 'send_email_notification')
    @patch.object(ErrorNotificationManager, 'send_command_notification')
    def test_send_notification(self, mock_send_command, mock_send_email):
        """Test sending notification through all channels."""
        # Configure mocks
        mock_send_email.return_value = True
        mock_send_command.return_value = True
        
        manager = ErrorNotificationManager(
            smtp_host="smtp.example.com",
            smtp_port=587,
            from_email="sender@example.com",
            to_emails=["recipient@example.com"],
            notification_commands=["echo {message}"]
        )
        
        result = manager.send_notification("Test Title", "Test Message", "error")
        
        assert result is True
        mock_send_email.assert_called_once()
        mock_send_command.assert_called_once()

    @patch.object(ErrorNotificationManager, 'send_email_notification')
    @patch.object(ErrorNotificationManager, 'send_command_notification')
    def test_send_notification_partial_success(self, mock_send_command, mock_send_email):
        """Test sending notification with partial success."""
        # Configure mocks - email fails, command succeeds
        mock_send_email.return_value = False
        mock_send_command.return_value = True
        
        manager = ErrorNotificationManager(
            notification_commands=["echo {message}"]
        )
        
        result = manager.send_notification("Test Title", "Test Message", "error")
        
        assert result is True
        mock_send_email.assert_called_once()
        mock_send_command.assert_called_once()

    @patch.object(ErrorNotificationManager, 'send_email_notification')
    @patch.object(ErrorNotificationManager, 'send_command_notification')
    def test_send_notification_all_fail(self, mock_send_command, mock_send_email):
        """Test sending notification with all channels failing."""
        # Configure mocks - both fail
        mock_send_email.return_value = False
        mock_send_command.return_value = False
        
        manager = ErrorNotificationManager()
        
        result = manager.send_notification("Test Title", "Test Message", "error")
        
        assert result is False
        mock_send_email.assert_called_once()
        mock_send_command.assert_called_once()


class TestGlobalNotificationFunctions:
    """Test suite for global notification functions."""

    def test_initialize_and_get_notification_manager(self):
        """Test initializing and getting the notification manager."""
        # Initialize manager
        initialize_notification_manager(
            smtp_host="smtp.example.com",
            smtp_port=587,
            smtp_username="user",
            smtp_password="pass",
            from_email="sender@example.com",
            to_emails=["recipient@example.com"],
            notification_commands=["echo {message}"]
        )
        
        # Get manager
        manager = get_notification_manager()
        assert manager is not None
        assert isinstance(manager, ErrorNotificationManager)
        assert manager.smtp_host == "smtp.example.com"
        assert manager.smtp_port == 587
        assert manager.smtp_username == "user"
        assert manager.smtp_password == "pass"
        assert manager.from_email == "sender@example.com"
        assert manager.to_emails == ["recipient@example.com"]
        assert manager.notification_commands == ["echo {message}"]

    @patch('core.error_notifications.get_notification_manager')
    def test_send_critical_failure_notification_success(self, mock_get_manager):
        """Test successful critical failure notification."""
        # Configure mock manager
        mock_manager = Mock()
        mock_manager.send_notification.return_value = True
        mock_get_manager.return_value = mock_manager
        
        # Create test error
        error = AgenticError("TEST_ERROR", "Test error message")
        
        # Send notification
        result = send_critical_failure_notification("TestComponent", error, {"key": "value"})
        
        assert result is True
        mock_get_manager.assert_called_once()
        mock_manager.send_notification.assert_called_once()

    @patch('core.error_notifications.get_notification_manager')
    def test_send_critical_failure_notification_no_manager(self, mock_get_manager):
        """Test critical failure notification with no manager."""
        mock_get_manager.return_value = None
        
        # Create test error
        error = AgenticError("TEST_ERROR", "Test error message")
        
        # Send notification
        result = send_critical_failure_notification("TestComponent", error)
        
        assert result is False
        mock_get_manager.assert_called_once()

    @patch('core.error_notifications.get_notification_manager')
    def test_send_warning_notification_success(self, mock_get_manager):
        """Test successful warning notification."""
        # Configure mock manager
        mock_manager = Mock()
        mock_manager.send_notification.return_value = True
        mock_get_manager.return_value = mock_manager
        
        # Send notification
        result = send_warning_notification("TestComponent", "Test warning message", {"key": "value"})
        
        assert result is True
        mock_get_manager.assert_called_once()
        mock_manager.send_notification.assert_called_once()

    @patch('core.error_notifications.get_notification_manager')
    def test_send_warning_notification_no_manager(self, mock_get_manager):
        """Test warning notification with no manager."""
        mock_get_manager.return_value = None
        
        # Send notification
        result = send_warning_notification("TestComponent", "Test warning message")
        
        assert result is False
        mock_get_manager.assert_called_once()

    @patch('core.error_notifications.get_notification_manager')
    def test_send_info_notification_success(self, mock_get_manager):
        """Test successful info notification."""
        # Configure mock manager
        mock_manager = Mock()
        mock_manager.send_notification.return_value = True
        mock_get_manager.return_value = mock_manager
        
        # Send notification
        result = send_info_notification("TestComponent", "Test info message", {"key": "value"})
        
        assert result is True
        mock_get_manager.assert_called_once()
        mock_manager.send_notification.assert_called_once()

    @patch('core.error_notifications.get_notification_manager')
    def test_send_info_notification_no_manager(self, mock_get_manager):
        """Test info notification with no manager."""
        mock_get_manager.return_value = None
        
        # Send notification
        result = send_info_notification("TestComponent", "Test info message")
        
        assert result is False
        mock_get_manager.assert_called_once()