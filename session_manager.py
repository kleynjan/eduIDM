"""
Session state management utilities for eduIDM application.
Provides a singleton session manager that works with NiceGUI reactive binding.
"""

import uuid
from typing import Dict, Any
from nicegui import app
from services.storage import load_storage, find_invitation_by_hash, find_group_by_id
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
        return self._server_session_key

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
                    'hash': '',
                    'group_name': 'Unknown Group',
                    'steps_completed': {
                        'code_entered': False,
                        'eduid_login': False,
                        'attributes_verified': False,
                        'completed': False
                    },
                    'hash_input': ''
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

    def update_state_from_hash(self, hash_param: str = None) -> None:
        """Update state based on hash parameter"""
        logger.debug(f"Updating state from hash parameter: {hash_param}")
        storage_data = load_storage()
        state = self.state
        current_hash = hash_param or state.get('hash', '')

        if current_hash:
            logger.debug(f"Processing hash: {current_hash}")
            invitation = find_invitation_by_hash(storage_data, current_hash)
            if invitation:
                logger.info(f"Found invitation for hash {current_hash}: guest_id={invitation.get('guest_id')}")
                group = find_group_by_id(storage_data, invitation.get('group_id'))
                if group:
                    group_name = group.get('name', 'Unknown Group')
                    state['group_name'] = group_name
                    state['redirect_url'] = group.get('redirect_url', 'https://canvas.uva.nl/')
                    state['redirect_text'] = group.get('redirect_text', 'Canvas (UvA)')
                    logger.info(f"Updated group info: {group_name}, redirect: {state['redirect_text']}")
                state['hash'] = current_hash
                state['steps_completed']['code_entered'] = True
                logger.info(f"Hash validation successful, code_entered step marked as completed")
            else:
                logger.warning(f"No guest group found for hash: {current_hash}")
        else:
            logger.debug("No hash provided, skipping state update")


# Create singleton instance
session_manager = SessionManager()
