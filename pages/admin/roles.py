"""
Admin Roles Page
Manage admin roles - who can see/invite what group
"""

from nicegui import ui
from data_manager import DataManager, AdminRole
from typing import Optional


def render_page(data_manager: DataManager):
    """Render the admin roles page"""

    # Page header
    ui.label('Role Management').classes('text-3xl font-bold mb-6')

    # Navigation
    with ui.row().classes('mb-4 gap-2'):
        ui.button('← Back to Home', on_click=lambda: ui.navigate.to('/')).classes('bg-gray-500 text-white')
        ui.button('Users', on_click=lambda: ui.navigate.to('/admin/users')).classes('bg-blue-500 text-white')
        ui.button('Groups', on_click=lambda: ui.navigate.to('/groups')).classes('bg-green-500 text-white')
        ui.button('Guests', on_click=lambda: ui.navigate.to('/guests')).classes('bg-purple-500 text-white')

    # Add new role button
    ui.button('+ Add New Role', on_click=lambda: show_add_role_dialog(data_manager)
              ).classes('bg-blue-600 text-white mb-4')

    # Admin roles table
    admin_roles = data_manager.get_admin_roles()
    users = data_manager.get_users()
    groups = data_manager.get_groups()

    # Create lookup dictionaries for display
    user_lookup = {user.id: f"{user.username} ({user.given_name} {user.surname})" for user in users}
    group_lookup = {group.id: group.name for group in groups}

    if not admin_roles:
        ui.label('No admin roles found.').classes('text-gray-500 text-lg')
        return

    # Create table
    columns = [
        {'name': 'user', 'label': 'User', 'field': 'user', 'required': True, 'align': 'left'},
        {'name': 'group', 'label': 'Group', 'field': 'group', 'align': 'left'},
        {'name': 'admin_role', 'label': 'Role', 'field': 'admin_role', 'align': 'left'},
        {'name': 'actions', 'label': 'Actions', 'field': 'actions', 'align': 'center'},
    ]

    # Convert admin roles to table rows
    rows = []
    for role in admin_roles:
        rows.append({
            'user_id': role.user_id,
            'group_id': role.group_id,
            'user': user_lookup.get(role.user_id, f"Unknown User ({role.user_id})"),
            'group': group_lookup.get(role.group_id, f"Unknown Group ({role.group_id})"),
            'admin_role': role.admin_role,
            'actions': f"{role.user_id}|{role.group_id}"  # Combined key for actions
        })

    table = ui.table(columns=columns, rows=rows, row_key='actions').classes('w-full')

    # Add action buttons to each row
    table.add_slot('body-cell-actions', '''
        <q-td :props="props">
            <q-btn flat round dense icon="delete" color="red" @click="$parent.$emit('delete-role', props.row)" />
        </q-td>
    ''')

    # Handle table events
    table.on('delete-role', lambda e: show_delete_role_dialog(data_manager, e.args['user_id'], e.args['group_id']))


def show_add_role_dialog(data_manager: DataManager):
    """Show dialog to add a new admin role"""

    users = data_manager.get_users()
    groups = data_manager.get_groups()

    if not users:
        ui.notify('No users available. Please add users first.', type='warning')
        return

    if not groups:
        ui.notify('No groups available. Please add groups first.', type='warning')
        return

    with ui.dialog() as dialog, ui.card().classes('w-96'):
        ui.label('Add New Admin Role').classes('text-xl font-bold mb-4')

        # User selection
        user_options = {user.id: f"{user.username} ({user.given_name} {user.surname})" for user in users}
        user_select = ui.select(user_options, label='Select User').classes('w-full mb-2')

        # Group selection
        group_options = {group.id: group.name for group in groups}
        group_select = ui.select(group_options, label='Select Group').classes('w-full mb-2')

        # Role selection
        role_options = {
            'admin': 'Admin',
            'superuser': 'Superuser',
            'moderator': 'Moderator'
        }
        role_select = ui.select(role_options, label='Select Role').classes('w-full mb-4')

        with ui.row().classes('w-full justify-end gap-2'):
            ui.button('Cancel', on_click=dialog.close).classes('bg-gray-500 text-white')
            ui.button('Add Role', on_click=lambda: add_role(
                data_manager, dialog,
                user_select.value,
                group_select.value,
                role_select.value
            )).classes('bg-blue-600 text-white')

    dialog.open()


def show_delete_role_dialog(data_manager: DataManager, user_id: str, group_id: str):
    """Show confirmation dialog to delete an admin role"""

    # Get user and group info for display
    user = data_manager.get_user(user_id)
    group = data_manager.get_group(group_id)

    user_display = f"{user.username} ({user.given_name} {user.surname})" if user else f"Unknown User ({user_id})"
    group_display = group.name if group else f"Unknown Group ({group_id})"

    with ui.dialog() as dialog, ui.card().classes('w-96'):
        ui.label('Delete Admin Role').classes('text-xl font-bold mb-4')
        ui.label(f'Are you sure you want to remove admin role for:').classes('mb-2')
        ui.label(f'User: {user_display}').classes('mb-2')
        ui.label(f'Group: {group_display}').classes('mb-4')
        ui.label('This action cannot be undone.').classes('text-red-500 mb-4')

        with ui.row().classes('w-full justify-end gap-2'):
            ui.button('Cancel', on_click=dialog.close).classes('bg-gray-500 text-white')
            ui.button('Delete', on_click=lambda: delete_role(
                data_manager, dialog, user_id, group_id
            )).classes('bg-red-600 text-white')

    dialog.open()


def add_role(data_manager: DataManager, dialog, user_id: str, group_id: str, admin_role: str):
    """Add a new admin role"""

    if not all([user_id, group_id, admin_role]):
        ui.notify('All fields are required', type='negative')
        return

    # Check if role already exists
    existing_roles = data_manager.get_admin_roles()
    for role in existing_roles:
        if role.user_id == user_id and role.group_id == group_id:
            ui.notify('This user already has a role for this group', type='negative')
            return

    role = AdminRole(
        user_id=user_id,
        group_id=group_id,
        admin_role=admin_role
    )

    if data_manager.add_admin_role(role):
        ui.notify('Admin role added successfully', type='positive')
        dialog.close()
        ui.navigate.to('/admin/roles')  # Refresh the page
    else:
        ui.notify('Failed to add admin role', type='negative')


def delete_role(data_manager: DataManager, dialog, user_id: str, group_id: str):
    """Delete an admin role"""

    if data_manager.delete_admin_role(user_id, group_id):
        ui.notify('Admin role deleted successfully', type='positive')
        dialog.close()
        ui.navigate.to('/admin/roles')  # Refresh the page
    else:
        ui.notify('Failed to delete admin role', type='negative')
