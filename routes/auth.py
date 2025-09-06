# http/s endpoints for eduID OIDC: callback and error pages
# when eduID login is completed, calls complete_eduid_login with updated session_state

from nicegui import ui
from session_manager import session_manager
from eduid_auth import complete_eduid_login, process_eduid_completion, get_oidc_error, clear_oidc_error
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

        try:
            # Complete eduID login
            logger.debug("Completing eduID login flow")
            complete_eduid_login(code, session_state)

            # Process completion and update application state
            logger.debug("Processing eduID completion")
            process_eduid_completion(session_state, session_manager.state)

            logger.info("eduID authentication completed successfully")

            # Success - redirect back to accept page
            ui.label('Authentication Successful!').classes('text-xl font-bold text-green-600 mb-4')
            ui.label('Redirecting...').classes('text-lg mb-4')

            # Auto-redirect after a short delay
            current_hash = session_manager.state['hash']
            redirect_url = f'/accept/{current_hash}' if current_hash else '/accept'
            logger.info(f"Redirecting to: {redirect_url}")
            ui.timer(2.0, lambda: ui.navigate.to(redirect_url), once=True)

        except Exception as e:
            error_msg = str(e)
            logger.error(f"eduID authentication failed: {error_msg}")
            session_state['oidc']['error'] = error_msg

            ui.label('Authentication Failed').classes('text-xl font-bold text-red-600 mb-4')
            ui.label(f'Error: {error_msg}').classes('text-lg mb-4')
            ui.button('Return to Accept Page', on_click=lambda: ui.navigate.to(
                '/accept')).classes('bg-blue-500 text-white')


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
