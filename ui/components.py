"""
Reusable UI components for eduIDM application.
"""

from nicegui import ui


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
