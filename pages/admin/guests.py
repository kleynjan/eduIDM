"""
Admin Guests Page
Manage guests - overview of all guests (invited persons) including status + buttons to invite & delete
Also handles the invitation creation page
"""

from nicegui import ui
from data_manager import DataManager, Guest, GuestGroup
from typing import Optional


def render_page(data_manager: DataManager, group_id: Optional[str] = None):
    """Render the admin guests page"""

    # Page header
    if group_id:
        group = data_manager.get_group(group_id)
        group_name = group.name if group else f"Unknown Group ({group_id})"
        ui.label(f'Guest Management - {group_name}').classes('text-3xl font-bold mb-6')
    else:
        ui.label('Guest Management - All Groups').classes('text-3xl font-bold mb-6')

    # Navigation
    with ui.row().classes('mb-4 gap-2'):
        ui.button('← Back to Home', on_click=lambda: ui.navigate.to('/')).classes('bg-gray-500 text-white')
        ui.button('Users', on_click=lambda: ui.navigate.to('/admin/users')).classes('bg-blue-500 text-white')
        ui.button('Roles', on_click=lambda: ui.navigate.to('/admin/roles')).classes('bg-orange-500 text-white')
        ui.button('Groups', on_click=lambda: ui.navigate.to('/groups')).classes('bg-green-500 text-white')

    # Group filter
    groups = data_manager.get_groups()
    if groups and not group_id:
        with ui.row().classes('mb-4 gap-2'):
            ui.label('Filter by Group:').classes('self-center')
            for group in groups:
                ui.button(group.name, on_click=lambda g=group: ui.navigate.to(
                    f'/guests/{g.id}')).classes('bg-purple-500 text-white')
            ui.button('All Groups', on_click=lambda: ui.navigate.to('/guests')).classes('bg-purple-700 text-white')

    # Invite button
    if group_id:
        ui.button('+ Invite New Guest', on_click=lambda: ui.navigate.to(f'/guests/invite/{group_id}')
                  ).classes('bg-blue-600 text-white mb-4')
    else:
        ui.label('Select a group to invite guests').classes('text-gray-500 mb-4')

    # Get guest data
    if group_id:
        guest_groups = data_manager.get_guest_groups_by_group(group_id)
    else:
        guest_groups = data_manager.get_guest_groups()

    guests = data_manager.get_guests()
    groups_lookup = {group.id: group.name for group in groups}
    guests_lookup = {guest.guest_id: guest for guest in guests}

    if not guest_groups:
        ui.label('No guest invitations found.').classes('text-gray-500 text-lg')
        return

    # Create table
    columns = [
        {'name': 'guest_name', 'label': 'Guest Name', 'field': 'guest_name', 'required': True, 'align': 'left'},
        {'name': 'email_invited', 'label': 'Email Invited', 'field': 'email_invited', 'align': 'left'},
        {'name': 'group_name', 'label': 'Group', 'field': 'group_name', 'align': 'left'},
        {'name': 'status', 'label': 'Status', 'field': 'status', 'align': 'center'},
        {'name': 'invited_date', 'label': 'Invited Date', 'field': 'invited_date', 'align': 'center'},
        {'name': 'accepted_date', 'label': 'Accepted Date', 'field': 'accepted_date', 'align': 'center'},
        {'name': 'verification', 'label': 'Verification', 'field': 'verification', 'align': 'center'},
        {'name': 'actions', 'label': 'Actions', 'field': 'actions', 'align': 'center'},
    ]

    # Convert guest groups to table rows
    rows = []
    for gg in guest_groups:
        guest = guests_lookup.get(gg.mail_address_invited.split('@')[0])  # Simple lookup by email prefix
        guest_name = 'Unknown Guest'
        verification_status = 'N/A'

        if guest:
            guest_name = f"{guest.given_name or ''} {guest.surname or ''}".strip() or guest.guest_id
            if guest.verification_status:
                verifications = []
                if guest.verification_status.get('verify_institution'):
                    verifications.append('Institution')
                if guest.verification_status.get('verify_idin'):
                    verifications.append('iDIN')
                if guest.verification_status.get('verify_mfa'):
                    verifications.append('MFA')
                verification_status = ', '.join(verifications) if verifications else 'None'

        status = 'Accepted' if gg.datetime_accepted else 'Pending'
        invited_date = gg.datetime_invited.split('T')[0] if gg.datetime_invited else 'N/A'
        accepted_date = gg.datetime_accepted.split('T')[0] if gg.datetime_accepted else 'N/A'

        rows.append({
            'id': gg.id,
            'guest_name': guest_name,
            'email_invited': gg.mail_address_invited,
            'group_name': groups_lookup.get(gg.group_id, f"Unknown ({gg.group_id})"),
            'status': status,
            'invited_date': invited_date,
            'accepted_date': accepted_date,
            'verification': verification_status,
            'actions': gg.id
        })

    table = ui.table(columns=columns, rows=rows, row_key='id').classes('w-full')

    # Add action buttons to each row
    table.add_slot('body-cell-actions', '''
        <q-td :props="props">
            <q-btn flat round dense icon="delete" color="red" @click="$parent.$emit('delete-invitation', props.row)" />
        </q-td>
    ''')

    # Handle table events
    table.on('delete-invitation', lambda e: show_delete_invitation_dialog(data_manager, e.args['id']))


def render_invite_page(data_manager: DataManager, group_id: str):
    """Render the invitation creation page"""

    group = data_manager.get_group(group_id)
    if not group:
        ui.label('Group not found').classes('text-red-500 text-xl')
        ui.button('← Back to Guests', on_click=lambda: ui.navigate.to('/guests')).classes('bg-gray-500 text-white mt-4')
        return

    # Page header
    ui.label(f'Invite Guest to {group.name}').classes('text-3xl font-bold mb-6')

    # Navigation
    with ui.row().classes('mb-4 gap-2'):
        ui.button('← Back to Guests', on_click=lambda: ui.navigate.to(
            f'/guests/{group_id}')).classes('bg-gray-500 text-white')
        ui.button('View Group Details', on_click=lambda: ui.navigate.to(
            f'/groups/{group_id}')).classes('bg-green-500 text-white')

    # Invitation form
    with ui.card().classes('w-full max-w-2xl'):
        ui.label('Guest Invitation Form').classes('text-xl font-bold mb-4')

        # Option to select existing guest or create new
        with ui.row().classes('w-full mb-4'):
            guest_type = ui.radio(['existing', 'new'], value='new',
                                  on_change=lambda e: toggle_guest_form(e.value)).props('inline')
            ui.label('Choose existing guest or create new').classes('self-center ml-4')

        # Existing guest selection (initially hidden)
        existing_guests = data_manager.get_guests()
        guest_options = {guest.guest_id: f"{guest.given_name or ''} {guest.surname or ''} ({guest.mail_address_preferred or guest.guest_id})"
                         for guest in existing_guests}

        existing_guest_container = ui.column().classes('w-full')
        with existing_guest_container:
            existing_guest_select = ui.select(guest_options, label='Select Existing Guest').classes('w-full mb-4')
        existing_guest_container.set_visibility(False)

        # New guest form
        new_guest_container = ui.column().classes('w-full')
        with new_guest_container:
            ui.label('Guest Details').classes('text-lg font-semibold mb-2')
            guest_id_input = ui.input('Guest ID (optional)').classes('w-full mb-2')
            given_name_input = ui.input('Given Name').classes('w-full mb-2')
            surname_input = ui.input('Surname').classes('w-full mb-2')
            email_input = ui.input('Email Address').classes('w-full mb-4')

        # Invitation details
        ui.label('Invitation Details').classes('text-lg font-semibold mb-2')
        invite_email_input = ui.input('Email to Send Invitation To',
                                      placeholder='Leave empty to use guest email').classes('w-full mb-4')

        # Group information display
        with ui.card().classes('w-full mb-4 bg-gray-50'):
            ui.label('Group Settings').classes('text-lg font-semibold mb-2')
            ui.label(f'Group: {group.name}').classes('mb-1')
            ui.label(f'Validity: {group.validity_days} days').classes('mb-1')
            ui.label(f'iDIN Required: {"Yes" if group.idin_required else "No"}').classes('mb-1')
            ui.label(f'MFA Required: {"Yes" if group.mfa_required else "No"}').classes('mb-1')
            ui.label(f'Can Edit Email: {"Yes" if group.can_edit_mail_address else "No"}').classes('mb-1')

        # Action buttons
        with ui.row().classes('w-full justify-end gap-2 mt-4'):
            ui.button('Cancel', on_click=lambda: ui.navigate.to(
                f'/guests/{group_id}')).classes('bg-gray-500 text-white')
            ui.button('Send Invitation', on_click=lambda: send_invitation(
                data_manager, group_id, guest_type.value,
                existing_guest_select.value if guest_type.value == 'existing' else None,
                guest_id_input.value, given_name_input.value, surname_input.value,
                email_input.value, invite_email_input.value
            )).classes('bg-blue-600 text-white')

        def toggle_guest_form(guest_type_value):
            """Toggle between existing and new guest forms"""
            if guest_type_value == 'existing':
                existing_guest_container.set_visibility(True)
                new_guest_container.set_visibility(False)
            else:
                existing_guest_container.set_visibility(False)
                new_guest_container.set_visibility(True)


def show_delete_invitation_dialog(data_manager: DataManager, guest_group_id: str):
    """Show confirmation dialog to delete a guest invitation"""

    guest_groups = data_manager.get_guest_groups()
    guest_group = next((gg for gg in guest_groups if gg.id == guest_group_id), None)

    if not guest_group:
        ui.notify('Invitation not found', type='negative')
        return

    with ui.dialog() as dialog, ui.card().classes('w-96'):
        ui.label('Delete Invitation').classes('text-xl font-bold mb-4')
        ui.label(f'Are you sure you want to delete the invitation for:').classes('mb-2')
        ui.label(f'Email: {guest_group.mail_address_invited}').classes('mb-4')
        ui.label('This action cannot be undone.').classes('text-red-500 mb-4')

        with ui.row().classes('w-full justify-end gap-2'):
            ui.button('Cancel', on_click=dialog.close).classes('bg-gray-500 text-white')
            ui.button('Delete', on_click=lambda: delete_invitation(
                data_manager, dialog, guest_group_id
            )).classes('bg-red-600 text-white')

    dialog.open()


def send_invitation(data_manager: DataManager, group_id: str, guest_type: str,
                    existing_guest_id: Optional[str], new_guest_id: str,
                    given_name: str, surname: str, email: str, invite_email: str):
    """Send an invitation to a guest"""

    # Determine the email to send invitation to
    target_email = invite_email.strip() if invite_email.strip() else email.strip()

    if not target_email:
        ui.notify('Email address is required', type='negative')
        return

    guest_id_to_use = None

    if guest_type == 'existing':
        if not existing_guest_id:
            ui.notify('Please select an existing guest', type='negative')
            return
        guest_id_to_use = existing_guest_id
    else:
        # Create new guest
        if not all([given_name.strip(), surname.strip(), email.strip()]):
            ui.notify('Given name, surname, and email are required for new guests', type='negative')
            return

        guest_id_to_use = new_guest_id.strip() if new_guest_id.strip() else email.split('@')[0]

        # Check if guest already exists
        if data_manager.get_guest(guest_id_to_use):
            ui.notify(f'Guest with ID "{guest_id_to_use}" already exists', type='negative')
            return

        # Create the new guest
        new_guest = Guest(
            guest_id=guest_id_to_use,
            given_name=given_name.strip(),
            surname=surname.strip(),
            mail_address_preferred=email.strip(),
            verification_status={
                'verify_idin': False,
                'verify_institution': False,
                'verify_mfa': False
            }
        )

        if not data_manager.add_guest(new_guest):
            ui.notify('Failed to create guest', type='negative')
            return

    # Check if invitation already exists
    existing_invitations = data_manager.get_guest_groups_by_group(group_id)
    for invitation in existing_invitations:
        if invitation.mail_address_invited == target_email:
            ui.notify('An invitation has already been sent to this email address', type='negative')
            return

    # Create the invitation
    invite_code = data_manager.generate_invite_code()
    guest_group = GuestGroup(
        id='',  # Will be generated
        group_id=group_id,
        mail_address_invited=target_email,
        datetime_invited=data_manager.get_current_timestamp(),
        datetime_accepted=None
    )

    if data_manager.add_guest_group(guest_group):
        ui.notify(f'Invitation sent successfully to {target_email}', type='positive')
        ui.notify(f'Invite code: {invite_code}', type='info')  # In real app, this would be sent via email
        ui.navigate.to(f'/guests/{group_id}')
    else:
        ui.notify('Failed to send invitation', type='negative')


def delete_invitation(data_manager: DataManager, dialog, guest_group_id: str):
    """Delete a guest invitation"""

    if data_manager.delete_guest_group(guest_group_id):
        ui.notify('Invitation deleted successfully', type='positive')
        dialog.close()
        ui.navigate.to('/guests')  # Refresh the page
    else:
        ui.notify('Failed to delete invitation', type='negative')
