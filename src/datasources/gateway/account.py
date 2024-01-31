import datetime
import json
import logging
import traceback
from os import environ, getenv

from lib.query import Query


class Account:
    def __init__(self, headers=None):
        from config import URL
        from init import DB

        self.db = DB
        self.url = URL
        self.headers = headers

    def status(self, usage_point_id: str, use_cache: bool):
        target = f"{self.url}/valid_access/{usage_point_id}"
        if use_cache:
            target += "/cache"
        response = Query(endpoint=target, headers=self.headers).get()
        if response:
            status = json.loads(response.text)
            if response.status_code == 200:
                try:
                    for key, value in status.items():
                        logging.info(f"{key}: {value}")
                    return status
                except Exception as e:
                    if "DEBUG" in environ and getenv("DEBUG"):
                        traceback.print_exc()
                    logging.error(e)
                    return {
                        "error": True,
                        "description": "Erreur lors de la récupération du statut du compte.",
                    }
            else:
                if "DEBUG" in environ and getenv("DEBUG"):
                    traceback.print_exc()
                logging.error(status["detail"])
                return {"error": True, "description": status["detail"]}
        else:
            if "DEBUG" in environ and getenv("DEBUG"):
                traceback.print_exc()
            return {
                "error": True,
                "status_code": response.status_code,
                "description": json.loads(response.text),
            }
