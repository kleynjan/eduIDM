"""
SCIM provisioning service for eduIDM application.
Handles SCIM provisioning dialog and operations.
"""

from nicegui import ui
from session_manager import session_manager
from services.storage import load_storage, find_invitation_by_hash
from utils.logging import logger


def scim_provisioning():
    """Handle SCIM provisioning dialog and operations"""
    logger.info("Starting SCIM provisioning process")

    # Get session state
    state = session_manager.state

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
