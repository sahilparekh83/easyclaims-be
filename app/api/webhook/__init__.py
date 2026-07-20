from fastapi import APIRouter
from .ticket import webhook_router
from .whatsapp import whatsapp_router
from .meta_whatsapp import meta_whatsapp_router

webhook_main_router = APIRouter()
webhook_main_router.include_router(webhook_router, prefix="/ticket", tags=["Webhook"])
webhook_main_router.include_router(whatsapp_router, prefix="/whatsapp", tags=["Webhook"])
webhook_main_router.include_router(meta_whatsapp_router, prefix="/whatsapp/meta", tags=["Webhook"])
