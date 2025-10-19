"""
Error notification system for the agentic system.
"""

import logging
import smtplib
import subprocess
from typing import Dict, Any, Optional, List
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from .exceptions import AgenticError


class ErrorNotificationManager:
    """Manager for sending error notifications."""
    
    def __init__(
        self,
        smtp_host: Optional[str] = None,
        smtp_port: Optional[int] = None,
        smtp_username: Optional[str] = None,
        smtp_password: Optional[str] = None,
        from_email: Optional[str] = None,
        to_emails: Optional[List[str]] = None,
        notification_commands: Optional[List[str]] = None
    ):
        """
        Initialize the error notification manager.
        
        Args:
            smtp_host: SMTP server host
            smtp_port: SMTP server port
            smtp_username: SMTP username
            smtp_password: SMTP password
            from_email: Sender email address
            to_emails: List of recipient email addresses
            notification_commands: List of shell commands to execute for notifications
        """
        self.smtp_host = smtp_host
        self.smtp_port = smtp_port
        self.smtp_username = smtp_username
        self.smtp_password = smtp_password
        self.from_email = from_email
        self.to_emails = to_emails or []
        self.notification_commands = notification_commands or []
        self.logger = logging.getLogger("error_notifications")
    
    def send_email_notification(self, subject: str, message: str) -> bool:
        """
        Send an email notification.
        
        Args:
            subject: The email subject
            message: The email message
            
        Returns:
            True if the email was sent successfully, False otherwise
        """
        # Check if email configuration is available
        if not all([self.smtp_host, self.smtp_port, self.from_email, self.to_emails]):
            self.logger.warning("Email notification configuration is incomplete")
            return False
        
        try:
            # Create message
            msg = MIMEMultipart()
            msg['From'] = self.from_email
            msg['To'] = ', '.join(self.to_emails)
            msg['Subject'] = subject
            
            # Add message body
            msg.attach(MIMEText(message, 'plain'))
            
            # Connect to SMTP server and send email
            server = smtplib.SMTP(self.smtp_host, self.smtp_port)
            if self.smtp_username and self.smtp_password:
                server.starttls()
                server.login(self.smtp_username, self.smtp_password)
            
            text = msg.as_string()
            server.sendmail(self.from_email, self.to_emails, text)
            server.quit()
            
            self.logger.info(f"Email notification sent: {subject}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to send email notification: {e}")
            return False
    
    def send_command_notification(self, message: str) -> bool:
        """
        Send a notification via shell commands.
        
        Args:
            message: The notification message
            
        Returns:
            True if the commands were executed successfully, False otherwise
        """
        if not self.notification_commands:
            self.logger.warning("No notification commands configured")
            return False
        
        success = True
        for command in self.notification_commands:
            try:
                # Replace {message} placeholder with actual message
                formatted_command = command.format(message=message)
                result = subprocess.run(
                    formatted_command,
                    shell=True,
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                if result.returncode != 0:
                    self.logger.error(
                        f"Notification command failed: {formatted_command} "
                        f"Error: {result.stderr}"
                    )
                    success = False
                else:
                    self.logger.info(f"Notification command executed: {formatted_command}")
            except subprocess.TimeoutExpired:
                self.logger.error(f"Notification command timed out: {command}")
                success = False
            except Exception as e:
                self.logger.error(f"Failed to execute notification command {command}: {e}")
                success = False
        
        return success
    
    def send_notification(self, title: str, message: str, severity: str = "error") -> bool:
        """
        Send a notification through all configured channels.
        
        Args:
            title: The notification title
            message: The notification message
            severity: The severity level (error, warning, info)
            
        Returns:
            True if at least one notification channel succeeded, False otherwise
        """
        full_message = f"[{severity.upper()}] {title}\n\n{message}"
        email_subject = f"[{severity.upper()}] {title}"
        
        # Send email notification
        email_success = self.send_email_notification(email_subject, full_message)
        
        # Send command notification
        command_success = self.send_command_notification(full_message)
        
        # Return success if at least one channel succeeded
        return email_success or command_success


# Global instance
_notification_manager: Optional[ErrorNotificationManager] = None


def initialize_notification_manager(
    smtp_host: Optional[str] = None,
    smtp_port: Optional[int] = None,
    smtp_username: Optional[str] = None,
    smtp_password: Optional[str] = None,
    from_email: Optional[str] = None,
    to_emails: Optional[List[str]] = None,
    notification_commands: Optional[List[str]] = None
):
    """
    Initialize the global notification manager.
    
    Args:
        smtp_host: SMTP server host
        smtp_port: SMTP server port
        smtp_username: SMTP username
        smtp_password: SMTP password
        from_email: Sender email address
        to_emails: List of recipient email addresses
        notification_commands: List of shell commands to execute for notifications
    """
    global _notification_manager
    _notification_manager = ErrorNotificationManager(
        smtp_host=smtp_host,
        smtp_port=smtp_port,
        smtp_username=smtp_username,
        smtp_password=smtp_password,
        from_email=from_email,
        to_emails=to_emails,
        notification_commands=notification_commands
    )


def get_notification_manager() -> Optional[ErrorNotificationManager]:
    """
    Get the global notification manager instance.
    
    Returns:
        The notification manager instance, or None if not initialized
    """
    global _notification_manager
    return _notification_manager


def send_critical_failure_notification(
    component: str,
    error: Exception,
    context: Optional[Dict[str, Any]] = None
) -> bool:
    """
    Send a critical failure notification.
    
    Args:
        component: The component where the error occurred
        error: The error that occurred
        context: Additional context information
        
    Returns:
        True if the notification was sent successfully, False otherwise
    """
    manager = get_notification_manager()
    if not manager:
        logging.warning("Notification manager not initialized")
        return False
    
    # Create notification content
    title = f"Critical Failure in {component}"
    
    message_parts = [
        f"Component: {component}",
        f"Error Type: {type(error).__name__}",
        f"Error Message: {str(error)}",
    ]
    
    # Add context information if available
    if context:
        message_parts.append("Context:")
        for key, value in context.items():
            message_parts.append(f"  {key}: {value}")
    
    # Add error details if it's an AgenticError
    if isinstance(error, AgenticError):
        message_parts.append(f"Error Code: {error.error_code}")
        if hasattr(error, 'details') and error.details:
            message_parts.append("Error Details:")
            for key, value in error.details.items():
                message_parts.append(f"  {key}: {value}")
    
    message = "\n".join(message_parts)
    
    # Send notification
    return manager.send_notification(title, message, "error")


def send_warning_notification(
    component: str,
    message: str,
    context: Optional[Dict[str, Any]] = None
) -> bool:
    """
    Send a warning notification.
    
    Args:
        component: The component where the warning occurred
        message: The warning message
        context: Additional context information
        
    Returns:
        True if the notification was sent successfully, False otherwise
    """
    manager = get_notification_manager()
    if not manager:
        logging.warning("Notification manager not initialized")
        return False
    
    # Create notification content
    title = f"Warning from {component}"
    
    message_parts = [
        f"Component: {component}",
        f"Message: {message}",
    ]
    
    # Add context information if available
    if context:
        message_parts.append("Context:")
        for key, value in context.items():
            message_parts.append(f"  {key}: {value}")
    
    full_message = "\n".join(message_parts)
    
    # Send notification
    return manager.send_notification(title, full_message, "warning")


def send_info_notification(
    component: str,
    message: str,
    context: Optional[Dict[str, Any]] = None
) -> bool:
    """
    Send an info notification.
    
    Args:
        component: The component where the info occurred
        message: The info message
        context: Additional context information
        
    Returns:
        True if the notification was sent successfully, False otherwise
    """
    manager = get_notification_manager()
    if not manager:
        logging.warning("Notification manager not initialized")
        return False
    
    # Create notification content
    title = f"Info from {component}"
    
    message_parts = [
        f"Component: {component}",
        f"Message: {message}",
    ]
    
    # Add context information if available
    if context:
        message_parts.append("Context:")
        for key, value in context.items():
            message_parts.append(f"  {key}: {value}")
    
    full_message = "\n".join(message_parts)
    
    # Send notification
    return manager.send_notification(title, full_message, "info")