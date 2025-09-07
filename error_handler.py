"""
Error handling utilities for eduIDM application.
Provides consistent error handling and user notification patterns.
"""

from typing import Optional
from nicegui import ui
from utils.logging import logger


def handle_error(error_msg: str, error_type: str = "error", notify_user: bool = True,
                 notification_type: str = "negative") -> None:
    """
    Handle errors consistently across the application

    Args:
        error_msg: The error message to log and optionally display
        error_type: Type of error for logging context
        notify_user: Whether to show a notification to the user
        notification_type: Type of notification (negative, warning, info)
    """
    logger.error(f"{error_type}: {error_msg}")

    if notify_user:
        ui.notify(error_msg, type=notification_type)  # type: ignore


def handle_oidc_error(error_msg: str, session_state: dict, notify_user: bool = True) -> None:
    """
    Handle OIDC-specific errors

    Args:
        error_msg: The error message
        session_state: Session state to store error in
        notify_user: Whether to notify the user
    """
    # Store error in session state
    if 'oidc' not in session_state:
        session_state['oidc'] = {}
    session_state['oidc']['error'] = error_msg

    # Log and optionally notify
    handle_error(f"OIDC Error: {error_msg}", "OIDC", notify_user)


def clear_oidc_error(session_state: dict) -> None:
    """Clear OIDC error from session state"""
    if 'oidc' in session_state:
        session_state['oidc']['error'] = None


def get_oidc_error(session_state: dict) -> Optional[str]:
    """Get current OIDC error if any"""
    if 'oidc' in session_state:
        return session_state['oidc']['error'] if 'error' in session_state['oidc'] else None
    return None
