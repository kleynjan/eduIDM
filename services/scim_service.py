# services/scim_service.py
# not really scim provisioning yet...

from nicegui import ui
from services.session_manager import session_manager
from services.storage import find_invitation_by_code

# dummy scim
def scim_provisioning():
    state = session_manager.state
    invitation = find_invitation_by_code(state['invite_code'])
    userinfo = state.get('eduid_userinfo', {})

    def close_scim_dialog():
        state['show_scim_dialog'] = False

    if invitation:
        with ui.dialog(value=True) as scim_dialog, ui.card().classes('w-lg p-4'):
            ui.label('Uw eduID wordt nu gekoppeld in de applicatie:').classes('text-lg font-bold mb-2')
            ui.label(f'guest_id: {invitation.get("guest_id", "N/A")}')
            ui.label(f'eduID userId: {userinfo.get("sub", "N/A")}')
            ui.label(f'group: {state["group_name"]}')
            ui.button('OK', on_click=lambda: (close_scim_dialog(), scim_dialog.close())).classes('mt-4')
