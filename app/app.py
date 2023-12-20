import logging
import os
from os import getenv, environ

import uvicorn
from fastapi import FastAPI, APIRouter
from fastapi.openapi.utils import get_openapi
from fastapi.staticfiles import StaticFiles
from fastapi_utils.tasks import repeat_every

from config import LOG_FORMAT, LOG_FORMAT_DATE, cycle_minimun
from utils import title, get_version, title_warning, logo, APPLICATION_PATH
from init import CONFIG, DB
from models.jobs import Job
from routers import account
from routers import action
from routers import data
from routers import html
from routers import info

APP = FastAPI(
    title="MyElectricalData",
    swagger_ui_parameters={
        "operationsSorter": "method",
        # "defaultModelRendering": "model",
        "tagsSorter": "alpha",
        # "docExpansion": "none",
        "deepLinking": True,
    }
)
APP.include_router(info.ROUTER)
APP.include_router(html.ROUTER)
APP.include_router(data.ROUTER)
APP.include_router(action.ROUTER)
APP.include_router(account.ROUTER)

static_dir = os.path.join(APPLICATION_PATH, "static")
APP.mount("/static", StaticFiles(directory=static_dir), name="static")


INFO = {
    "title": "MyElectricalData",
    "version": get_version(),
    "description": "",
    "contact": {
        "name": "m4dm4rtig4n",
        "url": "https://github.com/MyElectricalData/myelectricaldata/issues",
    },
    "license_info": {
        "name": "Apache 2.0",
        "url": "https://www.apache.org/licenses/LICENSE-2.0.html",
    },
    "routes": APP.routes,
    "servers": [],
}

OPENAPI_SCHEMA = get_openapi(
    title=INFO["title"],
    version=INFO["version"],
    description=INFO["description"],
    contact=INFO["contact"],
    license_info=INFO["license_info"],
    routes=INFO["routes"],
    servers=INFO["servers"],
)
OPENAPI_SCHEMA["info"]["x-logo"] = {
    "url": "https://pbs.twimg.com/profile_images/1415338422143754242/axomHXR0_400x400.png"
}

APP.openapi_schema = OPENAPI_SCHEMA


def validate_cycle():
    CYCLE = CONFIG.get('cycle')
    if not CYCLE:
        CYCLE = 14400
    else:
        if CYCLE < cycle_minimun:
            logging.warning("Le cycle minimun est de 3600s")
            CYCLE = cycle_minimun
            CONFIG.set("cycle", cycle_minimun)
    return CYCLE


@APP.on_event("startup")
@repeat_every(seconds=validate_cycle(), wait_first=False)
def import_job():
    Job().boot()


@APP.on_event("startup")
@repeat_every(seconds=3600, wait_first=True)
def home_assistant_export():
    Job().export_home_assistant(target="ecowatt")


@APP.on_event("startup")
@repeat_every(seconds=600, wait_first=False)
def gateway_status():
    Job().get_gateway_status()


def main():
    if "DEV" in environ or "DEBUG" in environ:
        title_warning("Run in Development mode")
    else:
        title("Run in production mode")

    logo(get_version())
    log_config = uvicorn.config.LOGGING_CONFIG
    log_config["formatters"]["access"]["fmt"] = LOG_FORMAT
    log_config["formatters"]["access"]["datefmt"] = LOG_FORMAT_DATE
    log_config["formatters"]["default"]["fmt"] = LOG_FORMAT
    log_config["formatters"]["default"]["datefmt"] = LOG_FORMAT_DATE
    uvicorn_params = {
        "host": "0.0.0.0",
        "port": CONFIG.port(),
        "log_config": log_config,
    }
    if ("DEV" in environ and getenv("DEV")) or ("DEBUG" in environ and getenv("DEBUG")):
        uvicorn_params["reload"] = True
        uvicorn_params["reload_dirs"] = ["/app"]

    ssl_config = CONFIG.ssl_config()
    if ssl_config:
        uvicorn_params = {**uvicorn_params, **ssl_config}

    uvicorn.run("app:APP", **uvicorn_params)


if __name__ == '__main__':
    main()
