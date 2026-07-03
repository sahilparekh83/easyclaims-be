from uuid import UUID
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field
from ...schemas.base import ResponseModel
from ...db.queries.float_query import FloatQuery
from ...db.queries.partner_query import PartnerQuery
from ...services.notification_helper import notify_partner
from ..users import _require_superadmin

admin_finance_router = APIRouter()


class TopUpBody(BaseModel):
    partner_id: str
    amount: int = Field(..., gt=0)
    note: Optional[str] = None


def _txn_dict(t, partner_name=None) -> dict:
    return {
        "id": str(t.id),
        "partner_id": str(t.partner_id),
        "partner_name": partner_name,
        "type": t.type,
        "amount": t.amount,
        "balance_after": t.balance_after,
        "note": t.note,
        "ref_type": t.ref_type,
        "ref_id": t.ref_id,
        "is_reconciled": t.is_reconciled,
        "reconciled_by": t.reconciled_by,
        "reconciled_at": t.reconciled_at.isoformat() if t.reconciled_at else None,
        "created_at": t.created_at.isoformat() if t.created_at else None,
    }


@admin_finance_router.post("/topup", response_model=ResponseModel, status_code=201)
async def top_up_partner(body: TopUpBody, request: Request, _=Depends(_require_superadmin)):
    """Admin credits a partner's prepaid float balance (billing entry)."""
    admin_id = request.state.user_payload.get("sub") if hasattr(request.state, "user_payload") else None
    pq = PartnerQuery()
    partner = pq.get_by_id(body.partner_id)
    if not partner:
        raise HTTPException(status_code=404, detail="Partner not found")

    fq = FloatQuery()
    try:
        txn = fq.top_up(body.partner_id, body.amount, note=body.note, created_by=admin_id)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))

    notify_partner(
        partner_id=body.partner_id,
        type="float_topup",
        title="Float Balance Credited",
        body=f"Your float balance has been topped up by {body.amount}. New balance: {txn.balance_after}.",
        ref_id=str(txn.id), ref_type="float_transaction",
    )
    return ResponseModel.ok(data=_txn_dict(txn, partner_name=partner.name))


@admin_finance_router.get("/ledger", response_model=ResponseModel)
async def list_ledger(
    request: Request,
    skip: int = 0,
    limit: int = 50,
    partner_id: Optional[str] = None,
    is_reconciled: Optional[bool] = None,
    type: Optional[str] = None,
    _=Depends(_require_superadmin),
):
    """Billing/Reconciliation ledger — every float top-up and per-enrollment deduction."""
    fq = FloatQuery()
    pq = PartnerQuery()
    total, txns = fq.list_all(skip=skip, limit=limit, partner_id=partner_id,
                              is_reconciled=is_reconciled, type=type)

    partner_cache = {}
    result = []
    for t in txns:
        pid = str(t.partner_id)
        if pid not in partner_cache:
            partner_cache[pid] = pq.get_by_id(pid)
        partner = partner_cache[pid]
        result.append(_txn_dict(t, partner_name=partner.name if partner else None))

    return ResponseModel.ok(data={"data": result, "total": total, "skip": skip, "limit": limit})


@admin_finance_router.patch("/ledger/{transaction_id}/reconcile", response_model=ResponseModel)
async def reconcile_transaction(transaction_id: UUID, request: Request,
                                _=Depends(_require_superadmin)):
    admin_id = request.state.user_payload.get("sub") if hasattr(request.state, "user_payload") else "admin"
    if not FloatQuery().mark_reconciled(str(transaction_id), admin_id):
        raise HTTPException(status_code=404, detail="Transaction not found")
    return ResponseModel.ok(data={"message": "Transaction marked as reconciled"})


@admin_finance_router.get("/dashboard", response_model=ResponseModel)
async def finance_dashboard(request: Request, _=Depends(_require_superadmin)):
    """Finance Dashboard — Billing (top-ups/deductions), Reconciliation status, Float Utilization."""
    fq = FloatQuery()
    pq = PartnerQuery()

    partners = pq.list_all(skip=0, limit=1000)
    total_float = sum(p.float_balance or 0 for p in partners)

    top_ups_this_month = fq.sum_by_type_this_month("top_up")
    deductions_this_month = fq.sum_by_type_this_month("deduction")

    _, unreconciled = fq.list_all(skip=0, limit=1000, is_reconciled=False, type="top_up")

    low_float = fq.list_low_float_partners()

    return ResponseModel.ok(data={
        "total_float_balance": total_float,
        "top_ups_this_month": top_ups_this_month,
        "deductions_this_month": deductions_this_month,
        "unreconciled_topups_count": len(unreconciled),
        "low_float_partners": [
            {"partner_id": str(p.id), "partner_name": p.name,
             "float_balance": p.float_balance, "low_float_threshold": p.low_float_threshold}
            for p in low_float
        ],
        "partners": [
            {"partner_id": str(p.id), "partner_name": p.name, "float_balance": p.float_balance}
            for p in partners
        ],
    })
