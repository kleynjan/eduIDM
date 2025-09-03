"""
Data Manager for EduInvite
Handles loading, saving, and manipulating data from storage.json
"""

import json
import uuid
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict


@dataclass
class User:
    id: str
    surname: str
    given_name: str
    username: str
    eduid_nameid: str
    mail: str


@dataclass
class AdminRole:
    user_id: str
    group_id: str
    admin_role: str


@dataclass
class Group:
    id: str
    name: str
    mail_template_file_html: str
    mail_template_file_txt: str
    idin_required: bool
    mfa_required: bool
    can_edit_mail_address: bool
    validity_days: int


@dataclass
class Guest:
    guest_id: str
    surname: Optional[str] = None
    given_name: Optional[str] = None
    mail_address_preferred: Optional[str] = None
    eduid_nameid: Optional[str] = None
    eduid_surname: Optional[str] = None
    eduid_given_name: Optional[str] = None
    eduid_mail_address: Optional[str] = None
    verification_status: Optional[Dict[str, bool]] = None


@dataclass
class GuestGroup:
    id: str
    group_id: str
    mail_address_invited: str
    datetime_invited: str
    datetime_accepted: Optional[str] = None


class DataManager:
    def __init__(self, storage_file: str = "storage.json"):
        self.storage_file = storage_file
        self.data = {}
        self.load_data()

    def load_data(self):
        """Load data from storage.json file"""
        try:
            with open(self.storage_file, 'r') as f:
                self.data = json.load(f)
        except FileNotFoundError:
            # Initialize with empty data structure if file doesn't exist
            self.data = {
                "users": [],
                "admin_roles": [],
                "groups": [],
                "guests": [],
                "guest_groups": []
            }
            self.save_data()
        except json.JSONDecodeError as e:
            raise Exception(f"Error parsing {self.storage_file}: {e}")

    def save_data(self):
        """Save current data to storage.json file"""
        try:
            with open(self.storage_file, 'w') as f:
                json.dump(self.data, f, indent=4)
        except Exception as e:
            raise Exception(f"Error saving to {self.storage_file}: {e}")

    # User management methods
    def get_users(self) -> List[User]:
        """Get all users"""
        return [User(**user) for user in self.data.get("users", [])]

    def get_user(self, user_id: str) -> Optional[User]:
        """Get a specific user by ID"""
        for user_data in self.data.get("users", []):
            if user_data["id"] == user_id:
                return User(**user_data)
        return None

    def add_user(self, user: User) -> bool:
        """Add a new user"""
        if not user.id:
            user.id = str(uuid.uuid4())

        # Check if user already exists
        if self.get_user(user.id):
            return False

        self.data["users"].append(asdict(user))
        self.save_data()
        return True

    def update_user(self, user: User) -> bool:
        """Update an existing user"""
        for i, user_data in enumerate(self.data.get("users", [])):
            if user_data["id"] == user.id:
                self.data["users"][i] = asdict(user)
                self.save_data()
                return True
        return False

    def delete_user(self, user_id: str) -> bool:
        """Delete a user"""
        for i, user_data in enumerate(self.data.get("users", [])):
            if user_data["id"] == user_id:
                del self.data["users"][i]
                self.save_data()
                return True
        return False

    # Admin role management methods
    def get_admin_roles(self) -> List[AdminRole]:
        """Get all admin roles"""
        return [AdminRole(**role) for role in self.data.get("admin_roles", [])]

    def add_admin_role(self, admin_role: AdminRole) -> bool:
        """Add a new admin role"""
        self.data["admin_roles"].append(asdict(admin_role))
        self.save_data()
        return True

    def delete_admin_role(self, user_id: str, group_id: str) -> bool:
        """Delete an admin role"""
        for i, role_data in enumerate(self.data.get("admin_roles", [])):
            if role_data["user_id"] == user_id and role_data["group_id"] == group_id:
                del self.data["admin_roles"][i]
                self.save_data()
                return True
        return False

    # Group management methods
    def get_groups(self) -> List[Group]:
        """Get all groups"""
        return [Group(**group) for group in self.data.get("groups", [])]

    def get_group(self, group_id: str) -> Optional[Group]:
        """Get a specific group by ID"""
        for group_data in self.data.get("groups", []):
            if group_data["id"] == group_id:
                return Group(**group_data)
        return None

    def add_group(self, group: Group) -> bool:
        """Add a new group"""
        if not group.id:
            group.id = str(uuid.uuid4())

        # Check if group already exists
        if self.get_group(group.id):
            return False

        self.data["groups"].append(asdict(group))
        self.save_data()
        return True

    def update_group(self, group: Group) -> bool:
        """Update an existing group"""
        for i, group_data in enumerate(self.data.get("groups", [])):
            if group_data["id"] == group.id:
                self.data["groups"][i] = asdict(group)
                self.save_data()
                return True
        return False

    def delete_group(self, group_id: str) -> bool:
        """Delete a group"""
        for i, group_data in enumerate(self.data.get("groups", [])):
            if group_data["id"] == group_id:
                del self.data["groups"][i]
                self.save_data()
                return True
        return False

    # Guest management methods
    def get_guests(self) -> List[Guest]:
        """Get all guests"""
        return [Guest(**guest) for guest in self.data.get("guests", [])]

    def get_guest(self, guest_id: str) -> Optional[Guest]:
        """Get a specific guest by ID"""
        for guest_data in self.data.get("guests", []):
            if guest_data["guest_id"] == guest_id:
                return Guest(**guest_data)
        return None

    def add_guest(self, guest: Guest) -> bool:
        """Add a new guest"""
        if not guest.guest_id:
            guest.guest_id = str(uuid.uuid4())

        # Check if guest already exists
        if self.get_guest(guest.guest_id):
            return False

        self.data["guests"].append(asdict(guest))
        self.save_data()
        return True

    def update_guest(self, guest: Guest) -> bool:
        """Update an existing guest"""
        for i, guest_data in enumerate(self.data.get("guests", [])):
            if guest_data["guest_id"] == guest.guest_id:
                self.data["guests"][i] = asdict(guest)
                self.save_data()
                return True
        return False

    def delete_guest(self, guest_id: str) -> bool:
        """Delete a guest"""
        for i, guest_data in enumerate(self.data.get("guests", [])):
            if guest_data["guest_id"] == guest_id:
                del self.data["guests"][i]
                self.save_data()
                return True
        return False

    # Guest group management methods
    def get_guest_groups(self) -> List[GuestGroup]:
        """Get all guest groups"""
        return [GuestGroup(**gg) for gg in self.data.get("guest_groups", [])]

    def get_guest_groups_by_group(self, group_id: str) -> List[GuestGroup]:
        """Get guest groups for a specific group"""
        return [GuestGroup(**gg) for gg in self.data.get("guest_groups", [])
                if gg["group_id"] == group_id]

    def add_guest_group(self, guest_group: GuestGroup) -> bool:
        """Add a new guest group relationship"""
        if not guest_group.id:
            guest_group.id = str(uuid.uuid4())

        self.data["guest_groups"].append(asdict(guest_group))
        self.save_data()
        return True

    def update_guest_group(self, guest_group: GuestGroup) -> bool:
        """Update an existing guest group relationship"""
        for i, gg_data in enumerate(self.data.get("guest_groups", [])):
            if gg_data["id"] == guest_group.id:
                self.data["guest_groups"][i] = asdict(guest_group)
                self.save_data()
                return True
        return False

    def delete_guest_group(self, guest_group_id: str) -> bool:
        """Delete a guest group relationship"""
        for i, gg_data in enumerate(self.data.get("guest_groups", [])):
            if gg_data["id"] == guest_group_id:
                del self.data["guest_groups"][i]
                self.save_data()
                return True
        return False

    # Utility methods
    def generate_invite_code(self) -> str:
        """Generate a unique invite code"""
        return str(uuid.uuid4())

    def get_current_timestamp(self) -> str:
        """Get current timestamp in ISO format"""
        return datetime.now(timezone.utc).isoformat()
