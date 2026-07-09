from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel
from typing import Optional
from ...schemas.base import ResponseModel
from ..deps import require_permission
from ...db.queries.system_setting_query import SystemSettingQuery

admin_settings_router = APIRouter()

KNOWN_SETTINGS = {
    "upload_reminder_delay_minutes": "How many minutes after enrollment to send the upload reminder WhatsApp (e.g. 1440 for 24 hours)",
    "upload_reminder_run_hour_ist": "Hour of day (0-23, IST) at which the daily upload reminder job runs (e.g. 9). Requires app restart to take effect.",
    "child_age_limit": "Maximum age (in years) allowed for a Child family member (e.g. 21)",
}


class SettingUpdate(BaseModel):
    value: str


@admin_settings_router.get("", response_model=ResponseModel)
async def list_settings(_=Depends(require_permission("settings", "view"))):
    sq = SystemSettingQuery()
    rows = sq.list_all()
    existing = {r.key: r for r in rows}

    result = []
    for key, description in KNOWN_SETTINGS.items():
        row = existing.get(key)
        result.append({
            "key": key,
            "value": row.value if row else None,
            "description": description,
            "updated_at": row.updated_at.isoformat() if row and row.updated_at else None,
        })
    return ResponseModel.ok(data=result)


@admin_settings_router.patch("/{key}", response_model=ResponseModel)
async def update_setting(key: str, body: SettingUpdate, _=Depends(require_permission("settings", "edit"))):
    if key not in KNOWN_SETTINGS:
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail=f"Unknown setting key: {key}")

    sq = SystemSettingQuery()
    row = sq.set(key, body.value.strip(), description=KNOWN_SETTINGS[key])
    return ResponseModel.ok(data={
        "key": row.key,
        "value": row.value,
        "updated_at": row.updated_at.isoformat() if row.updated_at else None,
    })
