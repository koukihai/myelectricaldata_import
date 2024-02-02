import json
import logging
import traceback
from datetime import datetime

from dateutil.relativedelta import relativedelta

from config import URL
from dependencies import title
from init import DB, CONFIG
from lib.query import Query


class Tempo:
    def __init__(self):
        self.config = CONFIG
        self.db = DB
        self.url = URL
        self.valid_date = datetime.combine(datetime.now() + relativedelta(days=1), datetime.min.time())
        self.nb_check_day = 31

    def run(self):
        start = (datetime.now() - relativedelta(years=3)).strftime("%Y-%m-%d")
        end = (datetime.now() + relativedelta(days=2)).strftime("%Y-%m-%d")
        target = f"{self.url}/rte/tempo/{start}/{end}"
        query_response = Query(endpoint=target).get()
        if query_response.status_code == 200:
            try:
                response_json = json.loads(query_response.text)
                for date, color in response_json.items():
                    date = datetime.strptime(date, "%Y-%m-%d")
                    self.db.set_tempo(date, color)
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

    def get(self):
        data = self.db.get_tempo()
        output = {}
        for d in data:
            if hasattr(d, "date") and hasattr(d, "color"):
                output[d.date] = d.color
        return output

    def fetch(self):
        current_cache = self.db.get_tempo()
        result = {}
        if not current_cache:
            # No cache
            title(f"No cache")
            result = self.run()
        else:
            valid_date = self.valid_date
            missing_date = False
            for i in range(self.nb_check_day):
                if current_cache[i].date != valid_date:
                    missing_date = True
                valid_date = valid_date - relativedelta(days=1)
            if missing_date:
                result = self.run()
            else:
                logging.info(" => Toutes les données sont déjà en cache.")
        if "error" not in result:
            for key, value in result.items():
                logging.info(f"{key}: {value}")
        else:
            logging.error(result)
            return "OK"
        return result

    def fetch_day(self):
        target = f"{self.url}/edf/tempo/days"
        query_response = Query(endpoint=target).get()
        if query_response.status_code == 200:
            try:
                response_json = json.loads(query_response.text)
                self.db.set_tempo_config("days", response_json)
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

    def fetch_price(self):
        target = f"{self.url}/edf/tempo/price"
        query_response = Query(endpoint=target).get()
        if query_response.status_code == 200:
            try:
                response_json = json.loads(query_response.text)
                self.db.set_tempo_config("price", response_json)
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
