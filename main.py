import logging
import json
import os

from nicegui import ui, app

import eduid_oidc.oidc_callback
import routes.accept

# register routes
import routes.api
import routes.landing
import routes.m         # all /m routes
from services.logging import logger, setup_logging

try:
    settings = json.load(open('settings.json'))
except Exception:
    settings = {}
    print("Warning: could not load settings.json; set storage_secret for production use!")

DTAP, STORAGE_SECRET, LOG_LEVEL, CONSOLE_LOGGING = (
    settings.get('DTAP', 'dev'),
    settings.get('storage_secret', 'your-secret-here'),
    settings.get('log_level', 'INFO'),
    settings.get('console_logging', False)
)

setup_logging(
    log_file='eduidm.log',
    level=LOG_LEVEL,
    enable_console_logging=CONSOLE_LOGGING
)

app.add_static_files('/img', 'img')

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
