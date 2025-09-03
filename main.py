#!/usr/bin/env python3
"""
EduInvite - Invitation Management System
Main NiceGUI application with routing and authentication
"""

import json
import uuid
from datetime import datetime, timezone
from typing import Dict, List, Optional

from nicegui import app, ui
import nicegui
from data_manager import DataManager
from pages.admin import users, roles, groups, guests
from pages.guest import accept, profile


class EduInviteApp:
    def __init__(self):
        self.data_manager = DataManager()
        self.setup_routes()

    def setup_routes(self):
        """Setup all application routes"""

        # Home page
        @ui.page('/')
        def home():
            ui.label('EduInvite - Invitation Management System').classes('text-2xl font-bold mb-4')
            ui.label('Welcome to the invitation management system').classes('text-lg mb-4')

            with ui.row().classes('gap-4'):
                ui.button('Admin Panel', on_click=lambda: ui.navigate.to(
                    '/admin/users')).classes('bg-blue-500 text-white')
                ui.button('Guest Services', on_click=lambda: ui.navigate.to(
                    '/guests')).classes('bg-green-500 text-white')

        # Admin routes
        @ui.page('/admin/users')
        def admin_users():
            users.render_page(self.data_manager)

        @ui.page('/admin/roles')
        def admin_roles():
            roles.render_page(self.data_manager)

        @ui.page('/groups')
        @ui.page('/groups/{group_id}')
        def admin_groups(group_id: Optional[str] = None):
            groups.render_page(self.data_manager, group_id)

        @ui.page('/guests')
        @ui.page('/guests/{group_id}')
        def admin_guests(group_id: Optional[str] = None):
            guests.render_page(self.data_manager, group_id)

        @ui.page('/guests/invite/{group_id}')
        def invite_guest(group_id: str):
            guests.render_invite_page(self.data_manager, group_id)

        # Guest/End user routes
        @ui.page('/accept/{invite_code}')
        def accept_invitation(invite_code: str):
            accept.render_page(self.data_manager, invite_code)

        @ui.page('/my/{user_id}')
        def user_profile(user_id: str):
            profile.render_page(self.data_manager, user_id)


def main():
    """Main application entry point"""
    app.title = 'EduInvite - Invitation Management'

    # Initialize the application
    edu_invite = EduInviteApp()

    # Run the application
    ui.run(host='127.0.0.1', port=8080, reload=True, show=False)


if __name__ in {"__main__", "__mp_main__"}:
    main()
