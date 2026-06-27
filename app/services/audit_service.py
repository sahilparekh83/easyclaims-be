import logging
from typing import Optional

logger = logging.getLogger(__name__)


class AuditService:

    def log(
        self,
        actor_id: Optional[str],
        actor_type: Optional[str],
        action: str,
        entity_type: Optional[str] = None,
        entity_id: Optional[str] = None,
        old_value: Optional[dict] = None,
        new_value: Optional[dict] = None,
        ip_address: Optional[str] = None,
        note: Optional[str] = None,
    ) -> None:
        try:
            from ..db.queries.audit_log_query import AuditLogQuery
            AuditLogQuery().create(
                actor_id=actor_id,
                actor_type=actor_type,
                action=action,
                entity_type=entity_type,
                entity_id=entity_id,
                old_value=old_value,
                new_value=new_value,
                ip_address=ip_address,
                note=note,
            )
        except Exception:
            logger.exception("Audit log write failed — action=%s entity=%s/%s", action, entity_type, entity_id)
