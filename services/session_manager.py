"""
Session state management utilities for eduIDM application.
Provides a singleton session manager that works with NiceGUI reactive binding.
"""

import uuid
from typing import Dict, Any
from nicegui import app
from utils.logging import logger


class SessionManager:
    """Singleton session manager that maintains server session key and provides utilities"""

    _instance = None
    _server_session_key = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._server_session_key = str(uuid.uuid4())
        return cls._instance

    @property
    def server_session_key(self) -> str:
        """Get the current server session key"""
        return self._server_session_key  # type: ignore

    @property
    def session_state(self) -> Dict[str, Any]:
        """Get the current session state (direct access for reactive binding)"""
        return app.storage.user.get(self._server_session_key, {})

    @property
    def state(self) -> Dict[str, Any]:
        """Get the user state portion (direct access for reactive binding)"""
        return self.session_state.get('state', {})

    def initialize_user_state(self) -> None:
        """Initialize user state if it doesn't exist"""
        if self._server_session_key not in app.storage.user:
            logger.debug(f"Initializing new user state for server session: {self._server_session_key}")
            app.storage.user[self._server_session_key] = {
                'state': {
                    'invite_code': '',
                    'group_name': '',
                    'steps_completed': {
                        'code_entered': False,
                        'eduid_login': False,
                        'attributes_verified': False,
                        'completed': False
                    },
                    'invite_code_input': ''
                }
            }
            logger.info(f"User state initialized successfully for server session: {self._server_session_key}")
        else:
            logger.debug(f"User state already exists for current server session: {self._server_session_key}")

        self._cleanup_old_sessions()

    def _cleanup_old_sessions(self) -> None:
        """Clean up old session data"""
        sessions_to_remove = []
        for key in app.storage.user.keys():
            if key.startswith('session_') and key != self._server_session_key:
                sessions_to_remove.append(key)

        for old_session in sessions_to_remove:
            del app.storage.user[old_session]
            logger.debug(f"Cleaned up old session: {old_session}")


# Create singleton instance
session_manager = SessionManager()
