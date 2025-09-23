import json
import os
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

# Get the directory where this module is located
_MODULE_DIR = os.path.dirname(os.path.abspath(__file__))
_STORAGE_FILE = os.path.join(_MODULE_DIR, 'storage.json')

# storage.json handlers

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


# invitation CRUD

def find_invitation_by_code(invite_code: str) -> Optional[Dict[str, Any]]:
    storage_data = load_storage()

    for invitation in storage_data.get('invitations', []):
        if invitation['invitation_id'] == invite_code:
            return invitation

    return None


def update_invitation(invite_code: str, **updates) -> bool:
    storage_data = load_storage()

    for invitation in storage_data.get('invitations', []):
        if invitation['invitation_id'] == invite_code:
            invitation.update(updates)
            save_storage(storage_data)
            return True

    return False


def create_invitation(guest_id: str, group_id: str, invitation_mail_address: str) -> str:
    """Create a new invitation and return the invitation_id"""
    storage_data = load_storage()

    # Generate new invitation ID
    invitation_id = str(uuid.uuid4()).replace('-', '')

    # Create invitation record with empty eppn, eduid_props, and datetime_accepted (will be filled when accepted)
    invitation = {
        "invitation_id": invitation_id,
        "guest_id": guest_id,
        "group_id": group_id,
        "invitation_mail_address": invitation_mail_address,
        "datetime_invited": datetime.utcnow().isoformat() + 'Z',
        "datetime_accepted": "",
        "eppn": "",
        "eduid_props": {}
    }
    storage_data.setdefault('invitations', []).append(invitation)
    save_storage(storage_data)
    return invitation_id


def mark_invitation_accepted(invite_code: str):
    invitation = find_invitation_by_code(invite_code)
    if invitation and not invitation.get('datetime_accepted', ''):
        update_invitation(
            invite_code,
            datetime_accepted=datetime.utcnow().isoformat() + 'Z',
        )


def get_all_invitations_with_details() -> List[Dict[str, Any]]:
    storage_data = load_storage()
    invitations_with_details = []

    def format_datetime(iso_string):
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
        datetime_accepted_formatted = format_datetime(invitation.get('datetime_accepted', ''))

        invitation_detail = {
            'invitation_id': invitation['invitation_id'],
            'guest_id': invitation['guest_id'],
            'group_name': group_name,
            'group_id': invitation['group_id'],
            'invitation_mail_address': invitation.get('invitation_mail_address', ''),
            'datetime_invited_formatted': datetime_invited_formatted,
            'datetime_accepted_formatted': datetime_accepted_formatted,
            'datetime_invited': invitation['datetime_invited'],
            'datetime_accepted': invitation.get('datetime_accepted', '')
        }
        invitations_with_details.append(invitation_detail)

    return invitations_with_details


# group CRUD

def get_all_groups() -> List[Dict[str, Any]]:
    storage_data = load_storage()
    return storage_data.get('groups', [])


def find_group_by_id(group_id: str) -> Optional[Dict[str, Any]]:
    storage_data = load_storage()
    for group in storage_data.get('groups', []):
        if group['id'] == group_id:
            return group

    return None


def find_group_by_name(group_name: str) -> Optional[Dict[str, Any]]:
    storage_data = load_storage()
    for group in storage_data.get('groups', []):
        if group['name'] == group_name:
            return group

    return None


def create_group(name: str, redirect_url: str, redirect_text: str) -> str:
    storage_data = load_storage()

    group_id = str(uuid.uuid4())
    group = {
        "id": group_id,
        "name": name,
        "redirect_url": redirect_url,
        "redirect_text": redirect_text
    }
    storage_data.setdefault('groups', []).append(group)
    save_storage(storage_data)

    return group_id


def update_group(group_id: str, **updates) -> bool:
    storage_data = load_storage()

    for group in storage_data.get('groups', []):
        if group['id'] == group_id:
            group.update(updates)
            save_storage(storage_data)
            return True

    return False


def delete_group(group_id: str) -> bool:
    storage_data = load_storage()

    groups = storage_data.get('groups', [])
    original_length = len(groups)

    storage_data['groups'] = [g for g in groups if g['id'] != group_id]

    if len(storage_data['groups']) < original_length:
        save_storage(storage_data)
        return True

    return False
