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

