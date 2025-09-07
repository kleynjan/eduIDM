# /accept route: self-service page showing onboarding progress
# Simplified with reactive binding

from nicegui import ui

from eduid_oidc.app_interface import start_eduid_login
from services.scim_service import scim_provisioning
from services.session_manager import session_manager
from services.storage import find_invitation_by_code, find_group_by_id, load_storage
from utils.logging import logger


def handle_invite_code_submit():
    state = session_manager.state
    invite_code_value = state['invite_code_input'].strip()
    logger.debug(f"Invite code submission attempt with value: {invite_code_value}")

    if invite_code_value and apply_invite_code_to_state(invite_code_value):
        logger.info(f"Invite code validation successful for: {invite_code_value}")
        # No navigation needed - UI updates reactively
    else:
        logger.warning(f"Invalid invite_code submitted: {invite_code_value}")
        ui.notify('Ongeldige uitnodigingscode', type='negative')


def apply_invite_code_to_state(invite_code: str) -> bool:
    """Validate and apply invite code to session state if valid."""
    if not invite_code or not invite_code.strip():
        return False

    storage_data = load_storage()
    invitation = find_invitation_by_code(storage_data, invite_code.strip())
    if not invitation:
        return False

    group = find_group_by_id(storage_data, invitation['group_id'])
    if not group:
        return False

    # Update state - UI will update reactively
    state = session_manager.state
    state['invite_code'] = invite_code
    state['group_name'] = group.get('name', 'Unknown Group')
    state['redirect_url'] = group.get('redirect_url', 'https://canvas.uva.nl/')
    state['redirect_text'] = group.get('redirect_text', 'Canvas (UvA)')
    state['steps_completed']['code_entered'] = True

    return True


def handle_eduid_login():
    """Handle eduID login via OIDC"""
    from nicegui import app
    logger.info("Starting eduID login process via OIDC")

    try:
        start_eduid_login(app.storage.user)
    except Exception as e:
        logger.error(f"Failed to start eduID login. Error: {str(e)}")
        ui.notify(f'OIDC Error: {str(e)}', type='negative')


@ui.page('/accept')
@ui.page('/accept/{invite_code_param}')
def accept_invitation(invite_code_param: str = ""):
    """Handle the accept invitation route with reactive binding"""
    logger.info(f"Accept invitation page accessed with invite_code_param: {invite_code_param}")

    # Initialize user state
    session_manager.initialize_user_state()
    state = session_manager.state

    # Update state from invite_code parameter
    if invite_code_param and not state['invite_code']:
        apply_invite_code_to_state(invite_code_param)

    logger.debug(f"Current user state: {state}")

    # Page setup
    ui.page_title(f'Uitnodiging - {state["group_name"]}')

    with ui.column().classes('max-w-4xl mx-auto p-6'):
        # Reactive header
        ui.label().bind_text_from(state, 'group_name',
                                  lambda name: f'Welkom bij {name}').classes('text-3xl font-bold mb-2')
        ui.label('Volg het stappenplan hieronder om uw uitnodiging te accepteren.').classes('text-lg mb-6')

        # Step 1: Code input
        with ui.card().classes('w-full mb-4'):
            with ui.row().classes('items-center w-full'):
                step1_icon = ui.icon('radio_button_unchecked', color='grey').classes('text-2xl mr-4')
                step1_icon.bind_name_from(state['steps_completed'], 'code_entered',
                                          lambda done: 'check_circle' if done else 'radio_button_unchecked')

                with ui.column().classes('flex-grow'):
                    ui.label('1. Kopieer en plak hier de code die u heeft ontvangen.').classes('text-lg font-semibold')

                    # Show input or success message based on state
                    input_container = ui.element('div').classes('mt-2')
                    input_container.bind_visibility_from(state['steps_completed'], 'code_entered',
                                                         backward=lambda x: not x)
                    with input_container:
                        code_input = ui.input('Voer hier uw uitnodigingscode in',
                                              placeholder='Uitnodigingscode').classes('w-full')
                        code_input.bind_value(state, 'invite_code_input')

                        submit_btn = ui.button('Code bevestigen', on_click=handle_invite_code_submit).classes('mt-2')
                        # Enable button only when input has content
                        code_input.on('input', lambda: submit_btn.set_enabled(bool(state['invite_code_input'].strip())))

                    success_msg = ui.label('✓ Code ontvangen en bevestigd').classes('text-green-600 mt-2')
                    success_msg.bind_visibility_from(state['steps_completed'], 'code_entered')

        # Step 2: eduID login
        with ui.card().classes('w-full mb-4'):
            with ui.row().classes('items-center w-full'):
                step2_icon = ui.icon('radio_button_unchecked', color='grey').classes('text-2xl mr-4')
                step2_icon.bind_name_from(state['steps_completed'], 'eduid_login',
                                          lambda done: 'check_circle' if done else 'radio_button_unchecked')

                with ui.column().classes('flex-grow'):
                    ui.label('2. Klik hier om in te loggen met eduID.').classes('text-lg font-semibold')

                    # Show different content based on progress
                    login_container = ui.element('div').classes('mt-2')
                    login_container.bind_visibility_from(state['steps_completed'], 'code_entered')
                    with login_container:
                        if not state['steps_completed']['eduid_login']:
                            ui.button('Inloggen met eduID', on_click=handle_eduid_login).classes('mr-4')
                            with ui.row().classes('items-center mt-2'):
                                ui.label('Nog geen eduID?').classes('text-sm')
                                ui.link('Maak hem hier aan', 'https://eduid.nl/home',
                                        new_tab=True).classes('text-sm ml-1')
                        else:
                            ui.label('✓ Ingelogd met eduID').classes('text-green-600')

                    pending_msg = ui.label('Voltooi eerst stap 1').classes('text-gray-500 mt-2')
                    pending_msg.bind_visibility_from(state['steps_completed'], 'code_entered',
                                                     backward=lambda x: not x)

        # Step 3: Attribute verification
        with ui.card().classes('w-full mb-4'):
            with ui.row().classes('items-center w-full'):
                step3_icon = ui.icon('radio_button_unchecked', color='grey').classes('text-2xl mr-4')
                step3_icon.bind_name_from(state['steps_completed'], 'attributes_verified',
                                          lambda done: 'check_circle' if done else 'radio_button_unchecked')

                with ui.column().classes('flex-grow'):
                    ui.label('3. Verificatie van eduID attributen.').classes('text-lg font-semibold')

                    if state['steps_completed']['eduid_login']:
                        ui.label('✓ eduID attributen geverifieerd').classes('text-green-600 mt-2')

                        # Show eduID attributes if available
                        if 'eduid_userinfo' in state and state['eduid_userinfo']:
                            with ui.expansion('Bekijk eduID attributen', icon='info').classes('mt-2'):
                                with ui.column().classes('gap-1'):
                                    for key, value in state['eduid_userinfo'].items():
                                        if value:
                                            ui.label(f'{key}: {value}').classes('text-sm')
                    else:
                        ui.label('Voltooi eerst stap 2').classes('text-gray-500 mt-2')

        # Step 4: Completion
        with ui.card().classes('w-full mb-4'):
            with ui.row().classes('items-center w-full'):
                step4_icon = ui.icon('radio_button_unchecked', color='grey').classes('text-2xl mr-4')
                step4_icon.bind_name_from(state['steps_completed'], 'completed',
                                          lambda done: 'check_circle' if done else 'radio_button_unchecked')

                with ui.column().classes('flex-grow'):
                    ui.label('4. Gefeliciteerd, uw eduID is nu gekoppeld.').classes('text-lg font-semibold')

                    if state['steps_completed']['attributes_verified']:
                        with ui.column().classes('mt-2'):
                            ui.label('✓ Uw eduID is nu gekoppeld!').classes('text-green-600 mb-2')
                            redirect_url = state.get('redirect_url', 'https://canvas.uva.nl/')
                            redirect_text = state.get('redirect_text', 'Canvas (UvA)')
                            ui.link(f'Klik hier om in te loggen op {redirect_text}', redirect_url, new_tab=True).classes(
                                'bg-blue-500 text-white px-4 py-2 rounded hover:bg-blue-600')
                    else:
                        ui.label('Voltooi eerst de vorige stappen').classes('text-gray-500 mt-2')

        # Show SCIM provisioning dialog if flag is set
        if state.get('show_scim_dialog'):
            scim_provisioning()

        logger.debug(f"SCIM dialog flag: {state.get('show_scim_dialog')}")
        logger.debug(f"Steps completed: {state['steps_completed']}")
