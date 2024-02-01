from datetime import datetime
from typing import Optional

from datasources.gateway.usagepointgw import UsagePointGW
from datasources.db.usagepointdb import UsagePointDB


class UsagePointRepository:
    def __init__(self, usage_point_id: Optional[str] = None):
        self.id = usage_point_id
        self.db = UsagePointDB(usage_point_id=usage_point_id)

    def get_account_status(self):
        """
        Retrieve the account status and stores it into the local db

        :param usage_point_id: Usage point ID for which the status is requested
        :return:
        """
        assert self.id, "Operation not supported for unspecified usage point id"

        # Retrieve usage point config setting from DB
        usage_point_config = self.db.get_usage_point()

        # Read cache setting and token from retrieved config
        use_cache = getattr(usage_point_config, "cache", True)
        token = usage_point_config.token

        # Retrieve account status from the gateway using token
        status = UsagePointGW(usage_point_id=self.id, token=token) \
            .get_account_status(use_cache=use_cache)

        # If the status contains an "error" key, the request was successful, and we update the db
        if "error" not in status:
            self.db.update(
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
