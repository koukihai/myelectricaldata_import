from datetime import datetime

from datasources.gateway.account import Account as AccountGW
from datasources.db.usage_point import UsagePoint


class Account:
    def __init__(self, headers=None):
        self.gw = AccountGW(headers=headers)
        self.db = UsagePoint()

    def status(self, usage_point_id: str):
        """
        Retrieve the account status and stores it into the local db

        :param usage_point_id: Usage point ID for which the status is requested
        :return:
        """
        usage_point_config = UsagePoint().get_usage_point(usage_point_id=usage_point_id)

        # Use cache setting if provided, otherwise default to True
        use_cache = getattr(usage_point_config, "cache", True)

        status = self.gw.status(usage_point_id=usage_point_id, use_cache=use_cache)

        # If the status contains an "error" key, the request was successful, and we update the db
        if "error" not in status:
            self.db.update(
                usage_point_id,
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

