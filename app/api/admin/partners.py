import io
import re
from uuid import UUID
import openpyxl
from openpyxl.styles import PatternFill, Font
from fastapi import APIRouter, Depends, File, Request, UploadFile
from fastapi.responses import StreamingResponse
from ...schemas.base import ResponseModel
from ...schemas.partner import PartnerCreate, PartnerUpdate
from ...schemas.list_request import PartnerListRequest, MemberListRequest, PolicyListRequest
from ...services.partner_service import PartnerService
from ...services.plan_service import PlanService
from ...services.audit_service import AuditService
from ...db.queries.partner_query import PartnerQuery
from ...db.queries.user_query import UserQuery
from ...db.queries.member_query import MemberQuery
from ...db.queries.policy_query import PolicyQuery
from ...db.queries.policy_type_query import PolicyTypeQuery
from ..users import _require_superadmin
from ..plans import _plan_to_dict
from fastapi import HTTPException

admin_partners_router = APIRouter()


def _partner_dict(p, user=None) -> dict:
    return {
        "id": str(p.id),
        "user_id": str(p.user_id),
        "name": p.name,
        "partner_type": p.partner_type,
        "city": p.city,
        "state": getattr(p, "state", None),
        "legal_company_name": getattr(p, "legal_company_name", None),
        "trade_name": getattr(p, "trade_name", None),
        "registered_address": getattr(p, "registered_address", None),
        "pin_code": getattr(p, "pin_code", None),
        "gstin": getattr(p, "gstin", None),
        "pan": getattr(p, "pan", None),
        "authorized_signatory_name": getattr(p, "authorized_signatory_name", None),
        "designation": getattr(p, "designation", None),
        "data_1": getattr(p, "data_1", None),
        "data_2": getattr(p, "data_2", None),
        "data_3": getattr(p, "data_3", None),
        "status": p.status,
        "email": str(user.email) if user else None,
        "mobile_no": user.mobile_no if user else None,
        "api_key": p.api_key,
        "api_rate_limit": p.api_rate_limit,
        "created_at": p.created_at.isoformat() if p.created_at else None,
    }


def _enrich(partners: list) -> list:
    uq = UserQuery()
    mq = MemberQuery()
    result = []
    for p in partners:
        user = uq.get_user_by_id(str(p.user_id))
        d = _partner_dict(p, user)
        d["member_count"] = mq.count_by_partner(str(p.id))
        result.append(d)
    return result


@admin_partners_router.post("/list", response_model=ResponseModel)
async def list_partners(
    body: PartnerListRequest,
    request: Request,
    _=Depends(_require_superadmin),
):
    """
    Paginated partner list.

    filters[] supports: name, partner_type, status, city
    """
    pq = PartnerQuery()
    total, partners = pq.list_paginated(body)
    return ResponseModel.ok(data={
        "data": _enrich(partners),
        "total": total,
        "skip": body.skip,
        "limit": body.limit,
    })


@admin_partners_router.post("", response_model=ResponseModel, status_code=201)
async def create_partner(body: PartnerCreate, request: Request, _=Depends(_require_superadmin)):
    p = PartnerService().create(body)
    user = UserQuery().get_user_by_id(str(p.user_id))
    return ResponseModel.ok(data=_partner_dict(p, user))


# ── Column map for partner bulk upload ───────────────────────────────────────
_PARTNER_COL_MAP = {
    "partner type":                "partner_type",
    "legal company name":          "legal_company_name",
    "trade name":                  "trade_name",
    "trade name/brand name":       "trade_name",
    "registered office address":   "registered_address",
    "city":                        "city",
    "state":                       "state",
    "pin code":                    "pin_code",
    "gstin":                       "gstin",
    "pan":                         "pan",
    "authorized signatory name":   "authorized_signatory_name",
    "designation":                 "designation",
    "mobile number":               "mobile_no",
    "email id":                    "email",
    "data 1":                      "data_1",
    "data 2":                      "data_2",
    "data 3":                      "data_3",
}

_PARTNER_MANDATORY = {
    "legal_company_name", "trade_name", "registered_address", "city",
    "state", "pin_code", "gstin", "pan",
    "authorized_signatory_name", "designation", "mobile_no", "email",
}

_GSTIN_RE = re.compile(r"^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1}$")
_PAN_RE   = re.compile(r"^[A-Z]{5}[0-9]{4}[A-Z]{1}$")
_PIN_RE   = re.compile(r"^\d{6}$")
_MOB_RE   = re.compile(r"^\+?[\d\s\-()]{7,15}$")


def _validate_partner_row(row_data: dict) -> list:
    """Return list of error strings for a parsed row dict. Empty list = valid."""
    errors = []
    for field in _PARTNER_MANDATORY:
        if not row_data.get(field):
            label = field.replace("_", " ").title()
            errors.append(f"{label} is required")

    gstin = row_data.get("gstin", "")
    if gstin and not _GSTIN_RE.match(gstin.upper()):
        errors.append("Invalid GSTIN format (expected 15 chars, e.g. 27AAPFU0939F1ZV)")

    pan = row_data.get("pan", "")
    if pan and not _PAN_RE.match(pan.upper()):
        errors.append("Invalid PAN format (expected 10 chars, e.g. AAPFU0939F)")

    pin = row_data.get("pin_code", "")
    if pin and not _PIN_RE.match(str(pin)):
        errors.append("Invalid Pin Code — must be exactly 6 digits")

    mob = row_data.get("mobile_no", "")
    if mob and not _MOB_RE.match(mob):
        errors.append("Invalid Mobile Number format")

    return errors


def _parse_partner_excel(contents: bytes):
    """Parse Excel bytes → (header_row, data_rows, col_idx)."""
    wb = openpyxl.load_workbook(filename=io.BytesIO(contents), read_only=True, data_only=True)
    ws = wb.active
    rows = list(ws.iter_rows(values_only=True))
    wb.close()
    if not rows:
        raise HTTPException(status_code=422, detail="Excel file is empty")
    header = [str(c).strip().lower() if c else "" for c in rows[0]]
    col_idx = {_PARTNER_COL_MAP[h]: i for i, h in enumerate(header) if h in _PARTNER_COL_MAP}
    missing = _PARTNER_MANDATORY - set(col_idx.keys())
    if missing:
        raise HTTPException(
            status_code=422,
            detail=f"Missing mandatory columns: {', '.join(sorted(missing))}"
        )
    return rows[0], rows[1:], col_idx


def _row_to_dict(row, col_idx: dict) -> dict:
    def cell(field):
        idx = col_idx.get(field)
        if idx is None:
            return None
        v = row[idx] if idx < len(row) else None
        return str(v).strip() if v is not None else None
    return {field: cell(field) for field in list(_PARTNER_COL_MAP.values())}


@admin_partners_router.post("/bulk-upload", response_model=ResponseModel, status_code=201)
async def bulk_upload_partners(
    request: Request,
    file: UploadFile = File(...),
    _=Depends(_require_superadmin),
):
    """
    Upload an Excel file to bulk-create partners.
    Mandatory columns: Legal Company Name, Trade Name/Brand Name, Registered Office Address,
    City, State, Pin Code, GSTIN, PAN, Authorized Signatory Name, Designation,
    Mobile Number, Email ID.
    Optional: Partner Type, Data 1, Data 2, Data 3.
    """
    contents = await file.read()
    try:
        header_row, data_rows, col_idx = _parse_partner_excel(contents)
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=422, detail="Invalid Excel file — must be .xlsx format")

    svc = PartnerService()
    uq = UserQuery()
    admin_id = getattr(request.state, "user_id", "admin")
    ip = request.client.host if request.client else None
    results = {"created": [], "skipped": [], "errors": []}

    for row_num, row in enumerate(data_rows, start=2):
        rd = _row_to_dict(row, col_idx)
        row_errors = _validate_partner_row(rd)
        if row_errors:
            results["errors"].append({
                "row": row_num,
                "email": rd.get("email"),
                "errors": row_errors,
            })
            continue
        try:
            partner_data = PartnerCreate(
                name=rd["authorized_signatory_name"],
                email=rd["email"],
                mobile_no=rd["mobile_no"],
                partner_type=rd.get("partner_type") or "Broker",
                legal_company_name=rd["legal_company_name"],
                trade_name=rd["trade_name"],
                registered_address=rd["registered_address"],
                city=rd["city"],
                state=rd["state"],
                pin_code=rd["pin_code"],
                gstin=rd["gstin"].upper(),
                pan=rd["pan"].upper(),
                authorized_signatory_name=rd["authorized_signatory_name"],
                designation=rd["designation"],
                data_1=rd.get("data_1"),
                data_2=rd.get("data_2"),
                data_3=rd.get("data_3"),
            )
            p = svc.create(partner_data)
            results["created"].append({"row": row_num, "email": rd["email"], "id": str(p.id)})
        except HTTPException as e:
            results["skipped"].append({"row": row_num, "email": rd.get("email"), "reason": e.detail})
        except Exception as e:
            results["errors"].append({"row": row_num, "email": rd.get("email"), "errors": [str(e)]})

    AuditService().log(
        actor_id=admin_id, actor_type="admin",
        action="bulk_upload",
        entity_type="partner",
        note=f"Partner bulk upload: {len(results['created'])} created, {len(results['skipped'])} skipped, {len(results['errors'])} errors",
        ip_address=ip,
    )
    return ResponseModel.ok(data={"total_rows": len(data_rows), **results})


@admin_partners_router.post("/bulk-upload/report")
async def partner_bulk_upload_report(
    request: Request,
    file: UploadFile = File(...),
    _=Depends(_require_superadmin),
):
    """
    Dry-run the same file and return an annotated Excel with:
    - Green row = valid
    - Red row = has errors
    - 'Status' column appended
    - 'Error Details' column appended
    """
    contents = await file.read()
    try:
        header_row, data_rows, col_idx = _parse_partner_excel(contents)
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=422, detail="Invalid Excel file")

    # Build annotated workbook
    wb_out = openpyxl.Workbook()
    ws_out = wb_out.active
    ws_out.title = "Partner Upload Report"

    GREEN_FILL = PatternFill(start_color="C6EFCE", end_color="C6EFCE", fill_type="solid")
    RED_FILL   = PatternFill(start_color="FFC7CE", end_color="FFC7CE", fill_type="solid")
    HDR_FILL   = PatternFill(start_color="BDD7EE", end_color="BDD7EE", fill_type="solid")
    GREEN_FONT = Font(color="276128", bold=False)
    RED_FONT   = Font(color="9C0006", bold=False)
    HDR_FONT   = Font(bold=True)

    # Write header row + two extra columns
    header_list = list(header_row) + ["Status", "Error Details"]
    for col_idx_h, val in enumerate(header_list, start=1):
        cell = ws_out.cell(row=1, column=col_idx_h, value=val)
        cell.fill = HDR_FILL
        cell.font = HDR_FONT

    status_col = len(header_list) - 1  # 1-indexed
    error_col  = len(header_list)

    # Process each data row
    for row_num, row in enumerate(data_rows, start=2):
        rd = _row_to_dict(row, col_idx)
        row_errors = _validate_partner_row(rd)
        fill   = RED_FILL   if row_errors else GREEN_FILL
        font   = RED_FONT   if row_errors else GREEN_FONT
        status = "Error ✗"  if row_errors else "Success ✓"
        err_msg = "; ".join(row_errors) if row_errors else ""

        for col_i, val in enumerate(row, start=1):
            cell = ws_out.cell(row=row_num, column=col_i, value=val)
            cell.fill = fill
            cell.font = font

        # Pad any missing cells up to status column
        for col_i in range(len(row) + 1, status_col):
            ws_out.cell(row=row_num, column=col_i, value="").fill = fill

        ws_out.cell(row=row_num, column=status_col, value=status).fill = fill
        err_cell = ws_out.cell(row=row_num, column=error_col, value=err_msg)
        err_cell.fill = fill
        err_cell.font = font

    # Auto-size columns (approximate)
    for col in ws_out.columns:
        max_len = max((len(str(c.value or "")) for c in col), default=0)
        ws_out.column_dimensions[col[0].column_letter].width = min(max_len + 4, 50)

    buf = io.BytesIO()
    wb_out.save(buf)
    buf.seek(0)

    return StreamingResponse(
        buf,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=partner_upload_report.xlsx"},
    )


@admin_partners_router.get("/bulk-upload/sample")
async def download_partner_sample_excel(_=Depends(_require_superadmin)):
    """Return a sample Excel file with the correct partner upload column headers."""
    from io import BytesIO
    from openpyxl.styles import Alignment

    HEADERS = [
        "Legal Company Name", "Trade Name/Brand Name", "Registered Office Address",
        "City", "State", "Pin Code", "GSTIN", "PAN",
        "Authorized Signatory Name", "Designation", "Mobile Number", "Email ID",
        "Partner Type", "Data 1", "Data 2", "Data 3",
    ]
    SAMPLE_ROW = [
        "Acme Insurance Pvt Ltd", "Acme Insurance", "123 MG Road, Andheri East",
        "Mumbai", "Maharashtra", "400069", "27AAPFU0939F1ZV", "AAPFU0939F",
        "Rahul Sharma", "Director", "9876543210", "rahul@acmecorp.com",
        "Broker", "", "", "",
    ]

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Partners"

    # Header row — bold, navy fill
    header_fill = PatternFill(start_color="0A2257", end_color="0A2257", fill_type="solid")
    for col_num, header in enumerate(HEADERS, start=1):
        cell = ws.cell(row=1, column=col_num, value=header)
        cell.font = Font(bold=True, color="FFFFFF")
        cell.fill = header_fill
        cell.alignment = Alignment(horizontal="center")
        ws.column_dimensions[cell.column_letter].width = max(len(header) + 4, 18)

    # Sample data row
    for col_num, value in enumerate(SAMPLE_ROW, start=1):
        ws.cell(row=2, column=col_num, value=value)

    buf = BytesIO()
    wb.save(buf)
    buf.seek(0)
    return StreamingResponse(
        buf,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=partner_upload_sample.xlsx"},
    )


@admin_partners_router.get("/{partner_id}", response_model=ResponseModel)
async def get_partner(partner_id: UUID, request: Request, _=Depends(_require_superadmin)):
    p = PartnerService().get_by_id(str(partner_id))
    user = UserQuery().get_user_by_id(str(p.user_id))
    return ResponseModel.ok(data=_partner_dict(p, user))


@admin_partners_router.patch("/{partner_id}", response_model=ResponseModel)
async def update_partner(partner_id: UUID, body: PartnerUpdate, request: Request,
                         _=Depends(_require_superadmin)):
    p = PartnerService().update(str(partner_id), body)
    user = UserQuery().get_user_by_id(str(p.user_id))
    return ResponseModel.ok(data=_partner_dict(p, user))


@admin_partners_router.delete("/{partner_id}", response_model=ResponseModel)
async def delete_partner(partner_id: UUID, request: Request, _=Depends(_require_superadmin)):
    PartnerService().delete(str(partner_id))
    return ResponseModel.ok(data={"message": "Partner deactivated"})


@admin_partners_router.post("/{partner_id}/regenerate-key", response_model=ResponseModel)
async def regen_key(partner_id: UUID, request: Request, _=Depends(_require_superadmin)):
    p = PartnerService().regenerate_api_key(str(partner_id))
    return ResponseModel.ok(data={"api_key": p.api_key})


@admin_partners_router.get("/{partner_id}/plans", response_model=ResponseModel)
async def partner_plans(partner_id: UUID, request: Request, _=Depends(_require_superadmin)):
    plans = PlanService().list_for_partner(str(partner_id))
    return ResponseModel.ok(data=[_plan_to_dict(p) for p in plans])


@admin_partners_router.post("/{partner_id}/members/list", response_model=ResponseModel)
async def list_partner_members(
    partner_id: UUID, body: MemberListRequest, request: Request, _=Depends(_require_superadmin)
):
    """Members enrolled under a specific partner, with their plan and policy count."""
    mq = MemberQuery()
    pq = PolicyQuery()
    from ...db.queries.plan_query import PlanQuery
    plan_q = PlanQuery()
    body.partner_id = str(partner_id)
    total, users = mq.list_members_paginated(body, partner_id=str(partner_id))
    result = []
    for u in users:
        enrollment = mq.get_enrollment(str(u.id), str(partner_id))
        plan_name = None
        if enrollment and enrollment.plan_id:
            plan = plan_q.get_by_id(str(enrollment.plan_id))
            plan_name = plan.name if plan else None
        policies = pq.list_by_user_partner(str(u.id), str(partner_id))
        family = mq.list_family(str(u.id))
        result.append({
            "id": str(u.id),
            "name": u.name,
            "email": u.email,
            "mobile_no": u.mobile_no,
            "is_active": u.is_active,
            "enrollment_status": enrollment.status if enrollment else None,
            "plan_id": str(enrollment.plan_id) if enrollment and enrollment.plan_id else None,
            "plan_name": plan_name,
            "policy_count": len(policies),
            "family_count": len(family),
        })
    return ResponseModel.ok(data={"data": result, "total": total, "skip": body.skip, "limit": body.limit})


@admin_partners_router.post("/{partner_id}/policies/list", response_model=ResponseModel)
async def list_partner_policies(
    partner_id: UUID, body: PolicyListRequest, request: Request, _=Depends(_require_superadmin)
):
    """Policies uploaded under a specific partner, with member info."""
    pq = PolicyQuery()
    uq = UserQuery()
    ptq = PolicyTypeQuery()
    body.partner_id = str(partner_id)
    total, policies = pq.list_paginated_all(body, partner_id=str(partner_id), user_id=body.user_id)
    user_cache: dict = {}
    pt_cache: dict = {}
    result = []
    for p in policies:
        uid = str(p.user_id)
        tid = str(p.policy_type_id)
        if uid not in user_cache:
            user_cache[uid] = uq.get_user_by_id(uid)
        if tid not in pt_cache:
            pt_cache[tid] = ptq.get_by_id(tid)
        u = user_cache[uid]
        pt = pt_cache[tid]
        result.append({
            "id": str(p.id),
            "policy_number": p.policy_number,
            "policy_type": pt.name if pt else None,
            "insurer": p.insurer,
            "sum_insured": p.sum_insured,
            "start_date": str(p.start_date) if p.start_date else None,
            "end_date": str(p.end_date) if p.end_date else None,
            "status": p.status,
            "file_name": p.file_name,
            "member_id": uid,
            "member_name": u.name if u else None,
            "member_email": u.email if u else None,
            "has_file": bool(p.storage_key),
            "created_at": p.created_at.isoformat() if p.created_at else None,
        })
    return ResponseModel.ok(data={"data": result, "total": total, "skip": body.skip, "limit": body.limit})
