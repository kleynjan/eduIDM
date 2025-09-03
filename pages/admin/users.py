"""
Admin Users Page
Manage backend users and their information
"""

from nicegui import ui
from data_manager import DataManager, User
from typing import Optional


def render_page(data_manager: DataManager):
    """Render the admin users page"""

    # Page header
    ui.label('User Management').classes('text-3xl font-bold mb-6')

    # Navigation
    with ui.row().classes('mb-4 gap-2'):
        ui.button('← Back to Home', on_click=lambda: ui.navigate.to('/')).classes('bg-gray-500 text-white')
        ui.button('Roles', on_click=lambda: ui.navigate.to('/admin/roles')).classes('bg-blue-500 text-white')
        ui.button('Groups', on_click=lambda: ui.navigate.to('/groups')).classes('bg-green-500 text-white')
        ui.button('Guests', on_click=lambda: ui.navigate.to('/guests')).classes('bg-purple-500 text-white')

    # Add new user button
    ui.button('+ Add New User', on_click=lambda: show_add_user_dialog(data_manager)
              ).classes('bg-blue-600 text-white mb-4')

    # Users table
    users = data_manager.get_users()

    if not users:
        ui.label('No users found.').classes('text-gray-500 text-lg')
        return

    # Create table
    columns = [
        {'name': 'username', 'label': 'Username', 'field': 'username', 'required': True, 'align': 'left'},
        {'name': 'given_name', 'label': 'Given Name', 'field': 'given_name', 'align': 'left'},
        {'name': 'surname', 'label': 'Surname', 'field': 'surname', 'align': 'left'},
        {'name': 'mail', 'label': 'Email', 'field': 'mail', 'align': 'left'},
        {'name': 'eduid_nameid', 'label': 'EduID NameID', 'field': 'eduid_nameid', 'align': 'left'},
        {'name': 'actions', 'label': 'Actions', 'field': 'actions', 'align': 'center'},
    ]

    # Convert users to table rows
    rows = []
    for user in users:
        rows.append({
            'id': user.id,
            'username': user.username,
            'given_name': user.given_name,
            'surname': user.surname,
            'mail': user.mail,
            'eduid_nameid': user.eduid_nameid,
            'actions': user.id  # We'll use this for action buttons
        })

    table = ui.table(columns=columns, rows=rows, row_key='id').classes('w-full')

    # Add action buttons to each row
    table.add_slot('body-cell-actions', '''
        <q-td :props="props">
            <q-btn flat round dense icon="edit" color="blue" @click="$parent.$emit('edit-user', props.row)" />
            <q-btn flat round dense icon="delete" color="red" @click="$parent.$emit('delete-user', props.row)" />
        </q-td>
    ''')

    # Handle table events
    table.on('edit-user', lambda e: show_edit_user_dialog(data_manager, e.args['id']))
    table.on('delete-user', lambda e: show_delete_user_dialog(data_manager, e.args['id']))


def show_add_user_dialog(data_manager: DataManager):
    """Show dialog to add a new user"""

    with ui.dialog() as dialog, ui.card().classes('w-96'):
        ui.label('Add New User').classes('text-xl font-bold mb-4')

        username_input = ui.input('Username').classes('w-full mb-2')
        given_name_input = ui.input('Given Name').classes('w-full mb-2')
        surname_input = ui.input('Surname').classes('w-full mb-2')
        mail_input = ui.input('Email').classes('w-full mb-2')
        eduid_nameid_input = ui.input('EduID NameID').classes('w-full mb-4')

        with ui.row().classes('w-full justify-end gap-2'):
            ui.button('Cancel', on_click=dialog.close).classes('bg-gray-500 text-white')
            ui.button('Add User', on_click=lambda: add_user(
                data_manager, dialog,
                username_input.value,
                given_name_input.value,
                surname_input.value,
                mail_input.value,
                eduid_nameid_input.value
            )).classes('bg-blue-600 text-white')

    dialog.open()


def show_edit_user_dialog(data_manager: DataManager, user_id: str):
    """Show dialog to edit an existing user"""

    user = data_manager.get_user(user_id)
    if not user:
        ui.notify('User not found', type='negative')
        return

    with ui.dialog() as dialog, ui.card().classes('w-96'):
        ui.label('Edit User').classes('text-xl font-bold mb-4')

        username_input = ui.input('Username', value=user.username).classes('w-full mb-2')
        given_name_input = ui.input('Given Name', value=user.given_name).classes('w-full mb-2')
        surname_input = ui.input('Surname', value=user.surname).classes('w-full mb-2')
        mail_input = ui.input('Email', value=user.mail).classes('w-full mb-2')
        eduid_nameid_input = ui.input('EduID NameID', value=user.eduid_nameid).classes('w-full mb-4')

        with ui.row().classes('w-full justify-end gap-2'):
            ui.button('Cancel', on_click=dialog.close).classes('bg-gray-500 text-white')
            ui.button('Update User', on_click=lambda: update_user(
                data_manager, dialog, user_id,
                username_input.value,
                given_name_input.value,
                surname_input.value,
                mail_input.value,
                eduid_nameid_input.value
            )).classes('bg-blue-600 text-white')

    dialog.open()


def show_delete_user_dialog(data_manager: DataManager, user_id: str):
    """Show confirmation dialog to delete a user"""

    user = data_manager.get_user(user_id)
    if not user:
        ui.notify('User not found', type='negative')
        return

    with ui.dialog() as dialog, ui.card().classes('w-96'):
        ui.label('Delete User').classes('text-xl font-bold mb-4')
        ui.label(f'Are you sure you want to delete user "{user.username}"?').classes('mb-4')
        ui.label('This action cannot be undone.').classes('text-red-500 mb-4')

        with ui.row().classes('w-full justify-end gap-2'):
            ui.button('Cancel', on_click=dialog.close).classes('bg-gray-500 text-white')
            ui.button('Delete', on_click=lambda: delete_user(
                data_manager, dialog, user_id
            )).classes('bg-red-600 text-white')

    dialog.open()


def add_user(data_manager: DataManager, dialog, username: str, given_name: str,
             surname: str, mail: str, eduid_nameid: str):
    """Add a new user"""

    if not all([username, given_name, surname, mail, eduid_nameid]):
        ui.notify('All fields are required', type='negative')
        return

    user = User(
        id='',  # Will be generated by data_manager
        username=username,
        given_name=given_name,
        surname=surname,
        mail=mail,
        eduid_nameid=eduid_nameid
    )

    if data_manager.add_user(user):
        ui.notify('User added successfully', type='positive')
        dialog.close()
        ui.navigate.to('/admin/users')  # Refresh the page
    else:
        ui.notify('Failed to add user', type='negative')


def update_user(data_manager: DataManager, dialog, user_id: str, username: str,
                given_name: str, surname: str, mail: str, eduid_nameid: str):
    """Update an existing user"""

    if not all([username, given_name, surname, mail, eduid_nameid]):
        ui.notify('All fields are required', type='negative')
        return

    user = User(
        id=user_id,
        username=username,
        given_name=given_name,
        surname=surname,
        mail=mail,
        eduid_nameid=eduid_nameid
    )

    if data_manager.update_user(user):
        ui.notify('User updated successfully', type='positive')
        dialog.close()
        ui.navigate.to('/admin/users')  # Refresh the page
    else:
        ui.notify('Failed to update user', type='negative')


def delete_user(data_manager: DataManager, dialog, user_id: str):
    """Delete a user"""

    if data_manager.delete_user(user_id):
        ui.notify('User deleted successfully', type='positive')
        dialog.close()
        ui.navigate.to('/admin/users')  # Refresh the page
    else:
        ui.notify('Failed to delete user', type='negative')
