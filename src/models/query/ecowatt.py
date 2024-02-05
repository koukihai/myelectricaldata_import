import ast
import logging
from datetime import datetime
from dateutil.relativedelta import relativedelta
from dependencies import title
from models.datasources.gatewayapi import GatewayAPI


class Ecowatt:
    @staticmethod
    def load_data():
        from init import DB

        data = DB.get_ecowatt()
        output = {}
        for d in data:
            if hasattr(d, "date") and hasattr(d, "value") and hasattr(d, "message") and hasattr(d, "detail"):
                output[d.date] = {
                    "value": d.value,
                    "message": d.message,
                    "detail": ast.literal_eval(d.detail),
                }
        return output

    @staticmethod
    def get_data():
        from init import DB

        current_cache = DB.get_ecowatt()
        result = {}
        valid_date = datetime.combine(datetime.now() + relativedelta(days=2), datetime.min.time())

        if not current_cache:
            # No cache
            title(f"No cache")
            result = GatewayAPI.get_ecowatt_data()
        else:
            last_item = current_cache[0]
            if last_item.date < valid_date:
                result = GatewayAPI.get_ecowatt_data()
            else:
                logging.info(" => Toutes les données sont déjà en cache.")

        try:
            for date, data in result.items():
                date = datetime.strptime(date, "%Y-%m-%d")
                DB.set_ecowatt(date, data["value"], data["message"], str(data["detail"]))
        except ValueError:
            result = {
                "error": True,
                "description": "Erreur lors de la récupération des données Ecowatt.",
            }

        if "error" not in result:
            for key, value in result.items():
                logging.info(f"{key}: {value['message']}")
        else:
            logging.error(result)
            return "OK"
        return result
