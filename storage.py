import json
import uuid
from datetime import datetime
from typing import Dict, Any, Optional, List

def load_storage() -> Dict[str, Any]:
    """Load storage.json as a dictionary"""
    try:
        with open('storage.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return {"groups": [], "invitations": []}

def save_storage(data: Dict[str, Any]) -> None:
    """Save dictionary back to storage.json"""
    with open('storage.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

def find_invitation_by_hash(storage_data: Dict[str, Any], hash_id: str) -> Optional[Dict[str, Any]]:
    """Find invitation entry by hash (invitation_id)"""
    for invitation in storage_data.get('invitations', []):
        if invitation.get('invitation_id') == hash_id:
            return invitation
    return None

def find_group_by_id(storage_data: Dict[str, Any], group_id: str) -> Optional[Dict[str, Any]]:
    """Find group by group_id"""
    for group in storage_data.get('groups', []):
        if group.get('id') == group_id:
            return group
    return None

def find_group_by_name(storage_data: Dict[str, Any], group_name: str) -> Optional[Dict[str, Any]]:
    """Find group by group name"""
    for group in storage_data.get('groups', []):
        if group.get('name') == group_name:
            return group
    return None

def create_invitation(guest_id: str, group_id: str, invitation_mail_address: str) -> str:
    """Create a new invitation and return the invitation_id"""
    storage_data = load_storage()

    # Generate new invitation ID
    invitation_id = str(uuid.uuid4()).replace('-', '')

    # Create invitation record with empty eppn and eduid_props (will be filled when accepted)
    invitation = {
        "invitation_id": invitation_id,
        "guest_id": guest_id,
        "group_id": group_id,
        "invitation_mail_address": invitation_mail_address,
        "datetime_invited": datetime.utcnow().isoformat() + 'Z',
        "eppn": "",
        "eduid_props": {}
    }

    # Add to storage
    storage_data.setdefault('invitations', []).append(invitation)

    save_storage(storage_data)
    return invitation_id

def get_all_invitations_with_details() -> List[Dict[str, Any]]:
    """Get all invitations with resolved group names and status"""
    storage_data = load_storage()
    invitations_with_details = []

    def format_datetime(iso_string):
        """Format ISO datetime string to human-readable format"""
        if not iso_string:
            return ''
        try:
            # Parse ISO format and convert to readable format
            dt = datetime.fromisoformat(iso_string.replace('Z', '+00:00'))
            return dt.strftime('%d-%m-%Y %H:%M')
        except:
            return iso_string

    for invitation in storage_data.get('invitations', []):
        # Get group details
        group = find_group_by_id(storage_data, invitation.get('group_id'))
        group_name = group.get('name', 'Unknown Group') if group else 'Unknown Group'

        # Format dates
        datetime_invited_formatted = format_datetime(invitation.get('datetime_invited'))
        datetime_accepted_formatted = format_datetime(invitation.get('datetime_accepted'))

        invitation_detail = {
            'invitation_id': invitation.get('invitation_id'),
            'guest_id': invitation.get('guest_id'),
            'group_name': group_name,
            'group_id': invitation.get('group_id'),
            'invitation_mail_address': invitation.get('invitation_mail_address', ''),
            'datetime_invited_formatted': datetime_invited_formatted,
            'datetime_accepted_formatted': datetime_accepted_formatted,
            'datetime_invited': invitation.get('datetime_invited'),
            'datetime_accepted': invitation.get('datetime_accepted')
        }
        invitations_with_details.append(invitation_detail)

    return invitations_with_details

def get_all_groups() -> List[Dict[str, Any]]:
    """Get all groups for dropdown selection"""
    storage_data = load_storage()
    return storage_data.get('groups', [])

# Legacy function for backward compatibility - can be removed later
def find_guest_group_by_hash(storage_data: Dict[str, Any], hash_id: str) -> Optional[Dict[str, Any]]:
    """Legacy function - use find_invitation_by_hash instead"""
    return find_invitation_by_hash(storage_data, hash_id)
