# /invitations page

from nicegui import ui
from services.storage import (
    create_invitation, get_all_invitations_with_details, get_all_groups
)
from utils.logging import logger

TITLE = "Invitations"

@ui.page('/invitations')
def invitations_page():
    logger.debug("invitations page accessed")

    ui.page_title(TITLE)

    # Create reactive state for the page
    page_state = {'invitations': [{}], 'groups': get_all_groups()}

    with ui.column().classes('max-w-6xl mx-auto p-6'):

        # Invitations table
        @ui.refreshable
        def invitations_table():
            page_state['invitations'] = get_all_invitations_with_details()

            if not page_state['invitations']:
                ui.label('Geen uitnodigingen gevonden.').classes('text-gray-500 text-center py-8')
            else:
                with ui.card().classes('w-full'):
                    # Table headers
                    with ui.row().classes('w-full font-bold border-b pb-2 mb-2'):
                        ui.label('Groep').classes('flex-1')
                        ui.label('Guest ID').classes('flex-1')
                        ui.label('Email').classes('flex-1')
                        ui.label('Uitgenodigd').classes('flex-1')
                        ui.label('Geaccepteerd').classes('flex-1')

                    # Table rows
                    for invitation in page_state['invitations']:
                        with ui.row().classes('w-full border-b py-2'):
                            ui.label(invitation['group_name']).classes('flex-1')
                            ui.label(invitation['guest_id']).classes('flex-1')
                            ui.label(invitation['invitation_mail_address']).classes('flex-1')
                            ui.label(invitation['datetime_invited_formatted']).classes('flex-1')
                            ui.label(invitation['datetime_accepted_formatted'] or '-').classes('flex-1')

        ui.label(TITLE).classes('text-3xl font-bold mb-6')
        invitations_table()
        ui.button('Invite...', on_click=lambda: manual_invite_dialog(page_state)).classes('mb-4 bg-blue-500 text-white')

        # Store reference to refresh function for later use
        page_state['refresh_function'] = invitations_table.refresh


def manual_invite_dialog(page_state):
    """Show the invitation dialog"""
    logger.info("Opening invite dialog")

    # Dialog state
    dialog_state = {
        'invitation_mail_address': '',
        'guest_id': '',
        'selected_group_id': ''
    }

    def handle_invite():
        """Handle the invite button click"""
        logger.info("Processing invitation creation")

        # Validate inputs
        if not dialog_state['invitation_mail_address'].strip():
            ui.notify('Email adres is verplicht', type='negative')
            return

        if not dialog_state['guest_id'].strip():
            ui.notify('Guest ID is verplicht', type='negative')
            return

        if not dialog_state['selected_group_id']:
            ui.notify('Selecteer een groep', type='negative')
            return

        try:
            # Create the invitation
            invitation_id = create_invitation(
                dialog_state['guest_id'].strip(),
                dialog_state['selected_group_id'],
                dialog_state['invitation_mail_address'].strip()
            )

            # Find group name for confirmation
            groups = [group for group in page_state['groups'] if group['id'] == dialog_state['selected_group_id']]
            if not groups:
                raise Exception("Selected group not found")
            selected_group = groups[0]

            logger.info(f"Invitation created successfully: {invitation_id}")

            # Close the invite dialog
            invite_dialog.close()

            # Show confirmation dialog
            show_confirmation_dialog(
                selected_group['name'],
                dialog_state['invitation_mail_address'],
                invitation_id,
                page_state
            )

        except Exception as e:
            logger.error(f"Failed to create invitation: {e}")
            ui.notify(f'Fout bij het aanmaken van uitnodiging: {str(e)}', type='negative')

    def handle_cancel():
        """Handle the cancel button click"""
        logger.info("Invite dialog cancelled")
        invite_dialog.close()

    # Create the dialog
    with ui.dialog() as invite_dialog, ui.card().classes('w-96'):
        ui.label('Nieuwe Uitnodiging').classes('text-xl font-bold mb-4')

        # Email input
        ui.input('Email adres', placeholder='gebruiker@example.com').bind_value(
            dialog_state, 'invitation_mail_address'
        ).classes('w-full mb-3')

        # Guest ID input
        ui.input('Guest ID', placeholder='guest123').bind_value(
            dialog_state, 'guest_id'
        ).classes('w-full mb-3')

        # Group selection
        group_options = {group['id']: group['name'] for group in page_state['groups']}
        if group_options:
            ui.select(
                options=group_options,
                label='Selecteer Groep',
                value=None
            ).bind_value(dialog_state, 'selected_group_id').classes('w-full mb-4')
        else:
            ui.label('Geen groepen beschikbaar').classes('text-red-500 mb-4')

        # Buttons
        with ui.row().classes('w-full justify-end gap-2'):
            ui.button('Cancel', on_click=handle_cancel).classes('bg-gray-500 text-white')
            ui.button('Invite', on_click=handle_invite).classes('bg-blue-500 text-white')

    invite_dialog.open()


def show_confirmation_dialog(group_name, email_address, invitation_id, page_state):
    """Show the confirmation dialog after successful invitation creation"""
    logger.info(f"Showing confirmation dialog for invitation: {invitation_id}")

    def handle_ok():
        """Handle OK button click - refresh the invitations list"""
        logger.info("Confirmation dialog closed, refreshing invitations list")

        # Close dialog first
        confirmation_dialog.close()

        # Refresh the table using the stored refresh function
        if 'refresh_function' in page_state:
            page_state['refresh_function']()

    with ui.dialog(value=True) as confirmation_dialog, ui.card().classes('w-96'):
        ui.label('Uitnodiging Aangemaakt').classes('text-xl font-bold mb-4')

        ui.label(f'Uitnodiging voor group {group_name} wordt verstuurd naar {email_address}.').classes('mb-2')
        ui.label(f'Uitnodigingscode: {invitation_id}').classes('mb-4 font-mono text-sm')

        ui.button('OK', on_click=handle_ok).classes('bg-blue-500 text-white w-full')
        ui.button('OK', on_click=handle_ok).classes('bg-blue-500 text-white w-full')
