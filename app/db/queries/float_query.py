import uuid as _uuid
from datetime import datetime, timezone
from typing import List, Optional, Tuple
from ..session import session_scope
from ..models.float_transaction import FloatTransaction
from ..models.partner import Partner


def utcnow():
    return datetime.now(timezone.utc)


class FloatQuery:

    def get_balance(self, partner_id: str) -> Optional[int]:
        with session_scope() as session:
            p = session.query(Partner).filter(Partner.id == _uuid.UUID(str(partner_id))).first()
            return p.float_balance if p else None

    def top_up(self, partner_id: str, amount: int, note: str = None,
              created_by: str = None) -> FloatTransaction:
        if amount <= 0:
            raise ValueError("Top-up amount must be positive")
        with session_scope() as session:
            partner = session.query(Partner).filter(Partner.id == _uuid.UUID(str(partner_id))).first()
            if not partner:
                raise ValueError("Partner not found")
            partner.float_balance = (partner.float_balance or 0) + amount
            t = FloatTransaction(
                partner_id=partner_id, type="top_up", amount=amount,
                balance_after=partner.float_balance, note=note, created_by=created_by,
            )
            session.add(t)
            session.flush()
            session.expunge(t)
            return t

    def deduct(self, partner_id: str, amount: int, ref_type: str = None,
              ref_id: str = None, note: str = None) -> Optional[FloatTransaction]:
        """Deducts from a partner's float balance. Balance is allowed to go negative —
        this only records the transaction and updates the running balance; callers
        should check the resulting balance/threshold themselves for low-float alerts."""
        if amount <= 0:
            return None
        with session_scope() as session:
            partner = session.query(Partner).filter(Partner.id == _uuid.UUID(str(partner_id))).first()
            if not partner:
                return None
            partner.float_balance = (partner.float_balance or 0) - amount
            t = FloatTransaction(
                partner_id=partner_id, type="deduction", amount=amount,
                balance_after=partner.float_balance, note=note,
                ref_type=ref_type, ref_id=ref_id,
            )
            session.add(t)
            session.flush()
            session.expunge(t)
            return t

    def mark_reconciled(self, transaction_id: str, admin_id: str) -> bool:
        with session_scope() as session:
            t = session.query(FloatTransaction).filter(
                FloatTransaction.id == _uuid.UUID(str(transaction_id))
            ).first()
            if not t:
                return False
            t.is_reconciled = True
            t.reconciled_by = admin_id
            t.reconciled_at = utcnow()
            session.flush()
            return True

    def list_all(self, skip: int = 0, limit: int = 100, partner_id: str = None,
                is_reconciled: bool = None, type: str = None) -> Tuple[int, List[FloatTransaction]]:
        with session_scope() as session:
            q = session.query(FloatTransaction)
            if partner_id:
                q = q.filter(FloatTransaction.partner_id == _uuid.UUID(str(partner_id)))
            if is_reconciled is not None:
                q = q.filter(FloatTransaction.is_reconciled == is_reconciled)
            if type:
                q = q.filter(FloatTransaction.type == type)
            total = q.count()
            rows = q.order_by(FloatTransaction.created_at.desc()).offset(skip).limit(limit).all()
            for r in rows:
                session.expunge(r)
            return total, rows

    def sum_by_type_this_month(self, type: str) -> int:
        today = utcnow()
        with session_scope() as session:
            rows = session.query(FloatTransaction).filter(
                FloatTransaction.type == type,
                FloatTransaction.created_at >= today.replace(day=1, hour=0, minute=0, second=0, microsecond=0),
            ).all()
            return sum(r.amount for r in rows)

    def list_low_float_partners(self) -> List[Partner]:
        with session_scope() as session:
            rows = session.query(Partner).filter(
                Partner.is_deleted == False,
                Partner.float_balance <= Partner.low_float_threshold,
            ).all()
            for r in rows:
                session.expunge(r)
            return rows
