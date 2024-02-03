import json
import logging
import re
import traceback
from datetime import datetime
from os import environ, getenv

from dependencies import get_version, header_generate
from lib.query import Query


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
    def get_contract(usage_point_id: str, token: str, use_cache: bool):
        from config import URL

        target = f"{URL}/contracts/{usage_point_id}"
        if use_cache:
            target += "/cache"

        query_response = Query(endpoint=target, headers=header_generate(token)).get()
        if query_response.status_code == 200:
            try:
                response_json = json.loads(query_response.text)
                response = response_json["customer"]["usage_points"][0]
                usage_point = response["usage_point"]
                contracts = response["contracts"]
                response = contracts
                response.update(usage_point)

                if contracts["offpeak_hours"] is not None:
                    offpeak_hours = re.search("HC \((.*)\)", contracts["offpeak_hours"]).group(1)
                else:
                    offpeak_hours = ""
                if "last_activation_date" in contracts and contracts["last_activation_date"] is not None:
                    last_activation_date = (
                        datetime.strptime(contracts["last_activation_date"], "%Y-%m-%d%z")
                    ).replace(tzinfo=None)
                else:
                    last_activation_date = contracts["last_activation_date"]
                if (
                        "last_distribution_tariff_change_date" in contracts
                        and contracts["last_distribution_tariff_change_date"] is not None
                ):
                    last_distribution_tariff_change_date = (
                        datetime.strptime(
                            contracts["last_distribution_tariff_change_date"],
                            "%Y-%m-%d%z",
                        )
                    ).replace(tzinfo=None)
                else:
                    last_distribution_tariff_change_date = contracts["last_distribution_tariff_change_date"]
                return {
                    "usage_point_status": usage_point["usage_point_status"],
                    "meter_type": usage_point["meter_type"],
                    "segment": contracts["segment"],
                    "subscribed_power": contracts["subscribed_power"],
                    "last_activation_date": last_activation_date,
                    "distribution_tariff": contracts["distribution_tariff"],
                    "offpeak_hours_0": offpeak_hours,
                    "offpeak_hours_1": offpeak_hours,
                    "offpeak_hours_2": offpeak_hours,
                    "offpeak_hours_3": offpeak_hours,
                    "offpeak_hours_4": offpeak_hours,
                    "offpeak_hours_5": offpeak_hours,
                    "offpeak_hours_6": offpeak_hours,
                    "contract_status": contracts["contract_status"],
                    "last_distribution_tariff_change_date": last_distribution_tariff_change_date,
                }
            except Exception as e:
                logging.error(e)
                traceback.print_exc()
                response = {
                    "error": True,
                    "description": "Erreur lors de la récupération du contrat.",
                }
            return response
        else:
            return {
                "error": True,
                "description": json.loads(query_response.text)["detail"],
            }
