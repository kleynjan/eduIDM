import json
from typing import Dict, Any, Optional

def load_storage() -> Dict[str, Any]:
    """Load storage.json as a dictionary"""
    try:
        with open('storage.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return {"groups": [], "guests": [], "invitations": []}

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

# Legacy function for backward compatibility - can be removed later
def find_guest_group_by_hash(storage_data: Dict[str, Any], hash_id: str) -> Optional[Dict[str, Any]]:
    """Legacy function - use find_invitation_by_hash instead"""
    return find_invitation_by_hash(storage_data, hash_id)
