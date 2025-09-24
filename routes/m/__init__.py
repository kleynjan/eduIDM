"""
Routes for /m pages
"""

# Import the page functions to register them with NiceGUI
from .groups import groups_page
from .invitations import invitations_page

# Export the page functions
__all__ = ['groups_page', 'invitations_page']
