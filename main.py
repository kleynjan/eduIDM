import logging
from nicegui import ui, run
from utils.logging import setup_logging, logger

# register routes
import routes.api
import routes.accept
import routes.invitations
import eduid_oidc.oidc_callback

# Configure logging
setup_logging(
    level=logging.DEBUG,
    log_file='eduidm.log',
    enable_console_logging=True
)

if __name__ in {"__main__", "__mp_main__"}:
    logger.info("starting eduIDM on localhost:8080")
    ui.run(host='localhost', port=8080, storage_secret="AbraXabra2452", title='eduIDM', show=False)
