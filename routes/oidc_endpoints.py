"""
OIDC-related routes for eduIDM application.
Handles OIDC callback and error pages.
"""

from nicegui import ui
from session_manager import session_manager
from error_handler import get_oidc_error, clear_oidc_error
from services.oidc_service import complete_oidc_flow
import oidc
from utils.logging import logger


@ui.page('/oidc_callback')
def oidc_callback(code: str = None, error: str = None):
    """Handle OIDC callback from authorization server"""
    logger.info(f"OIDC callback received - code: {'present' if code else 'missing'}, error: {error}")

    ui.page_title('Processing Authentication...')

    with ui.column().classes('max-w-2xl mx-auto p-6 text-center'):
        if error:
            logger.error(f"OIDC authorization error received: {error}")
            # Handle authorization error
            ui.label('Authentication Error').classes('text-2xl font-bold text-red-600 mb-4')
            ui.label(f'Error: {error}').classes('text-lg mb-4')
            ui.button('Return to Accept Page', on_click=lambda: ui.navigate.to(
                '/accept')).classes('bg-blue-500 text-white')
            return

        if not code:
            logger.error("OIDC callback received without authorization code")
            ui.label('Authentication Error').classes('text-2xl font-bold text-red-600 mb-4')
            ui.label('No authorization code received').classes('text-lg mb-4')
            ui.button('Return to Accept Page', on_click=lambda: ui.navigate.to(
                '/accept')).classes('bg-blue-500 text-white')
            return

        logger.info("Processing OIDC authorization code")
        # Show loading message
        ui.label('Processing Authentication...').classes('text-xl mb-4')
        ui.spinner(size='lg')

        # Get session state
        session_state = session_manager.session_state

        # Exchange code for access token
        logger.debug("Exchanging authorization code for access token")
        token_data = oidc.get_access_token(code, session_state)
        if not token_data:
            error_msg = get_oidc_error(session_state) or 'Failed to get access token'
            logger.error(f"Token exchange failed: {error_msg}")
            ui.label('Token Exchange Failed').classes('text-xl font-bold text-red-600 mb-4')
            ui.label(f'Error: {error_msg}').classes('text-lg mb-4')
            ui.button('Return to Accept Page', on_click=lambda: ui.navigate.to(
                '/accept')).classes('bg-blue-500 text-white')
            return

        logger.info("Token exchange successful, completing OIDC flow")
        # Complete the OIDC flow
        complete_oidc_flow()

        # Success - redirect back to accept page
        ui.label('Authentication Successful!').classes('text-xl font-bold text-green-600 mb-4')
        ui.label('Redirecting...').classes('text-lg mb-4')

        # Auto-redirect after a short delay
        current_hash = session_manager.state.get('hash', '')
        redirect_url = f'/accept/{current_hash}' if current_hash else '/accept'
        logger.info(f"Redirecting to: {redirect_url}")
        ui.timer(2.0, lambda: ui.navigate.to(redirect_url), once=True)


@ui.page('/oidc_error')
def oidc_error_page():
    """Display OIDC error page"""
    # Get session state
    session_state = session_manager.session_state
    error = get_oidc_error(session_state)
    logger.error(f"OIDC error page accessed with error: {error}")

    ui.page_title('OIDC Authentication Error')

    with ui.column().classes('max-w-2xl mx-auto p-6'):
        ui.label('Authentication Error').classes('text-2xl font-bold text-red-600 mb-4')

        if error:
            ui.label(f'Error: {error}').classes('text-lg mb-4')
        else:
            ui.label('An unknown error occurred during authentication.').classes('text-lg mb-4')

        ui.label('Please try again or contact support if the problem persists.').classes('mb-4')

        with ui.row().classes('gap-4'):
            ui.button('Try Again', on_click=lambda: (logger.info("User clicked 'Try Again' on error page"),
                      ui.navigate.to('/accept'))).classes('bg-blue-500 text-white')
            ui.button('Clear Error', on_click=lambda: (logger.info("User clicked 'Clear Error'"), clear_oidc_error(session_state),
                      ui.navigate.to('/accept'))).classes('bg-gray-500 text-white')
