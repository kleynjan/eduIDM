import base64
import hashlib
import json
import os
import re
import requests
from typing import Dict, Any, Optional, Tuple
from nicegui import app
from utils.logging import logger

def get_code_challenge() -> Tuple[str, str]:
    """Generate PKCE code verifier and challenge"""
    code_verifier = base64.urlsafe_b64encode(os.urandom(40)).decode('utf-8')
    code_verifier = re.sub('[^a-zA-Z0-9]+', '', code_verifier)
    code_challenge = hashlib.sha256(code_verifier.encode('utf-8')).digest()
    code_challenge = base64.urlsafe_b64encode(code_challenge).decode('utf-8')
    code_challenge = code_challenge.replace('=', '')
    return code_verifier, code_challenge

def load_oidc_config() -> Dict[str, Any]:
    """Load OIDC configuration from config.json and .well-known endpoint"""
    try:
        with open('config.json', 'r') as f:
            config = json.load(f)

        # Get .well-known configuration
        well_known_url = config.get('DOTWELLKNOWN')
        if well_known_url:
            response = requests.get(well_known_url)
            if response.status_code == 200:
                well_known_config = response.json()
                config.update(well_known_config)

        return config
    except Exception as e:
        print(f"Error loading OIDC config: {e}")
        return {}

def initialize_oidc_state(session_state: Dict[str, Any]):
    """Initialize OIDC state in session state dictionary"""
    if 'oidc' not in session_state:
        code_verifier, code_challenge = get_code_challenge()
        session_state['oidc'] = {
            'code_verifier': code_verifier,
            'code_challenge': code_challenge,
            'access_token': None,
            'userinfo': None,
            'error': None
        }
        logger.debug(f"Initialized new OIDC state with code_verifier: {code_verifier[:10]}...")
    # Don't regenerate if already exists - preserve PKCE state across redirects
    elif not session_state['oidc'].get('code_verifier'):
        # Only regenerate if somehow missing
        code_verifier, code_challenge = get_code_challenge()
        session_state['oidc']['code_verifier'] = code_verifier
        session_state['oidc']['code_challenge'] = code_challenge
        logger.debug(f"Regenerated missing code_verifier: {code_verifier[:10]}...")

def get_auth_url(session_state: Dict[str, Any]) -> Optional[str]:
    """Generate authorization URL for OIDC flow"""
    try:
        config = load_oidc_config()
        initialize_oidc_state(session_state)

        auth_endpoint = config.get('authorization_endpoint')
        if not auth_endpoint:
            return None

        params = {
            "response_type": "code",
            "client_id": config.get('CLIENT_ID'),
            "scope": "openid profile email",
            "redirect_uri": config.get('REDIRECT_URI'),
            "code_challenge": session_state['oidc']['code_challenge'],
            "code_challenge_method": "S256",
        }

        # Build URL manually to avoid redirect
        param_string = "&".join([f"{k}={requests.utils.quote(str(v))}" for k, v in params.items()])
        auth_url = f"{auth_endpoint}?{param_string}"
        logger.debug(f"Generated authorization URL for endpoint: {auth_endpoint}")
        return auth_url

    except Exception as e:
        error_msg = f"Error generating auth URL: {str(e)}"
        logger.error(error_msg)
        if 'oidc' not in session_state:
            session_state['oidc'] = {}
        session_state['oidc']['error'] = error_msg
        return None

def get_access_token(code: str, session_state: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Exchange authorization code for access token"""
    try:
        config = load_oidc_config()

        token_endpoint = config.get('token_endpoint')
        if not token_endpoint:
            return None

        # Check if we have OIDC state
        if 'oidc' not in session_state:
            session_state['oidc'] = {'error': "No OIDC state found during token exchange"}
            return None

        code_verifier = session_state['oidc'].get('code_verifier')
        if not code_verifier:
            session_state['oidc']['error'] = "No code_verifier found in OIDC state"
            return None

        # Debug: Log code_verifier (first 10 chars for security)
        logger.debug(f"Using code_verifier: {code_verifier[:10]}...")

        token_params = {
            'grant_type': 'authorization_code',
            'code': code,
            'client_id': config.get('CLIENT_ID'),
            'client_secret': config.get('CLIENT_SECRET'),
            'redirect_uri': config.get('REDIRECT_URI'),
            'code_verifier': code_verifier,
        }

        logger.debug(f"Token request to {token_endpoint}")
        logger.debug(
            f"Token params: {dict((k, v[:10] + '...' if len(str(v)) > 10 else v) for k, v in token_params.items())}")

        response = requests.post(token_endpoint, data=token_params)
        if response.status_code != 200:
            error_msg = f"Token request failed: {response.status_code} - {response.text}"
            logger.error(error_msg)
            session_state['oidc']['error'] = error_msg
            return None

        token_data = response.json()
        session_state['oidc']['access_token'] = token_data
        logger.info("Token exchange successful")
        return token_data

    except Exception as e:
        error_msg = f"Error getting access token: {str(e)}"
        logger.error(error_msg)
        session_state['oidc']['error'] = error_msg
        return None

def get_userinfo(session_state: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Get user information using access token"""
    try:
        if not is_logged_in(session_state):
            return None

        config = load_oidc_config()
        userinfo_endpoint = config.get('userinfo_endpoint')
        if not userinfo_endpoint:
            return None

        # Use the entire access_token object as data, matching Flask example
        access_token = session_state['oidc']['access_token']
        response = requests.post(userinfo_endpoint, data=access_token)
        if response.status_code != 200:
            error_msg = f"Userinfo request failed: {response.status_code} - {response.text}"
            session_state['oidc']['error'] = error_msg
            return None

        userinfo = response.json()
        session_state['oidc']['userinfo'] = userinfo
        logger.info(f"Retrieved userinfo for user: {userinfo.get('sub', 'unknown')}")
        return userinfo

    except Exception as e:
        error_msg = f"Error getting userinfo: {str(e)}"
        logger.error(error_msg)
        session_state['oidc']['error'] = error_msg
        return None

def is_logged_in(session_state: Dict[str, Any]) -> bool:
    """Check if user is logged in via OIDC"""
    return (
        'oidc' in session_state and
        session_state['oidc'].get('access_token') is not None
    )


def get_oidc_error(session_state: Dict[str, Any]) -> Optional[str]:
    """Get current OIDC error if any"""
    if 'oidc' in session_state:
        return session_state['oidc'].get('error')
    return None

def clear_oidc_error(session_state: Dict[str, Any]):
    """Clear OIDC error"""
    if 'oidc' in session_state:
        session_state['oidc']['error'] = None
