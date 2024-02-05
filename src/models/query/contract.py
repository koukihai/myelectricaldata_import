import logging

from models.datasources.gatewayapi import GatewayAPI


class Contract:
    @staticmethod
    def get(usage_point_id: str):
        from init import DB
        current_cache = DB.get_contract(usage_point_id=usage_point_id)
        usage_point_config = DB.get_usage_point(usage_point_id=usage_point_id)

        # Read cache setting and token from retrieved config
        use_cache = getattr(usage_point_config, "cache", True)
        token = usage_point_config.token

        if not current_cache:
            # No cache
            logging.info(" =>  Pas de cache")
            result = GatewayAPI.get_contract(use_cache=use_cache, usage_point_id=usage_point_id, token=token)
        else:
            # Refresh cache
            if hasattr(usage_point_config, "refresh_contract") and usage_point_config.refresh_contract:
                logging.info(" =>  Mise à jour du cache")
                result = GatewayAPI.get_contract(use_cache=use_cache, usage_point_id=usage_point_id, token=token)
                usage_point_config.refresh_contract = False
                DB.set_usage_point(usage_point_id, usage_point_config.__dict__)
            else:
                # Get data in cache
                logging.info(" =>  Récupération du cache")
                result = {}
                for column in current_cache.__table__.columns:
                    result[column.name] = str(getattr(current_cache, column.name))
                logging.debug(f" => {result}")

        if "_set_contract" in result:
            DB.set_contract(usage_point_id=usage_point_id, data=result["_set_contract"])

        if "error" not in result:
            for key, value in result.items():
                logging.info(f"{key}: {value}")
        else:
            logging.error(result)
        return result
