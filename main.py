import os
import logging
import uuid
from datetime import datetime
from typing import Dict, Any, Optional
from nicegui import app, ui, run
from storage import load_storage, save_storage, find_invitation_by_hash, find_group_by_id
from oidc import (
    get_auth_url, get_access_token, get_userinfo, is_logged_in,
    initialize_oidc_state, get_oidc_error, clear_oidc_error
)
from utils.logging import setup_logging, logger

# Generate unique server instance key on startup
SERVER_SESSION_KEY = str(uuid.uuid4())

# Configure logging
setup_logging(
    level=logging.DEBUG,
    log_file='eduinvite.log',
    enable_console_logging=False
)

def initialize_user_state():
    """Initialize user state in app.storage.user with server instance key"""
    # Check if current server session exists
    if SERVER_SESSION_KEY not in app.storage.user:
        logger.debug(f"Initializing new user state for server session: {SERVER_SESSION_KEY}")
        app.storage.user[SERVER_SESSION_KEY] = {
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
        logger.info(f"User state initialized successfully for server session: {SERVER_SESSION_KEY}")
    else:
        logger.debug(f"User state already exists for current server session: {SERVER_SESSION_KEY}")

    # Clean up old sessions (optional - keeps storage lean)
    sessions_to_remove = []
    for key in app.storage.user.keys():
        if key.startswith('session_') and key != SERVER_SESSION_KEY:
            sessions_to_remove.append(key)

    for old_session in sessions_to_remove:
        del app.storage.user[old_session]
        logger.debug(f"Cleaned up old session: {old_session}")

def update_state_from_hash(hash_param: str = None):
    """Update state based on hash parameter"""
    logger.debug(f"Updating state from hash parameter: {hash_param}")
    storage_data = load_storage()
    state = app.storage.user[SERVER_SESSION_KEY]['state']
    current_hash = hash_param or state['hash']

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

def handle_hash_submit():
    """Handle hash input submission"""
    state = app.storage.user[SERVER_SESSION_KEY]['state']
    hash_value = state['hash_input'].strip()
    logger.info(f"Hash submission attempt with value: {hash_value}")

    if hash_value:
        # Validate hash exists in storage
        storage_data = load_storage()
        invitation = find_invitation_by_hash(storage_data, hash_value)
        if invitation:
            logger.info(f"Hash validation successful for: {hash_value}")
            state['hash'] = hash_value
            state['steps_completed']['code_entered'] = True
            update_state_from_hash(hash_value)
            logger.info(f"Navigating to /accept/{hash_value}")
            ui.navigate.to(f'/accept/{hash_value}')
        else:
            logger.warning(f"Invalid hash submitted: {hash_value}")
            ui.notify('Ongeldige uitnodigingscode', type='negative')
    else:
        logger.warning("Empty hash value submitted")


def handle_eduid_login():
    """Handle eduID login via OIDC"""
    logger.info("Starting eduID login process via OIDC")

    # Get session state
    session_state = app.storage.user[SERVER_SESSION_KEY]

    # Initialize OIDC state
    logger.debug("Initializing OIDC state")
    initialize_oidc_state(session_state)

    # Clear any previous errors
    logger.debug("Clearing previous OIDC errors")
    clear_oidc_error(session_state)

    # Get authorization URL
    logger.debug("Requesting authorization URL")
    auth_url = get_auth_url(session_state)
    if auth_url:
        logger.info(f"Authorization URL generated successfully, redirecting to: {auth_url}")
        # Redirect to OIDC provider
        ui.navigate.to(auth_url, new_tab=False)
    else:
        error = get_oidc_error(session_state)
        logger.error(f"Failed to generate authorization URL. Error: {error}")
        ui.notify(f'OIDC Error: {error}' if error else 'Failed to generate authorization URL', type='negative')

def scim_provisioning():
    """Handle SCIM provisioning dialog and operations"""
    logger.info("Starting SCIM provisioning process")

    # Get session state
    session_state = app.storage.user[SERVER_SESSION_KEY]
    state = session_state['state']

    # Get invitation and userinfo
    storage_data = load_storage()
    invitation = find_invitation_by_hash(storage_data, state['hash']) if state['hash'] else None
    userinfo = state.get('eduid_userinfo', {})

    if not invitation or not userinfo:
        logger.error("Cannot perform SCIM provisioning: missing invitation or userinfo")
        return

    logger.debug("Displaying SCIM provisioning dialog")

    def close_scim_dialog():
        state['show_scim_dialog'] = False
        logger.info("SCIM provisioning dialog closed by user")

    with ui.dialog(value=True) as scim_dialog, ui.card():
        ui.label('SCIM provisioning naar backend systemen:').classes('text-lg font-bold mb-2')
        ui.label(f'guest_id: {invitation.get("guest_id", "N/A")}')
        ui.label(f'eduID userId: {userinfo.get("sub", "N/A")}')
        ui.label(f'group: {state["group_name"]}')
        ui.button('OK', on_click=lambda: (close_scim_dialog(), scim_dialog.close())).classes('mt-4')

def complete_oidc_flow():
    """Complete OIDC flow after successful authentication"""
    logger.info("Completing OIDC flow after successful authentication")

    # Get session state
    session_state = app.storage.user[SERVER_SESSION_KEY]

    # Get userinfo
    logger.debug("Retrieving user info from OIDC provider")
    userinfo = get_userinfo(session_state)
    if userinfo:
        logger.info(f"User info retrieved successfully for user: {userinfo.get('sub', 'unknown')}")

        # Get current session state
        state = session_state['state']

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

                # Store eduID attributes in guest record
                for guest in storage_data.get('guests', []):
                    if guest.get('guest_id') == invitation.get('guest_id'):
                        # Extract eduperson_principal_name and store as eppn
                        userinfo_copy = userinfo.copy()
                        eppn = userinfo_copy.pop('eduperson_principal_name', '')
                        guest['eppn'] = eppn
                        guest['eduid_props'] = userinfo_copy
                        logger.info(f"Stored eduID properties for guest_id: {guest.get('guest_id')}, eppn: {eppn}")
                        break

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

def create_step_card(step_num: int, title: str, is_completed: bool, content_func):
    """Create a step card with conditional content"""
    status_color = 'positive' if is_completed else 'grey'
    status_icon = 'check_circle' if is_completed else 'radio_button_unchecked'

    with ui.card().classes('w-full mb-4'):
        with ui.row().classes('items-center w-full'):
            ui.icon(status_icon, color=status_color).classes('text-2xl mr-4')
            with ui.column().classes('flex-grow'):
                ui.label(title).classes('text-lg font-semibold')
                content_func()

@ui.page('/accept')
@ui.page('/accept/{hash_param}')
def accept_invitation(hash_param: str = None):
    """Handle the accept invitation route"""
    logger.info(f"Accept invitation page accessed with hash_param: {hash_param}")

    # Initialize user state
    initialize_user_state()

    # Update state from hash parameter
    update_state_from_hash(hash_param)

    # Bind to state for reactivity using current server session
    state = app.storage.user[SERVER_SESSION_KEY]['state']
    logger.debug(f"Current user state: {state}")

    # Page setup
    ui.page_title(f'Uitnodiging - {state["group_name"]}')

    with ui.column().classes('max-w-4xl mx-auto p-6'):
        # Header
        ui.label().bind_text_from(state, 'group_name',
                                  lambda name: f'Welkom bij {name}').classes('text-3xl font-bold mb-2')
        ui.label('Volg het stappenplan hieronder om uw uitnodiging te accepteren.').classes('text-lg mb-6')

        # Step 1: Code input
        def step1_content():
            if not state['hash']:
                with ui.column().classes('mt-2'):
                    ui.input('Voer hier uw uitnodigingscode in',
                             placeholder='Uitnodigingscode').bind_value(state, 'hash_input').classes('w-full')
                    ui.button('Code bevestigen', on_click=handle_hash_submit).classes('mt-2')
            else:
                ui.label('✓ Code ontvangen en bevestigd').classes('text-green-600 mt-2')

        create_step_card(1, '1. Kopieer en plak hier de code die u heeft ontvangen.',
                         state['steps_completed']['code_entered'], step1_content)

        # Step 2: eduID login
        def step2_content():
            if state['hash'] and state['steps_completed']['code_entered']:
                if not state['steps_completed']['eduid_login']:
                    with ui.column().classes('mt-2'):
                        ui.button('Inloggen met eduID', on_click=handle_eduid_login).classes('mr-4')
                        with ui.row().classes('items-center mt-2'):
                            ui.label('Nog geen eduID?').classes('text-sm')
                            ui.link('Maak hem hier aan', 'https://eduid.nl/home', new_tab=True).classes('text-sm ml-1')
                else:
                    ui.label('✓ Ingelogd met eduID').classes('text-green-600 mt-2')
            else:
                ui.label('Voltooi eerst stap 1').classes('text-gray-500 mt-2')

        create_step_card(2, '2. Klik hier om in te loggen met eduID.',
                         state['steps_completed']['eduid_login'], step2_content)

        # Step 3: Attribute verification
        def step3_content():
            if state['steps_completed']['eduid_login']:
                ui.label('✓ eduID attributen geverifieerd').classes('text-green-600 mt-2')

                # Show eduID attributes if available
                userinfo = state.get('eduid_userinfo')
                if userinfo:
                    with ui.expansion('Bekijk eduID attributen', icon='info').classes('mt-2'):
                        with ui.column().classes('gap-1'):
                            for key, value in userinfo.items():
                                if value:  # Only show non-empty values
                                    ui.label(f'{key}: {value}').classes('text-sm')
            else:
                ui.label('Voltooi eerst stap 2').classes('text-gray-500 mt-2')

        create_step_card(3, '3. Verificatie van eduID attributen.',
                         state['steps_completed']['attributes_verified'], step3_content)

        # Step 4: Completion
        def step4_content():
            if state['steps_completed']['attributes_verified']:
                with ui.column().classes('mt-2'):
                    ui.label('✓ Uw eduID is nu gekoppeld!').classes('text-green-600 mb-2')
                    # Use direct values instead of binding for the link
                    redirect_url = state.get('redirect_url', 'https://canvas.uva.nl/')
                    redirect_text = state.get('redirect_text', 'Canvas (UvA)')
                    ui.link(f'Klik hier om in te loggen op {redirect_text}', redirect_url, new_tab=True).classes(
                        'bg-blue-500 text-white px-4 py-2 rounded hover:bg-blue-600')
            else:
                ui.label('Voltooi eerst de vorige stappen').classes('text-gray-500 mt-2')

        create_step_card(4, '4. Gefeliciteerd, uw eduID is nu gekoppeld.',
                         state['steps_completed']['completed'], step4_content)

        # Show SCIM provisioning dialog if flag is set
        if state.get('show_scim_dialog'):
            scim_provisioning()

        # Debug: Check if we should show SCIM dialog
        logger.debug(f"SCIM dialog flag: {state.get('show_scim_dialog')}")
        logger.debug(f"Steps completed: {state['steps_completed']}")

@ui.page('/oidc_callback')
def oidc_callback(code: str = None, error: str = None):
    """Handle OIDC callback from authorization server"""
    logger.info(f"OIDC callback received - code: {'present' if code else 'missing'}, error: {error}")

    ui.page_title('Processing Authentication...')

    with ui.column().classes('max-w-2xl mx-auto p-6 text-center'):
        if error:
            logger.error(f"OIDC authorization error received: {error}")
            # Handle authorization error
            ui.label('Authentication Error').classes('text-2xl font-bold text-red-600 mb-4')
            ui.label(f'Error: {error}').classes('text-lg mb-4')
            ui.button('Return to Accept Page', on_click=lambda: ui.navigate.to(
                '/accept')).classes('bg-blue-500 text-white')
            return

        if not code:
            logger.error("OIDC callback received without authorization code")
            ui.label('Authentication Error').classes('text-2xl font-bold text-red-600 mb-4')
            ui.label('No authorization code received').classes('text-lg mb-4')
            ui.button('Return to Accept Page', on_click=lambda: ui.navigate.to(
                '/accept')).classes('bg-blue-500 text-white')
            return

        logger.info("Processing OIDC authorization code")
        # Show loading message
        ui.label('Processing Authentication...').classes('text-xl mb-4')
        ui.spinner(size='lg')

        # Get session state
        session_state = app.storage.user[SERVER_SESSION_KEY]

        # Exchange code for access token
        logger.debug("Exchanging authorization code for access token")
        token_data = get_access_token(code, session_state)
        if not token_data:
            error_msg = get_oidc_error(session_state) or 'Failed to get access token'
            logger.error(f"Token exchange failed: {error_msg}")
            ui.label('Token Exchange Failed').classes('text-xl font-bold text-red-600 mb-4')
            ui.label(f'Error: {error_msg}').classes('text-lg mb-4')
            ui.button('Return to Accept Page', on_click=lambda: ui.navigate.to(
                '/accept')).classes('bg-blue-500 text-white')
            return

        logger.info("Token exchange successful, completing OIDC flow")
        # Complete the OIDC flow
        complete_oidc_flow()

        # Success - redirect back to accept page
        ui.label('Authentication Successful!').classes('text-xl font-bold text-green-600 mb-4')
        ui.label('Redirecting...').classes('text-lg mb-4')

        # Auto-redirect after a short delay
        current_hash = app.storage.user.get(SERVER_SESSION_KEY, {}).get('state', {}).get('hash', '')
        redirect_url = f'/accept/{current_hash}' if current_hash else '/accept'
        logger.info(f"Redirecting to: {redirect_url}")
        ui.timer(2.0, lambda: ui.navigate.to(redirect_url), once=True)

@ui.page('/oidc_error')
def oidc_error_page():
    """Display OIDC error page"""
    # Get session state
    session_state = app.storage.user[SERVER_SESSION_KEY]
    error = get_oidc_error(session_state)
    logger.error(f"OIDC error page accessed with error: {error}")

    ui.page_title('OIDC Authentication Error')

    with ui.column().classes('max-w-2xl mx-auto p-6'):
        ui.label('Authentication Error').classes('text-2xl font-bold text-red-600 mb-4')

        if error:
            ui.label(f'Error: {error}').classes('text-lg mb-4')
        else:
            ui.label('An unknown error occurred during authentication.').classes('text-lg mb-4')

        ui.label('Please try again or contact support if the problem persists.').classes('mb-4')

        with ui.row().classes('gap-4'):
            ui.button('Try Again', on_click=lambda: (logger.info("User clicked 'Try Again' on error page"),
                      ui.navigate.to('/accept'))).classes('bg-blue-500 text-white')
            ui.button('Clear Error', on_click=lambda: (logger.info("User clicked 'Clear Error'"), clear_oidc_error(session_state),
                      ui.navigate.to('/accept'))).classes('bg-gray-500 text-white')

if __name__ in {"__main__", "__mp_main__"}:
    logger.info("Starting EduInvite application on localhost:8080")
    ui.run(host='localhost', port=8080, storage_secret="AbraXabra2452", title='EduInvite', show=False)
