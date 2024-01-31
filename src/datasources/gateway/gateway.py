import json
import logging

from config import URL
from dependencies import get_version
from init import DB
from lib.query import Query


class Gateway:
    def __init__(self, headers=None):
        self.url = URL
        self.headers = headers

    def status(self):
        target = f"{self.url}/ping"
        status = {
            "version": get_version(),
            "status": False,
            "information": "MyElectricalData injoignable.",
        }
        try:
            response = Query(endpoint=target, headers=self.headers).get()
            if hasattr(response, "status_code") and response.status_code == 200:
                status = json.loads(response.text)
                for key, value in status.items():
                    logging.info(f"{key}: {value}")
                status["version"] = get_version()
                return status
            else:
                return status
        except LookupError:
            return status


class Status:
    def __init__(self, headers=None):
        self.db = DB
        self.url = URL
        self.headers = headers
