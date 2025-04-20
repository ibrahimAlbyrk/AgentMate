import asyncio
import json

from pydantic import ValidationError

from DB.database import get_db
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from Core.config import GmailConfig
from Engines.email_memory_summarizer_engine import EmailMemorySummarizerEngine
from Connectors.omi_connector import OmiConnector, MemoryData
from DB.Services.user_settings_service import UserSettingsService
from DB.Services.processed_gmail_service import ProcessedGmailService
from fastapi import APIRouter, Request, HTTPException, status, Depends

from Agents.Gmail.gmail_agent import GmailAgent
from Core.agent_manager import agent_manager

from Core.config import settings
from Core.EventBus import EventBus
from Core.Models.domain import Event, EventType

router = APIRouter(tags=["Unified Settings"])

memory_engine = EmailMemorySummarizerEngine()
omi = OmiConnector()

event_bus = EventBus()


@router.get("/{service}/get-settings")
async def get_settings(uid: str, service: str, session: AsyncSession = Depends(get_db)):
    if not uid:
        raise HTTPException(status_code=400, detail=f"UID not provided")

    config = await UserSettingsService.get_config(session, uid, service)
    default = settings.get_service_config(service)

    if not config:
        return default

    return {
        key: config.get(key, default.get(key))
        for key in default
    }


@router.post("/{service}/update-settings")
async def update_settings(uid: str, service: str, request: Request, db: AsyncSession = Depends(get_db)):
    if not uid:
        raise HTTPException(status_code=400, detail=f"UID not provided")

    try:
        data = await request.json()
    except Exception:
        return {"error": "Invalid or empty JSON body."}

    config_data = data.get("settings")

    config_model = settings.get_service_config_model(service)
    if config_model:
        try:
            config = config_model(**config_data).model_dump()
        except ValidationError as e:
            raise HTTPException(status_code=400, detail=f"Invalid {service} config: {str(e)}")
    else:
        config = config_data

    user_settings = await UserSettingsService.get(db, uid, service)
    service_id = user_settings.service_id

    await UserSettingsService.set_config(db, uid, service_id, service, config)

    await event_bus.publish_event(Event(
        type=EventType.RESTART_AGENT,
        data={"uid": uid, "service": service}
    ))

    return {
        "success": True,
        "status": f"{service} agent restarted with new config"
    }
