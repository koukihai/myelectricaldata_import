import json
import logging
import re
import traceback
from datetime import datetime
from os import environ, getenv

from dependencies import get_version, header_generate
from lib.query import Query
from datetime import datetime
from dateutil.relativedelta import relativedelta

class GatewayAPI:
    @staticmethod
    def get_status():
        from config import URL
        target = f"{URL}/ping"
        status = {
            "version": get_version(),
            "status": False,
            "information": "MyElectricalData injoignable.",
        }
        try:
            response = Query(endpoint=target).get()
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

    @staticmethod
    def get_account_status(usage_point_id: str, token: str, use_cache: bool):
        from config import URL

        target = f"{URL}/valid_access/{usage_point_id}"
        if use_cache:
            target += "/cache"
        response = Query(endpoint=target, headers=header_generate(token)).get()
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

    @staticmethod
    def get_tempo_data():
        from config import URL

        start = (datetime.now() - relativedelta(years=3)).strftime("%Y-%m-%d")
        end = (datetime.now() + relativedelta(days=2)).strftime("%Y-%m-%d")
        target = f"{URL}/rte/tempo/{start}/{end}"
        query_response = Query(endpoint=target).get()
        if query_response.status_code == 200:
            try:
                response_json = json.loads(query_response.text)
                response = response_json
            except Exception as e:
                logging.error(e)
                traceback.print_exc()
                response = {
                    "error": True,
                    "description": "Erreur lors de la récupération de données Tempo.",
                }
            return response
        else:
            return {
                "error": True,
                "description": json.loads(query_response.text)["detail"],
            }

    @staticmethod
    def get_tempo_days():
        from config import URL

        target = f"{URL}/edf/tempo/days"
        query_response = Query(endpoint=target).get()
        return query_response

    @staticmethod
    def get_tempo_price():
        from config import URL
        target = f"{URL}/edf/tempo/price"
        return Query(endpoint=target).get()

    @staticmethod
    def get_ecowatt_data():
        from config import URL

        start = (datetime.now() - relativedelta(years=3)).strftime("%Y-%m-%d")
        end = (datetime.now() + relativedelta(days=3)).strftime("%Y-%m-%d")
        target = f"{URL}/rte/ecowatt/{start}/{end}"
        query_response = Query(endpoint=target).get()
        if query_response.status_code == 200:
            try:
                response_json = json.loads(query_response.text)
                response = response_json
            except Exception as e:
                logging.error(e)
                traceback.print_exc()
                response = {
                    "error": True,
                    "description": "Erreur lors de la récupération des données Ecowatt.",
                }
            return response
        else:
            return {
                "error": True,
                "description": json.loads(query_response.text)["detail"],
            }
