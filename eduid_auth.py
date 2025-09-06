"""
eduID authentication integration.
Handles eduID-specific OIDC flow and business logic.
"""

import json
from datetime import datetime
from typing import Dict, Any, Optional
from oidc_client import generate_pkce, build_auth_url, exchange_code, get_userinfo, load_well_known_config
from storage import load_storage, save_storage, find_invitation_by_hash
from utils.logging import logger


def load_eduid_config() -> Dict[str, Any]:
    """Load eduID OIDC configuration"""
    with open('eduid_oidc_config.json', 'r') as f:
        config = json.load(f)

    # Load .well-known configuration
    well_known_config = load_well_known_config(config['DOTWELLKNOWN'])
    config.update(well_known_config)

    return config


def start_eduid_login(session_state: Dict[str, Any]) -> str:
    """
    Start eduID OIDC login flow.

    Args:
        session_state: Session state dictionary

    Returns:
        Authorization URL to redirect to

    Raises:
        Exception: If configuration or URL generation fails
    """
    logger.info("Starting eduID login process via OIDC")

    # Initialize OIDC state
    code_verifier, code_challenge = generate_pkce()
    session_state['oidc'] = {
        'code_verifier': code_verifier,
        'code_challenge': code_challenge,
        'access_token': None,
        'userinfo': None,
        'error': None
    }
    logger.debug(f"Initialized OIDC state with code_verifier: {code_verifier[:10]}...")

    # Load eduID config
    config = load_eduid_config()

    # Build authorization URL
    auth_url = build_auth_url(
        authorization_endpoint=config['authorization_endpoint'],
        client_id=config['CLIENT_ID'],
        redirect_uri=config['REDIRECT_URI'],
        code_challenge=code_challenge
    )

    logger.info(f"Authorization URL generated successfully: {auth_url}")
    return auth_url


def complete_eduid_login(code: str, session_state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Complete eduID OIDC login flow.

    Args:
        code: Authorization code from callback
        session_state: Session state dictionary

    Returns:
        User information from eduID

    Raises:
        Exception: If token exchange or userinfo retrieval fails
    """
    logger.info("Completing eduID OIDC flow")

    # Check OIDC state
    if 'oidc' not in session_state:
        raise Exception("No OIDC state found during token exchange")

    code_verifier = session_state['oidc']['code_verifier']
    if not code_verifier:
        raise Exception("No code_verifier found in OIDC state")

    logger.debug(f"Using code_verifier: {code_verifier[:10]}...")

    # Load eduID config
    config = load_eduid_config()

    # Exchange code for token
    logger.debug("Exchanging authorization code for access token")
    token_data = exchange_code(
        token_endpoint=config['token_endpoint'],
        client_id=config['CLIENT_ID'],
        client_secret=config['CLIENT_SECRET'],
        redirect_uri=config['REDIRECT_URI'],
        code=code,
        code_verifier=code_verifier
    )

    session_state['oidc']['access_token'] = token_data
    logger.info("Token exchange successful")

    # Get user info
    logger.debug("Retrieving user info from eduID")
    userinfo = get_userinfo(
        userinfo_endpoint=config['userinfo_endpoint'],
        token_data=token_data
    )

    session_state['oidc']['userinfo'] = userinfo
    logger.info(f"User info retrieved successfully for user: {userinfo['sub']}")

    return userinfo


def process_eduid_completion(session_state: Dict[str, Any], user_state: Dict[str, Any]) -> None:
    """
    Process eduID login completion and update application state.

    Args:
        session_state: Session state dictionary
        user_state: User state dictionary from session manager
    """
    logger.info("Processing eduID login completion")

    userinfo = session_state['oidc']['userinfo']
    if not userinfo:
        raise Exception("No userinfo available")

    # Mark steps as completed
    user_state['steps_completed']['eduid_login'] = True
    user_state['steps_completed']['attributes_verified'] = True
    logger.info("Marked eduid_login and attributes_verified steps as completed")

    # Store eduID user info
    user_state['eduid_userinfo'] = userinfo
    logger.debug("Stored eduID user info in user state")

    # Update storage with completion
    current_hash = user_state['hash']
    if current_hash:
        logger.debug(f"Updating storage for hash: {current_hash}")
        storage_data = load_storage()
        invitation = find_invitation_by_hash(storage_data, current_hash)
        if invitation and not invitation.get('datetime_accepted'):
            invitation['datetime_accepted'] = datetime.utcnow().isoformat() + 'Z'
            logger.info(f"Set acceptance timestamp for guest_id: {invitation['guest_id']}")

            # Store eduID attributes directly in invitation record
            # Extract eduperson_principal_name and store as eppn
            userinfo_copy = userinfo.copy()
            eppn = userinfo_copy.pop('eduperson_principal_name', '')
            invitation['eppn'] = eppn
            invitation['eduid_props'] = userinfo_copy
            logger.info(f"Stored eduID properties for guest_id: {invitation['guest_id']}, eppn: {eppn}")

            save_storage(storage_data)
            user_state['steps_completed']['completed'] = True
            # Set flag to show SCIM dialog on accept page
            user_state['show_scim_dialog'] = True
            logger.info("eduID flow completed successfully, all steps marked as done")
        else:
            logger.warning(f"Invitation already accepted or not found for hash: {current_hash}")
    else:
        logger.warning("No current hash found in user state during eduID completion")


def is_logged_in(session_state: Dict[str, Any]) -> bool:
    """Check if user is logged in via eduID OIDC"""
    return (
        'oidc' in session_state and
        session_state['oidc']['access_token'] is not None
    )


def get_oidc_error(session_state: Dict[str, Any]) -> Optional[str]:
    """Get current OIDC error if any"""
    if 'oidc' in session_state:
        return session_state['oidc']['error']
    return None


def clear_oidc_error(session_state: Dict[str, Any]) -> None:
    """Clear OIDC error"""
    if 'oidc' in session_state:
        session_state['oidc']['error'] = None
