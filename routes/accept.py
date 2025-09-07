# /accept route: self-service page showing onboarding progress

from nicegui import ui

from eduid_oidc.app_interface import start_eduid_login
from services.scim_service import scim_provisioning
from session_manager import session_manager
from services.storage import find_invitation_by_hash, load_storage
from utils.logging import logger

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


def handle_hash_submit():
    """Handle hash input submission"""

    state = session_manager.state
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
            session_manager.update_state_from_hash(hash_value)
            ui.navigate.to(f'/accept/{hash_value}')
        else:
            logger.warning(f"Invalid hash submitted: {hash_value}")
            ui.notify('Ongeldige uitnodigingscode', type='negative')
    else:
        logger.warning("Empty hash value submitted")


def handle_eduid_login():
    """Handle eduID login via OIDC"""
    from nicegui import app

    logger.info("Starting eduID login process via OIDC")

    try:
        # Start eduID login - this handles everything including the redirect
        start_eduid_login(app.storage.user)
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Failed to start eduID login. Error: {error_msg}")
        ui.notify(f'OIDC Error: {error_msg}', type='negative')


@ui.page('/accept')
@ui.page('/accept/{hash_param}')
def accept_invitation(hash_param: str = ""):
    """Handle the accept invitation route"""
    logger.info(f"Accept invitation page accessed with hash_param: {hash_param}")

    # Initialize user state
    session_manager.initialize_user_state()

    # Update state from hash parameter
    session_manager.update_state_from_hash(hash_param)

    # Bind to state for reactivity using session manager
    state = session_manager.state
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
