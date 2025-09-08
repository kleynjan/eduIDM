# /accept route: self-service page showing onboarding progress

from nicegui import app, ui

from eduid_oidc.app_interface import start_eduid_login
from services.logging import logger
from services.scim_service import scim_provisioning
from services.session_manager import session_manager
from services.storage import (
    find_group_by_id,
    find_invitation_by_code,
    mark_invitation_accepted,
)


def process_invite_code(invite_code: str):
    """Check invite code; if valid, add invite code & group details to session state"""

    invitation = find_invitation_by_code(invite_code.strip())
    if invitation:
        group = find_group_by_id(invitation['group_id'])
        if group:
            # Update state with all relevant data
            state = session_manager.state
            state['invite_code'] = invite_code
            state['group_name'] = group['name']
            state['redirect_url'] = group.get('redirect_url', '')
            state['redirect_text'] = group.get('redirect_text', '')
            state['steps_completed']['code_entered'] = True
            ui.navigate.to('/accept')
        else:
            logger.error(f"Group not found for group_id: {invitation['group_id']}")
            ui.notify('Ongeldige uitnodigingscode (groep niet gevonden)', type='negative')
    else:
        logger.warning(f"Invalid invite_code attempted: {invite_code}")
        ui.notify('Ongeldige uitnodigingscode', type='negative')


@ui.page('/accept')
@ui.page('/accept/{invite_code}')
def accept_invitation(invite_code: str = ""):
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

    session_manager.initialize_user_state()
    state = session_manager.state
    logger.debug(f"Accept page, current user state: {state}")

    # Update state from invite_code parameter using consolidated logic
    if invite_code:
        process_invite_code(invite_code)

    suffix = f"{state['group_name']}" if state['group_name'] else ""
    title = f"Uitnodiging - {suffix}" if suffix else "Uitnodiging"
    ui.page_title(title)

    with ui.column().classes('max-w-4xl mx-auto p-6'):
        ui.label(f"Welkom bij {suffix}" if suffix else "Welkom").classes('text-3xl font-bold mb-2')
        ui.label('Volg het stappenplan hieronder om uw uitnodiging te accepteren.').classes('text-lg mb-6')

        # Step 1: Code input
        def step1_content():
            if not state['invite_code']:
                with ui.column().classes('mt-2'):
                    invite_code_input = ui.input('Voer hier uw uitnodigingscode in',
                                                 placeholder='Uitnodigingscode').classes('w-full')
                    ui.button('Code bevestigen', on_click=lambda x: process_invite_code(
                        invite_code_input.value)).classes('mt-2')
            else:
                ui.label('✓ Code ontvangen en bevestigd').classes('text-green-600 mt-2')

        create_step_card(1, '1. Kopieer en plak hier de code die u heeft ontvangen.',
                         state['steps_completed']['code_entered'], step1_content)

        # Step 2: eduID login
        def step2_content():
            if state['invite_code'] and state['steps_completed']['code_entered']:
                if not state['steps_completed']['eduid_login']:
                    with ui.column().classes('mt-2'):
                        ui.button('Inloggen met eduID', on_click=lambda x: start_eduid_login(
                            app.storage.user)).classes('mr-4')
                        with ui.row().classes('items-center mt-2'):
                            ui.label('Nog geen eduID?').classes('text-sm')
                            ui.link('Maak hem hier aan', 'https://eduid.nl/home', new_tab=True).classes('text-sm ml-1')
                else:
                    ui.label('✓ Ingelogd met eduID').classes('text-green-600 mt-2')
            else:
                ui.label('Voltooi eerst stap 1').classes('text-gray-500 mt-2')

        create_step_card(2, '2. Klik hier om in te loggen met eduID.',
                         state['steps_completed']['eduid_login'], step2_content)

        # Step 3: MFA Verification
        def step3_content():
            if state['steps_completed']['eduid_login']:
                userinfo = state.get('eduid_userinfo', {})
                acr = userinfo.get('acr', '')

                if state['steps_completed']['mfa_verified']:
                    ui.label('✓ MFA is geconfigureerd').classes('text-green-600 mt-2')
                else:
                    # Check if ACR contains "Password" - meaning MFA is required
                    if 'Password' in acr:
                        with ui.column().classes('mt-2'):
                            ui.label('Een tweede factor is hier vereist. Installeer de eduID app.').classes(
                                'text-orange-600 mb-2')

                            def configure_mfa_dummy():
                                state['steps_completed']['mfa_verified'] = True
                                state['steps_completed']['completed'] = True
                                state['show_scim_dialog'] = True
                                ui.notify('Yep, uw tweede factor is nu zogenaamd actief!', type='positive')
                                ui.navigate.to('/accept')  # Refresh the page to show updated state

                            ui.button('Hmm, laten we net doen alsof',
                                      on_click=configure_mfa_dummy).classes('bg-orange-500 text-white')
                    else:
                        # No Password in ACR or no ACR info - MFA already configured
                        ui.label('✓ MFA is al geconfigureerd').classes('text-green-600 mt-2')

                # Show eduID attributes if available
                if userinfo:
                    with ui.expansion('Bekijk eduID attributen', icon='info').classes('mt-2'):
                        with ui.column().classes('gap-1'):
                            for key, value in userinfo.items():
                                if value:  # Only show non-empty values
                                    ui.label(f'{key}: {value}').classes('text-sm')
            else:
                ui.label('Voltooi eerst stap 2').classes('text-gray-500 mt-2')

        create_step_card(3, '3. MFA verificatie.',
                         state['steps_completed']['mfa_verified'], step3_content)

        # Step 4: Completion
        def step4_content():
            if state['steps_completed']['mfa_verified']:
                mark_invitation_accepted(state['invite_code'])      # update datetime_accepted
                with ui.column().classes('mt-2'):
                    ui.label('✓ Uw eduID is nu gekoppeld!').classes('text-green-600 mb-2')
                    redirect_url = state.get('redirect_url', 'https://canvas.uva.nl/')
                    redirect_text = state.get('redirect_text', 'Canvas (UvA)')
                    ui.link(f'Klik hier om in te loggen op {redirect_text}', redirect_url, new_tab=True).classes(
                        'bg-blue-500 text-white px-4 py-2 rounded hover:bg-blue-600')
            else:
                ui.label('Voltooi eerst de vorige stappen').classes('text-gray-500 mt-2')

        create_step_card(4, '4. Gefeliciteerd, uw eduID is nu gekoppeld.',
                         state['steps_completed']['completed'], step4_content)

        # Show SCIM provisioning dialog if flag is set
        if 'show_scim_dialog' in state and state['show_scim_dialog']:
            scim_provisioning()
