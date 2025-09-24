import logging
import json
import os

from nicegui import ui

import eduid_oidc.oidc_callback
import routes.accept

# register routes
import routes.api
import routes.groups
import routes.invitations
from services.logging import logger, setup_logging

try:
    settings = json.load(open('settings.json'))
except Exception:
    settings = {}
    print("Warning: could not load settings.json; set storage_secret for production use!")

DTAP, STORAGE_SECRET = (
    settings.get('DTAP', 'dev'),
    settings.get('storage_secret', 'your-secret-here')
)

if DTAP == "dev":
    LOG_LEVEL = logging.DEBUG
    CONSOLE_LOGGING = True
else:
    LOG_LEVEL = logging.INFO
    CONSOLE_LOGGING = False

setup_logging(
    level=LOG_LEVEL,
    log_file='eduidm.log',
    enable_console_logging=CONSOLE_LOGGING
)

# call this to run in production (from uvicorn)
def run(fastapi_app) -> None:
    ui.run_with(fastapi_app, storage_secret=STORAGE_SECRET, title='eduIDM', prod_js=True)

if __name__ in {"__main__", "__mp_main__"}:
    if DTAP == "dev":
        HOST = 'localhost'
        PORT = 8085
        logger.info(f"Starting eduIDM on {HOST}:{PORT}")
        ui.run(host=HOST, port=PORT, storage_secret=STORAGE_SECRET, title='eduIDM', show=False)
    else:
        print("For production use: run main_fastapi:fastapi_app from uvicorn")
