import json
import logging
import traceback
from datetime import datetime
from dateutil.relativedelta import relativedelta

from models.datasources.gatewayapi import GatewayAPI


class Tempo:
    @staticmethod
    def load_data():
        from init import DB

        data = DB.get_tempo()
        output = {}
        for d in data:
            if hasattr(d, "date") and hasattr(d, "color"):
                output[d.date] = d.color
        return output

    @staticmethod
    def get_data():
        from init import DB
        from dependencies import title

        current_cache = DB.get_tempo()
        valid_date = datetime.combine(datetime.now() + relativedelta(days=1), datetime.min.time())
        nb_check_day = 31

        result = {}
        if not current_cache:
            # No cache
            title(f"No cache")
            result = GatewayAPI.get_tempo_data()
        else:
            missing_date = False
            for i in range(nb_check_day):
                if current_cache[i].date != valid_date:
                    missing_date = True
                valid_date = valid_date - relativedelta(days=1)
            if missing_date:
                result = GatewayAPI.get_tempo_data()
            else:
                logging.info(" => Toutes les données sont déjà en cache.")

        try:
            for date, color in result.items():
                date = datetime.strptime(date, "%Y-%m-%d")
                DB.set_tempo(date, color)
        except ValueError:
            result = {'error': True, 'description': 'Erreur lors de la récupération de données Tempo.'}

        if "error" not in result:
            for date, color in result.items():
                logging.info(f"{date}: {color}")
            return result
        else:
            logging.error(result)
            return "OK"

    @staticmethod
    def get_days():
        from init import DB

        query_response = GatewayAPI.get_tempo_days()
        if query_response.status_code == 200:
            try:
                response_json = json.loads(query_response.text)
                DB.set_tempo_config("days", response_json)
                response = {"error": False, "description": "", "items": response_json}
                logging.info(" => Toutes les valeurs sont misent à jours.")
            except Exception as e:
                logging.error(e)
                traceback.print_exc()
                response = {
                    "error": True,
                    "description": "Erreur lors de la récupération de jours Tempo.",
                }
            return response
        else:
            return {
                "error": True,
                "description": json.loads(query_response.text)["detail"],
            }

    @staticmethod
    def get_price():
        from init import DB

        query_response = GatewayAPI.get_tempo_price()
        if query_response.status_code == 200:
            try:
                response_json = json.loads(query_response.text)
                DB.set_tempo_config("price", response_json)
                response = {"error": False, "description": "", "items": response_json}
                logging.info(" => Toutes les valeurs sont misent à jours.")
            except Exception as e:
                logging.error(e)
                traceback.print_exc()
                response = {
                    "error": True,
                    "description": "Erreur lors de la récupération de jours Tempo.",
                }
            return response
        else:
            return {
                "error": True,
                "description": json.loads(query_response.text)["detail"],
            }

