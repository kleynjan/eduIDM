# eduID integratie: OIDC -> app

import json
from typing import Any, Dict, Optional

from nicegui import ui

from services.logging import logger
from services.session_manager import session_manager
from services.storage import update_invitation

from .oidc_protocol import (
    build_auth_url,
    exchange_code,
    generate_pkce,
    get_userinfo,
    load_well_known_config,
)


def load_eduid_config() -> Dict[str, Any]:
    with open('config.json', 'r') as f:
        config = json.load(f)

    # load .well-known configuration
    well_known_config = load_well_known_config(config['DOTWELLKNOWN'])
    config.update(well_known_config)

    return config


def start_oidc_login(user_state: Dict[str, Any], login_hint: Optional[str] = None, acr_values: Optional[str] = None, force_login: bool = False):
    """
    Initiate OIDC login flow and redirect to authorization server.

    Args:
        user_state: dictionary to carry oidc state data
        login_hint: login hint for directing authentication to specific identity provider
        acr_values: optional ACR values to request specific authentication strength
        force_login: whether to force re-authentication (prompt=login)
    """

    hint_info = f" with login_hint: {login_hint}" if login_hint else ""
    acr_info = f" with ACR: {acr_values}" if acr_values else ""
    force_info = " (force_login=True)" if force_login else ""
    logger.info(f"Starting OIDC login process{hint_info}{acr_info}{force_info}")
    config = load_eduid_config()

    try:
        # Generate PKCE parameters
        code_verifier, code_challenge = generate_pkce()
        logger.debug(f"Generated PKCE with code_verifier: {code_verifier[:10]}...")

        # Store code_verifier in user state under eduid_oidc namespace
        user_state['eduid_oidc'] = {'code_verifier': code_verifier}

        # Build authorization URL
        prompt = "login" if force_login else None

        auth_url = build_auth_url(
            authorization_endpoint=config['authorization_endpoint'],
            client_id=config['CLIENT_ID'],
            redirect_uri=config['REDIRECT_URI'],
            code_challenge=code_challenge,
            acr_values=acr_values,
            prompt=prompt,
            login_hint=login_hint
        )

        logger.info(f"Authorization URL generated successfully, redirecting to: {auth_url}")
        # Redirect to OIDC provider
        ui.navigate.to(auth_url, new_tab=False)
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Failed to generate authorization URL. Error: {error_msg}")
        ui.notify(f'OIDC Error: {error_msg}', type='negative')


def complete_eduid_login(code: str, user_state: Dict[str, Any]):
    """
    Complete eduID OIDC login flow and update application state.

    Args:
        code: authorization code from callback
        user_state: dictionary to carry oidc state data
    """
    logger.info("Completing eduID OIDC flow")

    # retrieve code_verifier from user state
    if 'eduid_oidc' not in user_state or 'code_verifier' not in user_state['eduid_oidc']:
        raise Exception("No code_verifier found - login session may have expired")

    code_verifier = user_state['eduid_oidc']['code_verifier']
    logger.debug(f"Retrieved code_verifier: {code_verifier[:10]}...")

    # clean up OIDC state after retrieving
    del user_state['eduid_oidc']

    config = load_eduid_config()

    # exchange code for token
    logger.debug("Exchanging authorization code for access token")
    token_data = exchange_code(
        token_endpoint=config['token_endpoint'],
        client_id=config['CLIENT_ID'],
        client_secret=config['CLIENT_SECRET'],
        redirect_uri=config['REDIRECT_URI'],
        code=code,
        code_verifier=code_verifier
    )

    # getting userinfo
    logger.debug("Retrieving user info from eduID")
    userinfo = get_userinfo(
        userinfo_endpoint=config['userinfo_endpoint'],
        token_data=token_data
    )
    logger.info(f"User info retrieved successfully for user: {userinfo.get('sub', '')}")

    # update onboarding state
    onboarding_state = session_manager.state
    onboarding_state['eduid_userinfo'] = userinfo

    if onboarding_state['steps_completed']['eduid_login']:
        # This is step 3 - institutional login
        onboarding_state['steps_completed']['mfa_verified'] = True
        onboarding_state['steps_completed']['completed'] = True
    else:
        # This is step 2 - eduID login
        onboarding_state['steps_completed']['eduid_login'] = True

    # update invitation
    current_invite_code = onboarding_state.get('invite_code')
    if current_invite_code:
        logger.debug(f"Updating storage for invite_code: {current_invite_code}")

        userinfo_copy = userinfo.copy()
        eppn = userinfo_copy.pop('eduperson_principal_name', '')

        success = update_invitation(
            current_invite_code,
            eppn=eppn,
            eduid_props=userinfo_copy
        )
        if success:
            logger.info(f"eduID login for eppn: {eppn} completed successfully")
        else:
            logger.error(f"Failed to update invitation for invite_code: {current_invite_code}")
    else:
        logger.warning("No current invite_code found in onboarding state during eduID completion")


def start_eduid_login(user_state: Dict[str, Any], acr_values: Optional[str] = None, force_login: bool = False):
    """Backward compatibility wrapper for start_oidc_login with eduID hint"""
    return start_oidc_login(user_state, login_hint="https://login.test.eduid.nl", acr_values=acr_values, force_login=force_login)
