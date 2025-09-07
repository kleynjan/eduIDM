# eduID integratie: OIDC -> app

import json
from datetime import datetime
from typing import Dict, Any, Optional
from .oidc_protocol import generate_pkce, build_auth_url, exchange_code, get_userinfo, load_well_known_config
from services.storage import load_storage, save_storage, find_invitation_by_code
from utils.logging import logger

def load_eduid_config() -> Dict[str, Any]:
    with open('config.json', 'r') as f:
        config = json.load(f)

    # load .well-known configuration
    well_known_config = load_well_known_config(config['DOTWELLKNOWN'])
    config.update(well_known_config)

    return config


def start_eduid_login(user_state: Dict[str, Any]) -> None:
    """
    Initiate eduID OIDC login flow and redirect to authorization server.

    Args:
        user_state: User state dictionary (app.storage.user)
    """
    from nicegui import ui

    logger.info("Starting eduID login process")
    config = load_eduid_config()

    try:
        # Generate PKCE parameters
        code_verifier, code_challenge = generate_pkce()
        logger.debug(f"Generated PKCE with code_verifier: {code_verifier[:10]}...")

        # Store code_verifier in user state under eduid_oidc namespace
        user_state['eduid_oidc'] = {'code_verifier': code_verifier}

        # Build authorization URL
        auth_url = build_auth_url(
            authorization_endpoint=config['authorization_endpoint'],
            client_id=config['CLIENT_ID'],
            redirect_uri=config['REDIRECT_URI'],
            code_challenge=code_challenge
        )

        logger.info(f"Authorization URL generated successfully, redirecting to: {auth_url}")
        # Redirect to OIDC provider
        ui.navigate.to(auth_url, new_tab=False)
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Failed to generate authorization URL. Error: {error_msg}")
        ui.notify(f'OIDC Error: {error_msg}', type='negative')


def complete_eduid_login(code: str, user_state: Dict[str, Any]) -> tuple[Dict[str, Any], Dict[str, Any]]:
    """
    Complete eduID OIDC login flow.

    Args:
        code: authorization code from callback
        user_state: User state dictionary (app.storage.user)

    Returns:
        Tuple of (token_data, userinfo)
    """
    logger.info("Completing eduID OIDC flow")

    # Retrieve code_verifier from user state
    if 'eduid_oidc' not in user_state or 'code_verifier' not in user_state['eduid_oidc']:
        raise Exception("No code_verifier found - login session may have expired")

    code_verifier = user_state['eduid_oidc']['code_verifier']
    logger.debug(f"Retrieved code_verifier: {code_verifier[:10]}...")

    # Clean up OIDC state after retrieving
    del user_state['eduid_oidc']

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
    logger.debug(f"Token exchange successful, token data: {token_data}")

    logger.debug("Retrieving user info from eduID")
    userinfo = get_userinfo(
        userinfo_endpoint=config['userinfo_endpoint'],
        token_data=token_data
    )
    logger.info(f"User info retrieved successfully for user: {userinfo.get('sub', '')}")

    return token_data, userinfo


def process_eduid_completion(userinfo: Dict[str, Any], user_state: Dict[str, Any]) -> None:
    """
    Update application state after successful eduid login.

    Args:
        userinfo: User information from eduID
        user_state: User state dictionary from session manager
    """
    logger.info("Updating application state with eduID user info")

    user_state['steps_completed']['eduid_login'] = True
    user_state['eduid_userinfo'] = userinfo

    # to do: check other attributes, eg affiliation, MFA -- for now mark as complete
    user_state['steps_completed']['attributes_verified'] = True

    # Update storage with completion
    current_invite_code = user_state['invite_code']
    if current_invite_code:
        logger.debug(f"Updating storage for invite_code: {current_invite_code}")
        storage_data = load_storage()
        invitation = find_invitation_by_code(storage_data, current_invite_code)
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
            logger.warning(f"Invitation already accepted or not found for invite_code: {current_invite_code}")
    else:
        logger.warning("No current invite_code found in user state during eduID completion")


# Note: These functions are no longer needed since we don't maintain OIDC state
# The application only stores the final userinfo result
