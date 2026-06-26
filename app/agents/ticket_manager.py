from typing import Optional
from pydantic import BaseModel
from .base import BaseAgent
from .prompts import TICKET_MANAGER


class TicketClassification(BaseModel):
    category: str    # "claim" | "query" | "correction" | "renewal"
    priority: str    # "high" | "medium" | "low"
    summary: str
    is_duplicate: bool = False


class TicketManagerAgent(BaseAgent):
    agent_name = "ticket_manager"

    def classify(
        self,
        message: str,
        channel: str,
        member_name: str,
        member_id: Optional[str] = None,
    ) -> TicketClassification:
        prompt = TICKET_MANAGER.format(
            message=message,
            channel=channel,
            member_name=member_name,
        )
        return self._run(
            prompt=prompt,
            response_schema=TicketClassification,
            reference_id=member_id,
            reference_type="member",
        )
