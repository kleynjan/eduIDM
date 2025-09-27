# services/mail_service.py
# not really sending mail yet...

from services.storage import find_invitation_by_code, find_group_by_id
from services.logging import logger


def create_mail(invite_code: str):
    """Create mail content for invitation (returns mail object, no UI)"""
    logger.info(f"Mail service called for invitation: {invite_code}")

    invitation = find_invitation_by_code(invite_code)

    if not invitation:
        logger.error(f"No invitation found for code: {invite_code}")
        return None

    # Get group details
    group = find_group_by_id(invitation['group_id'])
    group_name = group.get('name', 'Onbekende groep') if group else 'Onbekende groep'

    logger.info(
        f"Creating mail content for guest_id: {invitation.get('guest_id')} to {invitation.get('invitation_mail_address')}")

    # Create mail content
    body = f"""Geachte,

U bent uitgenodigd om deel te nemen aan de groep "{group_name}" via eduIDM.

Guest ID: {invitation.get('guest_id', 'N/A')}
Uitnodigingscode: {invite_code}

Klik op onderstaande link om de uitnodiging te accepteren:
http://localhost:8080/accept?code={invite_code}

Met vriendelijke groet,
Het eduIDM Team"""

    mail_content = {
        'to': invitation.get('invitation_mail_address', 'N/A'),
        'from': 'noreply@eduidm.nl',
        'subject': 'Uitnodiging voor eduIDM',
        'body': body
    }

    logger.info(f"Mail content created for invitation: {invite_code}")
    return mail_content
