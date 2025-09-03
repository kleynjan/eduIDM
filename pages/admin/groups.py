"""
Admin Groups Page
Manage groups - group info and settings
"""

from nicegui import ui
from data_manager import DataManager, Group
from typing import Optional


def render_page(data_manager: DataManager, group_id: Optional[str] = None):
    """Render the admin groups page"""

    if group_id:
        render_group_detail(data_manager, group_id)
    else:
        render_groups_list(data_manager)


def render_groups_list(data_manager: DataManager):
    """Render the groups list page"""

    # Page header
    ui.label('Group Management').classes('text-3xl font-bold mb-6')

    # Navigation
    with ui.row().classes('mb-4 gap-2'):
        ui.button('← Back to Home', on_click=lambda: ui.navigate.to('/')).classes('bg-gray-500 text-white')
        ui.button('Users', on_click=lambda: ui.navigate.to('/admin/users')).classes('bg-blue-500 text-white')
        ui.button('Roles', on_click=lambda: ui.navigate.to('/admin/roles')).classes('bg-orange-500 text-white')
        ui.button('Guests', on_click=lambda: ui.navigate.to('/guests')).classes('bg-purple-500 text-white')

    # Add new group button
    ui.button('+ Add New Group', on_click=lambda: show_add_group_dialog(data_manager)
              ).classes('bg-blue-600 text-white mb-4')

    # Groups table
    groups = data_manager.get_groups()

    if not groups:
        ui.label('No groups found.').classes('text-gray-500 text-lg')
        return

    # Create table
    columns = [
        {'name': 'name', 'label': 'Group Name', 'field': 'name', 'required': True, 'align': 'left'},
        {'name': 'validity_days', 'label': 'Validity (Days)', 'field': 'validity_days', 'align': 'center'},
        {'name': 'idin_required', 'label': 'iDIN Required', 'field': 'idin_required', 'align': 'center'},
        {'name': 'mfa_required', 'label': 'MFA Required', 'field': 'mfa_required', 'align': 'center'},
        {'name': 'can_edit_mail', 'label': 'Can Edit Email', 'field': 'can_edit_mail', 'align': 'center'},
        {'name': 'actions', 'label': 'Actions', 'field': 'actions', 'align': 'center'},
    ]

    # Convert groups to table rows
    rows = []
    for group in groups:
        rows.append({
            'id': group.id,
            'name': group.name,
            'validity_days': group.validity_days,
            'idin_required': '✓' if group.idin_required else '✗',
            'mfa_required': '✓' if group.mfa_required else '✗',
            'can_edit_mail': '✓' if group.can_edit_mail_address else '✗',
            'actions': group.id
        })

    table = ui.table(columns=columns, rows=rows, row_key='id').classes('w-full')

    # Add action buttons to each row
    table.add_slot('body-cell-actions', '''
        <q-td :props="props">
            <q-btn flat round dense icon="visibility" color="blue" @click="$parent.$emit('view-group', props.row)" />
            <q-btn flat round dense icon="edit" color="green" @click="$parent.$emit('edit-group', props.row)" />
            <q-btn flat round dense icon="delete" color="red" @click="$parent.$emit('delete-group', props.row)" />
        </q-td>
    ''')

    # Handle table events
    table.on('view-group', lambda e: ui.navigate.to(f'/groups/{e.args["id"]}'))
    table.on('edit-group', lambda e: show_edit_group_dialog(data_manager, e.args['id']))
    table.on('delete-group', lambda e: show_delete_group_dialog(data_manager, e.args['id']))


def render_group_detail(data_manager: DataManager, group_id: str):
    """Render the group detail page"""

    group = data_manager.get_group(group_id)
    if not group:
        ui.label('Group not found').classes('text-red-500 text-xl')
        ui.button('← Back to Groups', on_click=lambda: ui.navigate.to('/groups')).classes('bg-gray-500 text-white mt-4')
        return

    # Page header
    ui.label(f'Group Details: {group.name}').classes('text-3xl font-bold mb-6')

    # Navigation
    with ui.row().classes('mb-4 gap-2'):
        ui.button('← Back to Groups', on_click=lambda: ui.navigate.to('/groups')).classes('bg-gray-500 text-white')
        ui.button('Edit Group', on_click=lambda: show_edit_group_dialog(
            data_manager, group_id)).classes('bg-blue-500 text-white')
        ui.button('View Guests', on_click=lambda: ui.navigate.to(
            f'/guests/{group_id}')).classes('bg-purple-500 text-white')

    # Group information cards
    with ui.row().classes('w-full gap-4'):
        # Basic Information
        with ui.card().classes('flex-1'):
            ui.label('Basic Information').classes('text-xl font-bold mb-4')
            ui.label(f'Name: {group.name}').classes('mb-2')
            ui.label(f'ID: {group.id}').classes('mb-2 text-gray-600 text-sm')
            ui.label(f'Validity Period: {group.validity_days} days').classes('mb-2')

        # Security Settings
        with ui.card().classes('flex-1'):
            ui.label('Security Settings').classes('text-xl font-bold mb-4')
            ui.label(f'iDIN Required: {"Yes" if group.idin_required else "No"}').classes('mb-2')
            ui.label(f'MFA Required: {"Yes" if group.mfa_required else "No"}').classes('mb-2')
            ui.label(f'Can Edit Email: {"Yes" if group.can_edit_mail_address else "No"}').classes('mb-2')

    # Email Templates
    with ui.card().classes('w-full mt-4'):
        ui.label('Email Templates').classes('text-xl font-bold mb-4')
        ui.label(f'HTML Template: {group.mail_template_file_html}').classes('mb-2')
        ui.label(f'Text Template: {group.mail_template_file_txt}').classes('mb-2')

    # Group statistics
    guest_groups = data_manager.get_guest_groups_by_group(group_id)
    with ui.card().classes('w-full mt-4'):
        ui.label('Statistics').classes('text-xl font-bold mb-4')
        ui.label(f'Total Invitations: {len(guest_groups)}').classes('mb-2')
        accepted_count = len([gg for gg in guest_groups if gg.datetime_accepted])
        ui.label(f'Accepted Invitations: {accepted_count}').classes('mb-2')
        ui.label(f'Pending Invitations: {len(guest_groups) - accepted_count}').classes('mb-2')


def show_add_group_dialog(data_manager: DataManager):
    """Show dialog to add a new group"""

    with ui.dialog() as dialog, ui.card().classes('w-96'):
        ui.label('Add New Group').classes('text-xl font-bold mb-4')

        name_input = ui.input('Group Name').classes('w-full mb-2')
        validity_input = ui.number('Validity Days', value=30, min=1, max=365).classes('w-full mb-2')
        html_template_input = ui.input('HTML Template File', value='invite_mail.html').classes('w-full mb-2')
        txt_template_input = ui.input('Text Template File', value='invite_mail.txt').classes('w-full mb-2')

        idin_checkbox = ui.checkbox('iDIN Required', value=False).classes('mb-2')
        mfa_checkbox = ui.checkbox('MFA Required', value=False).classes('mb-2')
        edit_mail_checkbox = ui.checkbox('Can Edit Email Address', value=True).classes('mb-4')

        with ui.row().classes('w-full justify-end gap-2'):
            ui.button('Cancel', on_click=dialog.close).classes('bg-gray-500 text-white')
            ui.button('Add Group', on_click=lambda: add_group(
                data_manager, dialog,
                name_input.value,
                validity_input.value,
                html_template_input.value,
                txt_template_input.value,
                idin_checkbox.value,
                mfa_checkbox.value,
                edit_mail_checkbox.value
            )).classes('bg-blue-600 text-white')

    dialog.open()


def show_edit_group_dialog(data_manager: DataManager, group_id: str):
    """Show dialog to edit an existing group"""

    group = data_manager.get_group(group_id)
    if not group:
        ui.notify('Group not found', type='negative')
        return

    with ui.dialog() as dialog, ui.card().classes('w-96'):
        ui.label('Edit Group').classes('text-xl font-bold mb-4')

        name_input = ui.input('Group Name', value=group.name).classes('w-full mb-2')
        validity_input = ui.number('Validity Days', value=group.validity_days, min=1, max=365).classes('w-full mb-2')
        html_template_input = ui.input('HTML Template File', value=group.mail_template_file_html).classes('w-full mb-2')
        txt_template_input = ui.input('Text Template File', value=group.mail_template_file_txt).classes('w-full mb-2')

        idin_checkbox = ui.checkbox('iDIN Required', value=group.idin_required).classes('mb-2')
        mfa_checkbox = ui.checkbox('MFA Required', value=group.mfa_required).classes('mb-2')
        edit_mail_checkbox = ui.checkbox('Can Edit Email Address', value=group.can_edit_mail_address).classes('mb-4')

        with ui.row().classes('w-full justify-end gap-2'):
            ui.button('Cancel', on_click=dialog.close).classes('bg-gray-500 text-white')
            ui.button('Update Group', on_click=lambda: update_group(
                data_manager, dialog, group_id,
                name_input.value,
                validity_input.value,
                html_template_input.value,
                txt_template_input.value,
                idin_checkbox.value,
                mfa_checkbox.value,
                edit_mail_checkbox.value
            )).classes('bg-blue-600 text-white')

    dialog.open()


def show_delete_group_dialog(data_manager: DataManager, group_id: str):
    """Show confirmation dialog to delete a group"""

    group = data_manager.get_group(group_id)
    if not group:
        ui.notify('Group not found', type='negative')
        return

    # Check if group has associated data
    guest_groups = data_manager.get_guest_groups_by_group(group_id)
    admin_roles = [role for role in data_manager.get_admin_roles() if role.group_id == group_id]

    with ui.dialog() as dialog, ui.card().classes('w-96'):
        ui.label('Delete Group').classes('text-xl font-bold mb-4')
        ui.label(f'Are you sure you want to delete group "{group.name}"?').classes('mb-4')

        if guest_groups or admin_roles:
            ui.label('Warning: This group has associated data:').classes('text-orange-500 mb-2')
            if guest_groups:
                ui.label(f'• {len(guest_groups)} guest invitations').classes('text-orange-500 mb-1')
            if admin_roles:
                ui.label(f'• {len(admin_roles)} admin roles').classes('text-orange-500 mb-1')
            ui.label('All associated data will be deleted.').classes('text-orange-500 mb-4')

        ui.label('This action cannot be undone.').classes('text-red-500 mb-4')

        with ui.row().classes('w-full justify-end gap-2'):
            ui.button('Cancel', on_click=dialog.close).classes('bg-gray-500 text-white')
            ui.button('Delete', on_click=lambda: delete_group(
                data_manager, dialog, group_id
            )).classes('bg-red-600 text-white')

    dialog.open()


def add_group(data_manager: DataManager, dialog, name: str, validity_days: int,
              html_template: str, txt_template: str, idin_required: bool,
              mfa_required: bool, can_edit_mail: bool):
    """Add a new group"""

    if not all([name, html_template, txt_template]):
        ui.notify('Name and template files are required', type='negative')
        return

    if validity_days < 1 or validity_days > 365:
        ui.notify('Validity days must be between 1 and 365', type='negative')
        return

    group = Group(
        id='',  # Will be generated by data_manager
        name=name,
        mail_template_file_html=html_template,
        mail_template_file_txt=txt_template,
        idin_required=idin_required,
        mfa_required=mfa_required,
        can_edit_mail_address=can_edit_mail,
        validity_days=validity_days
    )

    if data_manager.add_group(group):
        ui.notify('Group added successfully', type='positive')
        dialog.close()
        ui.navigate.to('/groups')  # Refresh the page
    else:
        ui.notify('Failed to add group', type='negative')


def update_group(data_manager: DataManager, dialog, group_id: str, name: str,
                 validity_days: int, html_template: str, txt_template: str,
                 idin_required: bool, mfa_required: bool, can_edit_mail: bool):
    """Update an existing group"""

    if not all([name, html_template, txt_template]):
        ui.notify('Name and template files are required', type='negative')
        return

    if validity_days < 1 or validity_days > 365:
        ui.notify('Validity days must be between 1 and 365', type='negative')
        return

    group = Group(
        id=group_id,
        name=name,
        mail_template_file_html=html_template,
        mail_template_file_txt=txt_template,
        idin_required=idin_required,
        mfa_required=mfa_required,
        can_edit_mail_address=can_edit_mail,
        validity_days=validity_days
    )

    if data_manager.update_group(group):
        ui.notify('Group updated successfully', type='positive')
        dialog.close()
        ui.navigate.to('/groups')  # Refresh the page
    else:
        ui.notify('Failed to update group', type='negative')


def delete_group(data_manager: DataManager, dialog, group_id: str):
    """Delete a group and all associated data"""

    # Delete associated guest groups first
    guest_groups = data_manager.get_guest_groups_by_group(group_id)
    for gg in guest_groups:
        data_manager.delete_guest_group(gg.id)

    # Delete associated admin roles
    admin_roles = [role for role in data_manager.get_admin_roles() if role.group_id == group_id]
    for role in admin_roles:
        data_manager.delete_admin_role(role.user_id, role.group_id)

    # Delete the group itself
    if data_manager.delete_group(group_id):
        ui.notify('Group and all associated data deleted successfully', type='positive')
        dialog.close()
        ui.navigate.to('/groups')  # Refresh the page
    else:
        ui.notify('Failed to delete group', type='negative')
