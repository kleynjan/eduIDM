"""
RESTful API endpoints for eduIDM application.
Provides JSON API access to invitations and groups data.
"""

import json
from nicegui import app
from fastapi import Request, HTTPException
from services.storage import (
    create_invitation, get_all_invitations_with_details, get_all_groups,
    load_storage, find_group_by_name
)
from utils.logging import logger


# GET /api/invitations - return all invitations
@app.get("/api/invitations")
async def get_invitations():
    """GET /api/invitations - return all invitations"""
    try:
        invitations = get_all_invitations_with_details()
        logger.info(f"API GET /api/invitations - returning {len(invitations)} invitations")
        return invitations
    except Exception as e:
        logger.error(f"API GET /api/invitations error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


# POST /api/invitations - create new invitation
@app.post("/api/invitations")
async def create_invitation_api(request: Request):
    """POST /api/invitations - create new invitation"""
    try:
        # Parse JSON request body
        body = await request.body()
        data = json.loads(body.decode('utf-8'))
        logger.info(f"API POST /api/invitations - received data: {data}")

        # Validate required fields
        required_fields = ['guest_id', 'group_name', 'invitation_mail_address']
        missing_fields = [field for field in required_fields if not data.get(field, '').strip()]

        if missing_fields:
            logger.warning(f"API POST /api/invitations - missing fields: {missing_fields}")
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "Missing required fields",
                    "missing_fields": missing_fields
                }
            )

        # Look up group by name to get group_id
        storage_data = load_storage()
        group = find_group_by_name(storage_data, data['group_name'].strip())

        if not group:
            logger.warning(f"API POST /api/invitations - group not found: {data['group_name']}")
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "Group not found",
                    "group_name": data['group_name'].strip()
                }
            )

        # Create invitation using the found group_id
        invitation_id = create_invitation(
            data['guest_id'].strip(),
            group['id'],
            data['invitation_mail_address'].strip()
        )

        logger.info(f"API POST /api/invitations - created invitation: {invitation_id}")

        # Return created invitation
        return {
            "invitation_id": invitation_id,
            "guest_id": data['guest_id'].strip(),
            "group_name": data['group_name'].strip(),
            "group_id": group['id'],
            "invitation_mail_address": data['invitation_mail_address'].strip(),
            "message": "Invitation created successfully"
        }

    except json.JSONDecodeError as e:
        logger.error(f"API POST /api/invitations - JSON decode error: {e}")
        raise HTTPException(status_code=400, detail="Invalid JSON format")

    except HTTPException:
        # Re-raise HTTP exceptions
        raise

    except Exception as e:
        logger.error(f"API POST /api/invitations error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


# GET /api/groups - return all groups
@app.get("/api/groups")
async def get_groups():
    """GET /api/groups - return all groups"""
    try:
        groups = get_all_groups()
        logger.info(f"API GET /api/groups - returning {len(groups)} groups")
        return groups
    except Exception as e:
        logger.error(f"API GET /api/groups error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
