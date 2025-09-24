import logging
import json
import os

from fastapi import FastAPI
from nicegui import ui

import eduid_oidc.oidc_callback
import routes.accept

# register routes
import routes.api
import routes.groups
import routes.invitations
from services.logging import logger, setup_logging

fastapi_app = FastAPI()

settings = json.load(open('settings.json'))
DTAP, HOST, PORT, STORAGE_SECRET = (
    settings.get('DTAP', 'dev'),
    settings.get('host', 'localhost'),
    settings.get('port', 8085),
    settings.get('storage_secret', 'your-secret-here')
)

# Configure logging
setup_logging(
    level=logging.DEBUG,
    log_file='eduidm.log',
    enable_console_logging=True
)

# call this to run in production (from uvicorn)
def run() -> None:
    ui.run_with(fastapi_app, storage_secret=STORAGE_SECRET, title='eduIDM', prod_js=True)

if __name__ in {"__main__", "__mp_main__"}:
    logger.info(f"Starting eduIDM on {HOST}:{PORT}")
    if DTAP == "dev":
        ui.run(host=HOST, port=PORT, storage_secret=STORAGE_SECRET, title='eduIDM', show=False)
    else:
        print(f"In production: run with 'uvicorn main:run --workers 1 --port {PORT}'")
    run()
