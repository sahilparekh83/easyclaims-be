from typing import Optional, List
from pydantic import BaseModel
from .base import BaseAgent
from .prompts import DASHBOARD_INSIGHTS


class Insight(BaseModel):
    message: str
    is_alert: bool = False


class DashboardInsightsResponse(BaseModel):
    insights: List[Insight]


class DashboardInsightsAgent(BaseAgent):
    agent_name = "dashboard_insights"

    def generate(
        self,
        partner_name: str,
        period: str,
        total_members: int,
        active_members: int,
        expiring_soon: int,
        renewals_done: int,
        float_balance: float,
        claims_count: int,
        open_tickets: int,
        partner_id: Optional[str] = None,
    ) -> DashboardInsightsResponse:
        prompt = DASHBOARD_INSIGHTS.format(
            partner_name=partner_name,
            period=period,
            total_members=total_members,
            active_members=active_members,
            expiring_soon=expiring_soon,
            renewals_done=renewals_done,
            float_balance=float_balance,
            claims_count=claims_count,
            open_tickets=open_tickets,
        )
        return self._run(
            prompt=prompt,
            response_schema=DashboardInsightsResponse,
            reference_id=partner_id,
            reference_type="partner",
        )
