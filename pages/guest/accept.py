"""
Guest Accept Page
Handle invitation acceptance - check eduID, iDIN, MFA, confirm/edit email
"""

from nicegui import ui
from data_manager import DataManager
from typing import Optional


def render_page(data_manager: DataManager, invite_code: str):
    """Render the invitation acceptance page"""

    # Find the invitation by invite code (simplified - in real app would have proper invite code tracking)
    guest_groups = data_manager.get_guest_groups()
    invitation = None

    # For demo purposes, we'll match by the last part of the invite code to a guest group ID
    # In a real implementation, you'd store invite codes properly
    for gg in guest_groups:
        if gg.id.endswith(invite_code[-8:]) or invite_code in gg.id:
            invitation = gg
            break

    if not invitation:
        render_invalid_invitation()
        return

    # Check if already accepted
    if invitation.datetime_accepted:
        render_already_accepted(data_manager, invitation)
        return

    # Get group information
    group = data_manager.get_group(invitation.group_id)
    if not group:
        render_invalid_invitation()
        return

    render_invitation_form(data_manager, invitation, group, invite_code)


def render_invalid_invitation():
    """Render invalid invitation page"""

    ui.label('Invalid Invitation').classes('text-3xl font-bold mb-6 text-red-500')
    ui.label('The invitation code you provided is invalid or has expired.').classes('text-lg mb-4')
    ui.label('Please contact the administrator for assistance.').classes('text-gray-600 mb-4')

    ui.button('← Back to Home', on_click=lambda: ui.navigate.to('/')).classes('bg-gray-500 text-white')


def render_already_accepted(data_manager: DataManager, invitation):
    """Render already accepted invitation page"""

    group = data_manager.get_group(invitation.group_id)
    group_name = group.name if group else "Unknown Group"

    ui.label('Invitation Already Accepted').classes('text-3xl font-bold mb-6 text-green-500')
    ui.label(f'You have already accepted the invitation to join "{group_name}".').classes('text-lg mb-4')
    ui.label(f'Accepted on: {invitation.datetime_accepted.split("T")[0]}').classes('text-gray-600 mb-4')

    # Find user ID for profile link (simplified lookup)
    guest_id = invitation.mail_address_invited.split('@')[0]
    ui.button('View My Profile', on_click=lambda: ui.navigate.to(
        f'/my/{guest_id}')).classes('bg-blue-500 text-white mr-2')
    ui.button('← Back to Home', on_click=lambda: ui.navigate.to('/')).classes('bg-gray-500 text-white')


def render_invitation_form(data_manager: DataManager, invitation, group, invite_code: str):
    """Render the invitation acceptance form"""

    ui.label(f'Accept Invitation to {group.name}').classes('text-3xl font-bold mb-6')

    # Invitation details
    with ui.card().classes('w-full max-w-2xl mb-6'):
        ui.label('Invitation Details').classes('text-xl font-bold mb-4')
        ui.label(f'Group: {group.name}').classes('mb-2')
        ui.label(f'Invited Email: {invitation.mail_address_invited}').classes('mb-2')
        ui.label(f'Invited Date: {invitation.datetime_invited.split("T")[0]}').classes('mb-2')
        ui.label(f'Valid for: {group.validity_days} days').classes('mb-2')

    # Verification requirements
    with ui.card().classes('w-full max-w-2xl mb-6'):
        ui.label('Verification Requirements').classes('text-xl font-bold mb-4')

        # eduID verification (always required)
        with ui.row().classes('mb-3 items-center'):
            ui.icon('school', color='blue').classes('mr-2')
            ui.label('eduID Verification').classes('font-semibold mr-4')
            ui.button('Verify with eduID', on_click=lambda: verify_eduid()).classes('bg-blue-500 text-white')

        # iDIN verification (if required)
        if group.idin_required:
            with ui.row().classes('mb-3 items-center'):
                ui.icon('verified_user', color='orange').classes('mr-2')
                ui.label('iDIN Verification').classes('font-semibold mr-4')
                ui.button('Verify with iDIN', on_click=lambda: verify_idin()).classes('bg-orange-500 text-white')

        # MFA verification (if required)
        if group.mfa_required:
            with ui.row().classes('mb-3 items-center'):
                ui.icon('security', color='green').classes('mr-2')
                ui.label('Multi-Factor Authentication').classes('font-semibold mr-4')
                ui.button('Setup MFA', on_click=lambda: verify_mfa()).classes('bg-green-500 text-white')

    # Email confirmation/editing
    with ui.card().classes('w-full max-w-2xl mb-6'):
        ui.label('Email Confirmation').classes('text-xl font-bold mb-4')

        if group.can_edit_mail_address:
            ui.label('You can confirm or edit your email address:').classes('mb-2')
            email_input = ui.input('Email Address', value=invitation.mail_address_invited).classes('w-full mb-2')
        else:
            ui.label('Your email address (cannot be changed):').classes('mb-2')
            ui.label(invitation.mail_address_invited).classes('font-mono bg-gray-100 p-2 rounded mb-2')
            email_input = None

    # Verification status tracking
    verification_status = {
        'eduid': False,
        'idin': not group.idin_required,  # Not required = automatically true
        'mfa': not group.mfa_required     # Not required = automatically true
    }

    # Status display
    status_container = ui.column().classes('w-full max-w-2xl mb-6')
    update_status_display(status_container, verification_status, group)

    # Accept button (initially disabled)
    accept_button = ui.button('Accept Invitation',
                              on_click=lambda: accept_invitation(data_manager, invitation, invite_code,
                                                                 email_input.value if email_input else invitation.mail_address_invited)
                              ).classes('bg-green-600 text-white text-lg px-8 py-3 mr-4')
    accept_button.disable()

    ui.button('Decline', on_click=lambda: ui.navigate.to('/')).classes('bg-red-500 text-white text-lg px-8 py-3')

    def verify_eduid():
        """Simulate eduID verification"""
        ui.notify('eduID verification successful!', type='positive')
        verification_status['eduid'] = True
        update_status_display(status_container, verification_status, group)
        check_all_verified(accept_button, verification_status)

    def verify_idin():
        """Simulate iDIN verification"""
        ui.notify('iDIN verification successful!', type='positive')
        verification_status['idin'] = True
        update_status_display(status_container, verification_status, group)
        check_all_verified(accept_button, verification_status)

    def verify_mfa():
        """Simulate MFA setup"""
        ui.notify('MFA setup completed!', type='positive')
        verification_status['mfa'] = True
        update_status_display(status_container, verification_status, group)
        check_all_verified(accept_button, verification_status)


def update_status_display(container, verification_status, group):
    """Update the verification status display"""

    container.clear()
    with container:
        with ui.card().classes('w-full'):
            ui.label('Verification Status').classes('text-xl font-bold mb-4')

            # eduID status
            status_icon = '✅' if verification_status['eduid'] else '⏳'
            status_text = 'Verified' if verification_status['eduid'] else 'Pending'
            ui.label(f'{status_icon} eduID: {status_text}').classes('mb-2')

            # iDIN status (if required)
            if group.idin_required:
                status_icon = '✅' if verification_status['idin'] else '⏳'
                status_text = 'Verified' if verification_status['idin'] else 'Pending'
                ui.label(f'{status_icon} iDIN: {status_text}').classes('mb-2')

            # MFA status (if required)
            if group.mfa_required:
                status_icon = '✅' if verification_status['mfa'] else '⏳'
                status_text = 'Completed' if verification_status['mfa'] else 'Pending'
                ui.label(f'{status_icon} MFA: {status_text}').classes('mb-2')


def check_all_verified(accept_button, verification_status):
    """Check if all verifications are complete and enable accept button"""

    all_verified = all(verification_status.values())
    if all_verified:
        accept_button.enable()
        ui.notify('All verifications complete! You can now accept the invitation.', type='positive')


def accept_invitation(data_manager: DataManager, invitation, invite_code: str, email: str):
    """Accept the invitation"""

    # Update the invitation with acceptance timestamp
    invitation.datetime_accepted = data_manager.get_current_timestamp()
    invitation.mail_address_invited = email  # Update email if changed

    if data_manager.update_guest_group(invitation):
        ui.notify('Invitation accepted successfully!', type='positive')

        # Create or update guest record
        guest_id = email.split('@')[0]  # Simple guest ID generation
        existing_guest = data_manager.get_guest(guest_id)

        if not existing_guest:
            from data_manager import Guest
            new_guest = Guest(
                guest_id=guest_id,
                mail_address_preferred=email,
                verification_status={
                    'verify_idin': True,
                    'verify_institution': True,
                    'verify_mfa': True
                }
            )
            data_manager.add_guest(new_guest)

        # Redirect to profile page
        ui.navigate.to(f'/my/{guest_id}')
    else:
        ui.notify('Failed to accept invitation. Please try again.', type='negative')
