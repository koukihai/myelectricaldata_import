import logging
from datetime import datetime

from datasources.db.usagepointdb import UsagePointDB
from datasources.gateway import Gateway


class Repository:
    @staticmethod
    def get_gateway_status():
        return Gateway.get_status()

    @staticmethod
    def get_account_status(usage_point_id: str):
        """
        Retrieve the account status from the gateway
        and stores it into the local db

        :return:
        """
        assert usage_point_id, "Operation not supported for unspecified usage point id"
        db = UsagePointDB(usage_point_id=usage_point_id)

        # Retrieve usage point config setting from DB
        usage_point_config = db.get_usage_point()

        # Read cache setting and token from retrieved config
        use_cache = getattr(usage_point_config, "cache", True)
        token = usage_point_config.token

        # Retrieve account status from the gateway using token
        status = Gateway.get_account_status(use_cache=use_cache, usage_point_id=usage_point_id, token=token)

        # If the status contains an "error" key, the request was successful, and we update the db
        if "error" not in status:
            db.update(
                consentement_expiration=datetime.strptime(
                    status["consent_expiration_date"], "%Y-%m-%dT%H:%M:%S"
                ),
                # last_call=datetime.datetime.strptime(status["last_call"], "%Y-%m-%dT%H:%M:%S.%f"),
                call_number=status["call_number"],
                quota_limit=status["quota_limit"],
                quota_reached=status["quota_reached"],
                quota_reset_at=datetime.strptime(status["quota_reset_at"], "%Y-%m-%dT%H:%M:%S.%f"),
                ban=status["ban"],
            )

        return status

    @staticmethod
    def get_contract(usage_point_id: str):
        from init import DB
        db = UsagePointDB(usage_point_id=usage_point_id)
        usage_point_config = db.get_usage_point()
        current_cache = db.get_contract()
        token = usage_point_config.token
        use_cache = getattr(usage_point_config, "cache", True)

        if not current_cache:
            # No cache
            logging.info(" =>  Pas de cache")
            result = Gateway.get_contract(usage_point_id=usage_point_id, token=token, use_cache=use_cache)
        elif getattr(usage_point_config, "refresh_contract", False):
            logging.info(" =>  Mise à jour du cache")
            result = Gateway.get_contract(usage_point_id=usage_point_id, token=token, use_cache=use_cache)
            usage_point_config.refresh_contact = False
            DB.set_usage_point(usage_point_id, usage_point_config.__dict__)
        else:
            # Get data in cache
            logging.info(" =>  Récupération du cache")
            result = {}
            for column in current_cache.__table__.columns:
                result[column.name] = str(getattr(current_cache, column.name))
            logging.debug(f" => {result}")

        if "error" not in result:
            for key, value in result.items():
                logging.info(f"{key}: {value}")
                db.set_contract(
                    usage_point_id,
                    {
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
                    },
                )
        else:
            logging.error(result)
        return result


        self.db.set_contract(
            self.usage_point_id,
            {
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
            },
        )
