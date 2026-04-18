"""
Placeholder authentication module for the MVP phase.

These functions return hardcoded identifiers so that all service and API
code can depend on a stable auth contract from day one.  When the project
moves to the SaaS phase, each function will be replaced with real
authentication logic (JWT verification, session lookup, etc.).
"""

import uuid

_MVP_USER_ID = uuid.UUID("00000000-0000-0000-0000-000000000001")
_MVP_WORKSPACE_ID = uuid.UUID("00000000-0000-0000-0000-000000000001")


async def get_current_user_id() -> uuid.UUID:
    """Return the current authenticated user's ID.

    MVP: returns a hardcoded value.  Will be replaced with JWT /
    session-based extraction in the SaaS phase.
    """
    return _MVP_USER_ID


async def get_current_workspace_id() -> uuid.UUID:
    """Return the current workspace ID for the authenticated user.

    MVP: returns a hardcoded value.  Will be replaced with workspace
    membership resolution in the SaaS phase.
    """
    return _MVP_WORKSPACE_ID
