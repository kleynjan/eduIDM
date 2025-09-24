"""
Pure OIDC client implementation.
Generic OIDC protocol functions with no application-specific logic.
"""

import base64
import hashlib
import os
import re
import requests
from typing import Dict, Any, Tuple, Optional


def generate_pkce() -> Tuple[str, str]:
    """
    Generate PKCE code_verifier and code_challenge.

    Returns:
        Tuple[code_verifier, code_challenge]
    """
    code_verifier = base64.urlsafe_b64encode(os.urandom(40)).decode('utf-8')
    code_verifier = re.sub('[^a-zA-Z0-9]+', '', code_verifier)
    code_challenge = hashlib.sha256(code_verifier.encode('utf-8')).digest()
    code_challenge = base64.urlsafe_b64encode(code_challenge).decode('utf-8')
    code_challenge = code_challenge.replace('=', '')
    return code_verifier, code_challenge


def build_auth_url(
    authorization_endpoint: str,
    client_id: str,
    redirect_uri: str,
    code_challenge: str,
    scope: str = "openid profile email",
    acr_values: Optional[str] = None,
    prompt: Optional[str] = None
) -> str:
    """
    Build OIDC authorization URL.

    Args:
        authorization_endpoint: OIDC authorization endpoint URL
        client_id: OAuth2 client ID
        redirect_uri: Callback URL
        code_challenge: PKCE code challenge
        scope: OAuth2 scopes
        acr_values: Authentication Context Class Reference values
        prompt: OIDC prompt parameter (e.g., 'login' to force re-authentication)

    Returns:
        Authorization URL
    """
    params = {
        "response_type": "code",
        "client_id": client_id,
        "scope": scope,
        "redirect_uri": redirect_uri,
        "code_challenge": code_challenge,
        "code_challenge_method": "S256",
    }

    if acr_values:
        params["acr_values"] = acr_values

    if prompt:
        params["prompt"] = prompt

    param_string = "&".join([f"{k}={requests.utils.quote(str(v))}" for k, v in params.items()])  # type: ignore
    return f"{authorization_endpoint}?{param_string}"


def exchange_code(
    token_endpoint: str,
    client_id: str,
    client_secret: str,
    redirect_uri: str,
    code: str,
    code_verifier: str
) -> Dict[str, Any]:
    """
    Exchange authorization code for access token.

    Args:
        token_endpoint: OIDC token endpoint URL
        client_id: OAuth2 client ID
        client_secret: OAuth2 client secret
        redirect_uri: Callback URL
        code: Authorization code
        code_verifier: PKCE code verifier

    Returns:
        Token response data

    Raises:
        requests.HTTPError: If token exchange fails
    """
    token_params = {
        'grant_type': 'authorization_code',
        'code': code,
        'client_id': client_id,
        'client_secret': client_secret,
        'redirect_uri': redirect_uri,
        'code_verifier': code_verifier,
    }

    response = requests.post(token_endpoint, data=token_params)
    response.raise_for_status()
    return response.json()


def get_userinfo(userinfo_endpoint: str, token_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Get user information using access token.

    Args:
        userinfo_endpoint: OIDC userinfo endpoint URL
        token_data: Token response data from exchange_code()

    Returns:
        User information

    Raises:
        requests.HTTPError: If userinfo request fails
    """
    response = requests.post(userinfo_endpoint, data=token_data)
    response.raise_for_status()
    return response.json()


def load_well_known_config(well_known_url: str) -> Dict[str, Any]:
    """
    Load OIDC configuration from .well-known endpoint.

    Args:
        well_known_url: .well-known/openid-configuration URL

    Returns:
        OIDC configuration

    Raises:
        requests.HTTPError: If config request fails
    """
    response = requests.get(well_known_url)
    response.raise_for_status()
    return response.json()
