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
    body = f"""Geachte collega,
    
U bent uitgenodigd als "{group_name}".

Klik op onderstaande link om de uitnodiging te accepteren:
<a href="http://uva.eduidm.nl/accept?code={invite_code}">http://uva.eduidm.nl/accept?code={invite_code}</a>

Of ga naar http://uva.eduidm.nl/accept en kopieer en plak daar deze code:
    {invite_code}

Met vriendelijke groet,
ICT Ondersteuning
Universitaire PABO Universiteit van Amsterdam"""

    mail_content = {
        'to': invitation.get('invitation_mail_address', 'N/A'),
        'from': 'icto_upva_someone@uva.nl',
        'subject': f'Uitnodiging als {group_name} voor de Universiteit van Amsterdam',
        'body': body
    }

    logger.info(f"Mail content created for invitation: {invite_code}")
    return mail_content
