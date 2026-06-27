from typing import Optional, List, Tuple
from ..session import session_scope
from ..models.audit_log import AuditLog


class AuditLogQuery:

    def create(
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
    ) -> AuditLog:
        with session_scope() as session:
            entry = AuditLog(
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
            session.add(entry)
            session.flush()
            session.expunge(entry)
            return entry

    def list_paginated(
        self,
        entity_type: Optional[str] = None,
        entity_id: Optional[str] = None,
        actor_id: Optional[str] = None,
        skip: int = 0,
        limit: int = 50,
    ) -> Tuple[int, List[AuditLog]]:
        with session_scope() as session:
            q = session.query(AuditLog)
            if entity_type:
                q = q.filter(AuditLog.entity_type == entity_type)
            if entity_id:
                q = q.filter(AuditLog.entity_id == entity_id)
            if actor_id:
                q = q.filter(AuditLog.actor_id == actor_id)
            total = q.count()
            rows = q.order_by(AuditLog.created_at.desc()).offset(skip).limit(limit).all()
            for r in rows:
                session.expunge(r)
            return total, rows
