"""
Guest Profile Page
Self-service page showing info registered about the user, optionally delete group memberships
"""

from nicegui import ui
from data_manager import DataManager
from typing import Optional


def render_page(data_manager: DataManager, user_id: str):
    """Render the user profile page"""

    # Find the guest
    guest = data_manager.get_guest(user_id)
    if not guest:
        render_guest_not_found()
        return

    # Get guest's group memberships
    guest_groups = [gg for gg in data_manager.get_guest_groups()
                    if gg.mail_address_invited.split('@')[0] == user_id or
                    gg.mail_address_invited == guest.mail_address_preferred]

    groups = data_manager.get_groups()
    groups_lookup = {group.id: group for group in groups}

    render_profile_page(data_manager, guest, guest_groups, groups_lookup)


def render_guest_not_found():
    """Render guest not found page"""

    ui.label('Profile Not Found').classes('text-3xl font-bold mb-6 text-red-500')
    ui.label('The user profile you requested could not be found.').classes('text-lg mb-4')
    ui.label('Please check the URL or contact support for assistance.').classes('text-gray-600 mb-4')

    ui.button('← Back to Home', on_click=lambda: ui.navigate.to('/')).classes('bg-gray-500 text-white')


def render_profile_page(data_manager: DataManager, guest, guest_groups, groups_lookup):
    """Render the main profile page"""

    ui.label('My Profile').classes('text-3xl font-bold mb-6')

    # Personal Information
    with ui.card().classes('w-full max-w-4xl mb-6'):
        ui.label('Personal Information').classes('text-xl font-bold mb-4')

        with ui.row().classes('w-full gap-8'):
            # Basic info
            with ui.column().classes('flex-1'):
                ui.label('Basic Details').classes('text-lg font-semibold mb-3')
                ui.label(f'Guest ID: {guest.guest_id}').classes('mb-2')

                if guest.given_name or guest.surname:
                    full_name = f"{guest.given_name or ''} {guest.surname or ''}".strip()
                    ui.label(f'Name: {full_name}').classes('mb-2')

                if guest.mail_address_preferred:
                    ui.label(f'Preferred Email: {guest.mail_address_preferred}').classes('mb-2')

            # eduID information
            with ui.column().classes('flex-1'):
                ui.label('eduID Information').classes('text-lg font-semibold mb-3')

                if guest.eduid_nameid:
                    ui.label(f'eduID NameID: {guest.eduid_nameid}').classes('mb-2 text-sm font-mono')

                if guest.eduid_given_name or guest.eduid_surname:
                    eduid_name = f"{guest.eduid_given_name or ''} {guest.eduid_surname or ''}".strip()
                    ui.label(f'eduID Name: {eduid_name}').classes('mb-2')

                if guest.eduid_mail_address:
                    ui.label(f'eduID Email: {guest.eduid_mail_address}').classes('mb-2')

    # Verification Status
    if guest.verification_status:
        with ui.card().classes('w-full max-w-4xl mb-6'):
            ui.label('Verification Status').classes('text-xl font-bold mb-4')

            with ui.row().classes('w-full gap-4'):
                # Institution verification
                status = guest.verification_status.get('verify_institution', False)
                icon = '✅' if status else '❌'
                color = 'text-green-600' if status else 'text-red-600'
                ui.label(f'{icon} Institution Verification').classes(f'mb-2 {color}')

                # iDIN verification
                status = guest.verification_status.get('verify_idin', False)
                icon = '✅' if status else '❌'
                color = 'text-green-600' if status else 'text-red-600'
                ui.label(f'{icon} iDIN Verification').classes(f'mb-2 {color}')

                # MFA verification
                status = guest.verification_status.get('verify_mfa', False)
                icon = '✅' if status else '❌'
                color = 'text-green-600' if status else 'text-red-600'
                ui.label(f'{icon} Multi-Factor Authentication').classes(f'mb-2 {color}')

    # Group Memberships
    with ui.card().classes('w-full max-w-4xl mb-6'):
        ui.label('Group Memberships').classes('text-xl font-bold mb-4')

        if not guest_groups:
            ui.label('You are not currently a member of any groups.').classes('text-gray-500 text-lg')
        else:
            # Create memberships table
            columns = [
                {'name': 'group_name', 'label': 'Group Name', 'field': 'group_name', 'required': True, 'align': 'left'},
                {'name': 'email_used', 'label': 'Email Used', 'field': 'email_used', 'align': 'left'},
                {'name': 'invited_date', 'label': 'Invited Date', 'field': 'invited_date', 'align': 'center'},
                {'name': 'accepted_date', 'label': 'Accepted Date', 'field': 'accepted_date', 'align': 'center'},
                {'name': 'status', 'label': 'Status', 'field': 'status', 'align': 'center'},
                {'name': 'actions', 'label': 'Actions', 'field': 'actions', 'align': 'center'},
            ]

            # Convert guest groups to table rows
            rows = []
            for gg in guest_groups:
                group = groups_lookup.get(gg.group_id)
                group_name = group.name if group else f"Unknown Group ({gg.group_id})"

                status = 'Active' if gg.datetime_accepted else 'Pending'
                invited_date = gg.datetime_invited.split('T')[0] if gg.datetime_invited else 'N/A'
                accepted_date = gg.datetime_accepted.split('T')[0] if gg.datetime_accepted else 'N/A'

                rows.append({
                    'id': gg.id,
                    'group_id': gg.group_id,
                    'group_name': group_name,
                    'email_used': gg.mail_address_invited,
                    'invited_date': invited_date,
                    'accepted_date': accepted_date,
                    'status': status,
                    'actions': gg.id
                })

            table = ui.table(columns=columns, rows=rows, row_key='id').classes('w-full')

            # Add action buttons to each row
            table.add_slot('body-cell-actions', '''
                <q-td :props="props">
                    <q-btn flat round dense icon="info" color="blue" @click="$parent.$emit('view-group', props.row)" />
                    <q-btn flat round dense icon="exit_to_app" color="red" @click="$parent.$emit('leave-group', props.row)" />
                </q-td>
            ''')

            # Handle table events
            table.on('view-group', lambda e: show_group_details(data_manager, e.args['group_id']))
            table.on('leave-group', lambda e: show_leave_group_dialog(data_manager,
                     guest, e.args['id'], e.args['group_name']))

    # Account Actions
    with ui.card().classes('w-full max-w-4xl mb-6'):
        ui.label('Account Actions').classes('text-xl font-bold mb-4')

        with ui.row().classes('gap-4'):
            ui.button('Edit Profile', on_click=lambda: show_edit_profile_dialog(
                data_manager, guest)).classes('bg-blue-500 text-white')
            ui.button('Delete All Data', on_click=lambda: show_delete_account_dialog(
                data_manager, guest)).classes('bg-red-500 text-white')

    # Navigation
    ui.button('← Back to Home', on_click=lambda: ui.navigate.to('/')).classes('bg-gray-500 text-white mt-4')


def show_group_details(data_manager: DataManager, group_id: str):
    """Show group details dialog"""

    group = data_manager.get_group(group_id)
    if not group:
        ui.notify('Group not found', type='negative')
        return

    with ui.dialog() as dialog, ui.card().classes('w-96'):
        ui.label(f'Group Details: {group.name}').classes('text-xl font-bold mb-4')

        ui.label(f'Validity Period: {group.validity_days} days').classes('mb-2')
        ui.label(f'iDIN Required: {"Yes" if group.idin_required else "No"}').classes('mb-2')
        ui.label(f'MFA Required: {"Yes" if group.mfa_required else "No"}').classes('mb-2')
        ui.label(f'Can Edit Email: {"Yes" if group.can_edit_mail_address else "No"}').classes('mb-4')

        ui.button('Close', on_click=dialog.close).classes('bg-gray-500 text-white')

    dialog.open()


def show_leave_group_dialog(data_manager: DataManager, guest, guest_group_id: str, group_name: str):
    """Show leave group confirmation dialog"""

    with ui.dialog() as dialog, ui.card().classes('w-96'):
        ui.label('Leave Group').classes('text-xl font-bold mb-4')
        ui.label(f'Are you sure you want to leave "{group_name}"?').classes('mb-4')
        ui.label('This will remove your access to the group and cannot be undone.').classes('text-red-500 mb-4')
        ui.label('You would need to be re-invited to rejoin.').classes('text-gray-600 mb-4')

        with ui.row().classes('w-full justify-end gap-2'):
            ui.button('Cancel', on_click=dialog.close).classes('bg-gray-500 text-white')
            ui.button('Leave Group', on_click=lambda: leave_group(
                data_manager, dialog, guest, guest_group_id
            )).classes('bg-red-600 text-white')

    dialog.open()


def show_edit_profile_dialog(data_manager: DataManager, guest):
    """Show edit profile dialog"""

    with ui.dialog() as dialog, ui.card().classes('w-96'):
        ui.label('Edit Profile').classes('text-xl font-bold mb-4')

        given_name_input = ui.input('Given Name', value=guest.given_name or '').classes('w-full mb-2')
        surname_input = ui.input('Surname', value=guest.surname or '').classes('w-full mb-2')
        email_input = ui.input('Preferred Email', value=guest.mail_address_preferred or '').classes('w-full mb-4')

        with ui.row().classes('w-full justify-end gap-2'):
            ui.button('Cancel', on_click=dialog.close).classes('bg-gray-500 text-white')
            ui.button('Save Changes', on_click=lambda: save_profile_changes(
                data_manager, dialog, guest,
                given_name_input.value,
                surname_input.value,
                email_input.value
            )).classes('bg-blue-600 text-white')

    dialog.open()


def show_delete_account_dialog(data_manager: DataManager, guest):
    """Show delete account confirmation dialog"""

    with ui.dialog() as dialog, ui.card().classes('w-96'):
        ui.label('Delete Account').classes('text-xl font-bold mb-4')
        ui.label('Are you sure you want to delete your account?').classes('mb-4')
        ui.label('This will:').classes('mb-2 font-semibold')
        ui.label('• Remove all your personal information').classes('mb-1 text-red-500')
        ui.label('• Remove you from all groups').classes('mb-1 text-red-500')
        ui.label('• Delete all invitation history').classes('mb-1 text-red-500')
        ui.label('This action cannot be undone!').classes('mb-4 text-red-600 font-bold')

        with ui.row().classes('w-full justify-end gap-2'):
            ui.button('Cancel', on_click=dialog.close).classes('bg-gray-500 text-white')
            ui.button('Delete Account', on_click=lambda: delete_account(
                data_manager, dialog, guest
            )).classes('bg-red-600 text-white')

    dialog.open()


def leave_group(data_manager: DataManager, dialog, guest, guest_group_id: str):
    """Leave a group"""

    if data_manager.delete_guest_group(guest_group_id):
        ui.notify('Successfully left the group', type='positive')
        dialog.close()
        ui.navigate.to(f'/my/{guest.guest_id}')  # Refresh the page
    else:
        ui.notify('Failed to leave group', type='negative')


def save_profile_changes(data_manager: DataManager, dialog, guest, given_name: str, surname: str, email: str):
    """Save profile changes"""

    # Update guest information
    guest.given_name = given_name.strip() if given_name.strip() else None
    guest.surname = surname.strip() if surname.strip() else None
    guest.mail_address_preferred = email.strip() if email.strip() else None

    if data_manager.update_guest(guest):
        ui.notify('Profile updated successfully', type='positive')
        dialog.close()
        ui.navigate.to(f'/my/{guest.guest_id}')  # Refresh the page
    else:
        ui.notify('Failed to update profile', type='negative')


def delete_account(data_manager: DataManager, dialog, guest):
    """Delete the user account and all associated data"""

    # Delete all guest group memberships
    guest_groups = [gg for gg in data_manager.get_guest_groups()
                    if gg.mail_address_invited.split('@')[0] == guest.guest_id or
                    gg.mail_address_invited == guest.mail_address_preferred]

    for gg in guest_groups:
        data_manager.delete_guest_group(gg.id)

    # Delete the guest record
    if data_manager.delete_guest(guest.guest_id):
        ui.notify('Account deleted successfully', type='positive')
        dialog.close()
        ui.navigate.to('/')  # Redirect to home
    else:
        ui.notify('Failed to delete account', type='negative')
