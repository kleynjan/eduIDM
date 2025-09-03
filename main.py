import os
from datetime import datetime
from typing import Dict, Any, Optional
from nicegui import app, ui, run
from storage import load_storage, save_storage, find_guest_group_by_hash, find_group_by_id

def initialize_user_state():
    """Initialize user state in app.storage.user"""
    if 'state' not in app.storage.user:
        app.storage.user['state'] = {
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

def update_state_from_hash(hash_param: str = None):
    """Update state based on hash parameter"""
    storage_data = load_storage()
    current_hash = hash_param or app.storage.user['state']['hash']

    if current_hash:
        guest_group = find_guest_group_by_hash(storage_data, current_hash)
        if guest_group:
            group = find_group_by_id(storage_data, guest_group.get('group_id'))
            if group:
                app.storage.user['state']['group_name'] = group.get('name', 'Unknown Group')
            app.storage.user['state']['hash'] = current_hash
            app.storage.user['state']['steps_completed']['code_entered'] = True

def handle_hash_submit():
    """Handle hash input submission"""
    hash_value = app.storage.user['state']['hash_input'].strip()
    if hash_value:
        # Validate hash exists in storage
        storage_data = load_storage()
        guest_group = find_guest_group_by_hash(storage_data, hash_value)
        if guest_group:
            app.storage.user['state']['hash'] = hash_value
            app.storage.user['state']['steps_completed']['code_entered'] = True
            update_state_from_hash(hash_value)
            ui.navigate.to(f'/accept/{hash_value}')
        else:
            ui.notify('Ongeldige uitnodigingscode', type='negative')

def handle_eduid_login():
    """Handle eduID login (placeholder for OIDC)"""
    ui.notify('OIDC authentication will be implemented in the next step', type='info')

    # Simulate successful login for testing
    app.storage.user['state']['steps_completed']['eduid_login'] = True
    app.storage.user['state']['steps_completed']['attributes_verified'] = True

    # Update storage with completion
    current_hash = app.storage.user['state']['hash']
    if current_hash:
        storage_data = load_storage()
        guest_group = find_guest_group_by_hash(storage_data, current_hash)
        if guest_group and not guest_group.get('datetime_accepted'):
            guest_group['datetime_accepted'] = datetime.utcnow().isoformat() + 'Z'
            save_storage(storage_data)
            app.storage.user['state']['steps_completed']['completed'] = True

            # Show SCIM provisioning popup
            with ui.dialog() as dialog, ui.card():
                ui.label('SCIM provisioning naar backend systemen:').classes('text-lg font-bold mb-2')
                ui.label(f'guest_id: {guest_group.get("guest_id", "N/A")}')
                ui.label(f'eduID userId: {app.storage.user["state"].get("eduid_user_id", "simulated-user-id")}')
                ui.label(f'group: {app.storage.user["state"]["group_name"]}')
                ui.button('OK', on_click=dialog.close).classes('mt-4')
            dialog.open()

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

    # Initialize user state
    initialize_user_state()

    # Update state from hash parameter
    update_state_from_hash(hash_param)

    # Bind to state for reactivity
    state = app.storage.user['state']

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
            else:
                ui.label('Voltooi eerst stap 2').classes('text-gray-500 mt-2')

        create_step_card(3, '3. Verificatie van eduID attributen.',
                         state['steps_completed']['attributes_verified'], step3_content)

        # Step 4: Completion
        def step4_content():
            if state['steps_completed']['attributes_verified']:
                with ui.column().classes('mt-2'):
                    ui.label('✓ Uw eduID is nu gekoppeld!').classes('text-green-600 mb-2')
                    ui.link('Klik hier om in te loggen op Canvas', 'https://canvas.uva.nl/',
                            new_tab=True).classes('bg-blue-500 text-white px-4 py-2 rounded hover:bg-blue-600')
            else:
                ui.label('Voltooi eerst de vorige stappen').classes('text-gray-500 mt-2')

        create_step_card(4, '4. Gefeliciteerd, uw eduID is nu gekoppeld.',
                         state['steps_completed']['completed'], step4_content)

if __name__ in {"__main__", "__mp_main__"}:
    ui.run(host='localhost', port=8080, storage_secret="AbraXabra2452", title='EduInvite', show=False)
