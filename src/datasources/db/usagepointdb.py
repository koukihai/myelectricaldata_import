from typing import List, Optional

from db_schema import UsagePoints
from sqlalchemy import create_engine, delete, inspect, update, select, func, desc, asc


class UsagePointDB:
    def __init__(self, usage_point_id: Optional[str]):
        from init import DB
        self.db = DB
        self.id = usage_point_id

    def update(
            self,
            consentement_expiration=None,
            call_number=None,
            quota_reached=None,
            quota_limit=None,
            quota_reset_at=None,
            last_call=None,
            ban=None,
    ):
        query = select(UsagePoints).where(UsagePoints.usage_point_id == self.id)
        usage_points = self.db.one_or_none(query)
        if consentement_expiration is not None:
            usage_points.consentement_expiration = consentement_expiration
        if call_number is not None:
            usage_points.call_number = call_number
        if quota_reached is not None:
            usage_points.quota_reached = quota_reached
        if quota_limit is not None:
            usage_points.quota_limit = quota_limit
        if quota_reset_at is not None:
            usage_points.quota_reset_at = quota_reset_at
        if last_call is not None:
            usage_points.last_call = last_call
        if ban is not None:
            usage_points.ban = ban
        self.db.flush()
        self.db.close()

    def get_usage_point(self):
        query = select(UsagePoints).where(UsagePoints.usage_point_id == self.id)
        data = self.db.one_or_none(query)
        self.db.close()
        return data

