"""
OIDC service for eduIDM application.
Handles OIDC flow completion and user data processing.
"""

from datetime import datetime
from session_manager import session_manager
from storage import load_storage, save_storage, find_invitation_by_hash
from oidc import get_userinfo
from utils.logging import logger


def complete_oidc_flow():
    """Complete OIDC flow after successful authentication"""
    logger.info("Completing OIDC flow after successful authentication")

    # Get session state
    session_state = session_manager.session_state

    # Get userinfo
    logger.debug("Retrieving user info from OIDC provider")
    userinfo = get_userinfo(session_state)
    if userinfo:
        logger.info(f"User info retrieved successfully for user: {userinfo.get('sub', 'unknown')}")

        # Get current session state
        state = session_manager.state

        # Mark steps as completed
        state['steps_completed']['eduid_login'] = True
        state['steps_completed']['attributes_verified'] = True
        logger.info("Marked eduid_login and attributes_verified steps as completed")

        # Store eduID user info
        state['eduid_userinfo'] = userinfo
        logger.debug("Stored eduID user info in session state")

        # Update storage with completion
        current_hash = state['hash']
        if current_hash:
            logger.debug(f"Updating storage for hash: {current_hash}")
            storage_data = load_storage()
            invitation = find_invitation_by_hash(storage_data, current_hash)
            if invitation and not invitation.get('datetime_accepted'):
                invitation['datetime_accepted'] = datetime.utcnow().isoformat() + 'Z'
                logger.info(f"Set acceptance timestamp for guest_id: {invitation.get('guest_id')}")

                # Store eduID attributes directly in invitation record
                # Extract eduperson_principal_name and store as eppn
                userinfo_copy = userinfo.copy()
                eppn = userinfo_copy.pop('eduperson_principal_name', '')
                invitation['eppn'] = eppn
                invitation['eduid_props'] = userinfo_copy
                logger.info(f"Stored eduID properties for guest_id: {invitation.get('guest_id')}, eppn: {eppn}")

                save_storage(storage_data)
                state['steps_completed']['completed'] = True
                # Set flag to show SCIM dialog on accept page
                state['show_scim_dialog'] = True
                logger.info("OIDC flow completed successfully, all steps marked as done")
            else:
                logger.warning(f"Invitation already accepted or not found for hash: {current_hash}")
        else:
            logger.warning("No current hash found in user state during OIDC completion")
    else:
        logger.error("Failed to retrieve user info from OIDC provider")
