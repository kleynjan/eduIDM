import json
import uuid
import os
from datetime import datetime
from typing import Dict, Any, Optional, List

# Get the directory where this module is located
_MODULE_DIR = os.path.dirname(os.path.abspath(__file__))
_STORAGE_FILE = os.path.join(_MODULE_DIR, 'storage.json')

def load_storage() -> Dict[str, Any]:
    """Load storage.json as a dictionary"""
    try:
        with open(_STORAGE_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return {"groups": [], "invitations": []}

def save_storage(data: Dict[str, Any]) -> None:
    """Save dictionary back to storage.json"""
    with open(_STORAGE_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

def find_invitation_by_code(invite_code: str) -> Optional[Dict[str, Any]]:
    """Find invitation entry by invite_code (invitation_id)"""
    storage_data = load_storage()
    for invitation in storage_data.get('invitations', []):
        if invitation['invitation_id'] == invite_code:
            return invitation
    return None

def find_group_by_id(group_id: str) -> Optional[Dict[str, Any]]:
    """Find group by group_id"""
    storage_data = load_storage()
    for group in storage_data.get('groups', []):
        if group['id'] == group_id:
            return group
    return None

def find_group_by_name(group_name: str) -> Optional[Dict[str, Any]]:
    """Find group by group name"""
    storage_data = load_storage()
    for group in storage_data.get('groups', []):
        if group['name'] == group_name:
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
        except:  # noqa: E722
            return iso_string

    for invitation in storage_data.get('invitations', []):
        # Get group details
        group = find_group_by_id(invitation['group_id'])
        group_name = group.get('name', '')  # type: ignore

        # Format dates
        datetime_invited_formatted = format_datetime(invitation['datetime_invited'])
        datetime_accepted_formatted = format_datetime(invitation['datetime_accepted'])

        invitation_detail = {
            'invitation_id': invitation['invitation_id'],
            'guest_id': invitation['guest_id'],
            'group_name': group_name,
            'group_id': invitation['group_id'],
            'invitation_mail_address': invitation.get('invitation_mail_address', ''),
            'datetime_invited_formatted': datetime_invited_formatted,
            'datetime_accepted_formatted': datetime_accepted_formatted,
            'datetime_invited': invitation['datetime_invited'],
            'datetime_accepted': invitation['datetime_accepted']
        }
        invitations_with_details.append(invitation_detail)

    return invitations_with_details

def get_all_groups() -> List[Dict[str, Any]]:
    """Get all groups for dropdown selection"""
    storage_data = load_storage()
    return storage_data.get('groups', [])

def create_group(name: str, redirect_url: str, redirect_text: str) -> str:
    """Create a new group and return the group_id"""
    storage_data = load_storage()

    # Generate new group ID
    group_id = str(uuid.uuid4())

    # Create group record
    group = {
        "id": group_id,
        "name": name,
        "redirect_url": redirect_url,
        "redirect_text": redirect_text
    }

    # Add to storage
    storage_data.setdefault('groups', []).append(group)

    save_storage(storage_data)
    return group_id

def update_group(group_id: str, **updates) -> bool:
    """Update a group with the provided fields

    Args:
        group_id: The group ID to update
        **updates: Keyword arguments for fields to update

    Returns:
        True if group was found and updated, False otherwise
    """
    storage_data = load_storage()

    for group in storage_data.get('groups', []):
        if group['id'] == group_id:
            group.update(updates)
            save_storage(storage_data)
            return True

    return False

def delete_group(group_id: str) -> bool:
    """Delete a group by ID

    Args:
        group_id: The group ID to delete

    Returns:
        True if group was found and deleted, False otherwise
    """
    storage_data = load_storage()

    groups = storage_data.get('groups', [])
    original_length = len(groups)

    # Remove the group
    storage_data['groups'] = [g for g in groups if g['id'] != group_id]

    if len(storage_data['groups']) < original_length:
        save_storage(storage_data)
        return True

    return False

def update_invitation(invite_code: str, **updates) -> bool:
    """Update an invitation with the provided fields

    Args:
        invite_code: The invitation code to update
        **updates: Keyword arguments for fields to update

    Returns:
        True if invitation was found and updated, False otherwise
    """
    storage_data = load_storage()

    for invitation in storage_data.get('invitations', []):
        if invitation['invitation_id'] == invite_code:
            invitation.update(updates)
            save_storage(storage_data)
            return True

    return False

# Legacy function for backward compatibility - can be removed later
def find_guest_group_by_hash(hash_id: str) -> Optional[Dict[str, Any]]:
    """Legacy function - use find_invitation_by_code instead"""
    return find_invitation_by_code(hash_id)

# Backward compatibility alias
def find_invitation_by_hash(hash_id: str) -> Optional[Dict[str, Any]]:
    """Backward compatibility alias - use find_invitation_by_code instead"""
    return find_invitation_by_code(hash_id)

# Backward compatibility alias
def find_invitation_by_invite_code(invite_code: str) -> Optional[Dict[str, Any]]:
    """Backward compatibility alias - use find_invitation_by_code instead"""
    return find_invitation_by_code(invite_code)
