# /groups page

from nicegui import ui

from services.logging import logger
from services.storage import create_group, delete_group, get_all_groups, update_group
from .nav_header import create_navigation_header

TITLE = "Groepen"

@ui.page('/m/groups')
def groups_page():
    logger.debug("groups page accessed")

    ui.page_title(TITLE)
    page_state = {'groups': []}

    with ui.column().classes('mx-auto p-6').style('width:1160px;'):
        # Add navigation header
        create_navigation_header('groups')

        @ui.refreshable
        def groups_table():
            page_state['groups'] = get_all_groups()

            if not page_state['groups']:
                ui.label('Geen groepen gevonden.').classes('text-gray-500 text-center py-8')
            else:
                with ui.card().classes('w-full').style('font-size: 12pt;'):
                    # Table headers
                    with ui.row().classes('w-full font-bold border-b pb-2 mb-2'):
                        ui.label('naam').style('width: 20%;')
                        ui.label('redirect URL').style('width: 30%;')
                        ui.label('redirect text').style('width: 30%;')

                    # Table rows
                    for group in page_state['groups']:
                        with ui.row().classes('w-full border-b py-2'):
                            ui.label(group['name']).style('width: 20%;')
                            ui.label(group['redirect_url']).style('width: 30%;')
                            ui.label(group['redirect_text']).style('width: 30%;')
                            with ui.row().classes('gap-2').style('width: 15%;'):
                                ui.button(
                                    icon='edit', color='grey',
                                    on_click=lambda g=group: edit_group_dialog(g, page_state)
                                ).props('flat dense').classes('text-grey-300')
                                ui.button(
                                    icon='delete', color='grey',
                                    on_click=lambda g=group: delete_group_dialog(g, page_state)
                                ).props('flat dense').classes('text-grey-300')

        groups_table()
        ui.button('Nieuwe Groep...', on_click=lambda: add_group_dialog(
            page_state)).classes('mb-4 bg-blue-500 text-white')

        # Store reference to refresh function for later use
        page_state['refresh_function'] = groups_table.refresh   # type: ignore


def add_group_dialog(page_state):
    """Show the add group dialog"""
    logger.info("Opening add group dialog")

    dialog_state = {
        'name': '',
        'redirect_url': '',
        'redirect_text': ''
    }

    def handle_add():
        logger.info("Processing group creation")

        if not dialog_state['name'].strip():
            ui.notify('Groepsnaam is verplicht', type='negative')
            return

        if not dialog_state['redirect_url'].strip():
            ui.notify('Redirect URL is verplicht', type='negative')
            return

        if not dialog_state['redirect_text'].strip():
            ui.notify('Redirect Text is verplicht', type='negative')
            return

        try:
            # Create the group
            group_id = create_group(
                dialog_state['name'].strip(),
                dialog_state['redirect_url'].strip(),
                dialog_state['redirect_text'].strip()
            )
            logger.info(f"Group created successfully: {group_id}")
            add_dialog.close()
            ui.notify(f'Groep "{dialog_state["name"]}" is aangemaakt', type='positive')

            if 'refresh_function' in page_state:
                page_state['refresh_function']()

        except Exception as e:
            logger.error(f"Failed to create group: {e}")
            ui.notify(f'Fout bij het aanmaken van groep: {str(e)}', type='negative')

    def handle_cancel():
        logger.info("Add group dialog cancelled")
        add_dialog.close()

    # create dialog
    with ui.dialog() as add_dialog, ui.card().classes('w-96'):
        ui.label('Nieuwe Groep').classes('text-xl font-bold mb-4')

        # Name input
        ui.input('Groepsnaam', placeholder='Bijv. UvA').bind_value(
            dialog_state, 'name'
        ).classes('w-full mb-3')

        # Redirect URL input
        ui.input('Redirect URL', placeholder='https://example.com/').bind_value(
            dialog_state, 'redirect_url'
        ).classes('w-full mb-3')

        # Redirect Text input
        ui.input('Redirect Text', placeholder='Bijv. Canvas (UvA)').bind_value(
            dialog_state, 'redirect_text'
        ).classes('w-full mb-4')

        # Buttons
        with ui.row().classes('w-full justify-end gap-2'):
            ui.button('Annuleren', on_click=handle_cancel).classes('bg-gray-500 text-white')
            ui.button('Toevoegen', on_click=handle_add).classes('bg-blue-500 text-white')

    add_dialog.open()


def edit_group_dialog(group, page_state):
    logger.info(f"Opening edit group dialog for group: {group['id']}")

    # Dialog state - pre-fill with current values
    dialog_state = {
        'name': group['name'],
        'redirect_url': group['redirect_url'],
        'redirect_text': group['redirect_text']
    }

    def handle_save():
        logger.info(f"Processing group update for: {group['id']}")

        if not dialog_state['name'].strip():
            ui.notify('Groepsnaam is verplicht', type='negative')
            return

        if not dialog_state['redirect_url'].strip():
            ui.notify('Redirect URL is verplicht', type='negative')
            return

        if not dialog_state['redirect_text'].strip():
            ui.notify('Redirect Text is verplicht', type='negative')
            return

        try:
            # Update the group
            success = update_group(
                group['id'],
                name=dialog_state['name'].strip(),
                redirect_url=dialog_state['redirect_url'].strip(),
                redirect_text=dialog_state['redirect_text'].strip()
            )

            if success:
                logger.info(f"Group updated successfully: {group['id']}")
                edit_dialog.close()
                ui.notify(f'Groep "{dialog_state["name"]}" is bijgewerkt', type='positive')

                # Refresh the table
                if 'refresh_function' in page_state:
                    page_state['refresh_function']()
            else:
                raise Exception("Group not found")

        except Exception as e:
            logger.error(f"Failed to update group: {e}")
            ui.notify(f'Fout bij het bijwerken van groep: {str(e)}', type='negative')

    def handle_cancel():
        logger.info("Edit group dialog cancelled")
        edit_dialog.close()

    # edit dialog
    with ui.dialog() as edit_dialog, ui.card().classes('w-96'):
        ui.label('Groep Bewerken').classes('text-xl font-bold mb-4')

        # Name input
        ui.input('Groepsnaam', placeholder='Bijv. UvA').bind_value(
            dialog_state, 'name'
        ).classes('w-full mb-3')

        # Redirect URL input
        ui.input('Redirect URL', placeholder='https://example.com/').bind_value(
            dialog_state, 'redirect_url'
        ).classes('w-full mb-3')

        # Redirect Text input
        ui.input('Redirect Text', placeholder='Bijv. Canvas (UvA)').bind_value(
            dialog_state, 'redirect_text'
        ).classes('w-full mb-4')

        # Buttons
        with ui.row().classes('w-full justify-end gap-2'):
            ui.button('Annuleren', on_click=handle_cancel).classes('bg-gray-500 text-white')
            ui.button('Opslaan', on_click=handle_save).classes('bg-blue-500 text-white')

    edit_dialog.open()


def delete_group_dialog(group, page_state):
    logger.info(f"Opening delete group dialog for group: {group['id']}")

    def handle_delete():
        logger.info(f"Processing group deletion for: {group['id']}")

        try:
            success = delete_group(group['id'])
            if success:
                logger.info(f"Group deleted successfully: {group['id']}")
                delete_dialog.close()
                ui.notify(f'Groep "{group["name"]}" is verwijderd', type='positive')

                # Refresh the table
                if 'refresh_function' in page_state:
                    page_state['refresh_function']()
            else:
                raise Exception("Group not found")

        except Exception as e:
            logger.error(f"Failed to delete group: {e}")
            ui.notify(f'Fout bij het verwijderen van groep: {str(e)}', type='negative')

    def handle_cancel():
        logger.info("Delete group dialog cancelled")
        delete_dialog.close()

    # deletion dialog
    with ui.dialog() as delete_dialog, ui.card().classes('w-96'):
        ui.label('Groep Verwijderen').classes('text-xl font-bold mb-4')

        ui.label(f'Weet je zeker dat je de groep "{group["name"]}" wilt verwijderen?').classes('mb-4')
        ui.label('Deze actie kan niet ongedaan worden gemaakt.').classes('text-red-500 mb-4')

        with ui.row().classes('w-full justify-end gap-2'):
            ui.button('Annuleren', on_click=handle_cancel).classes('bg-gray-500 text-white')
            ui.button('Verwijderen', on_click=handle_delete).classes('bg-red-500 text-white')

    delete_dialog.open()
