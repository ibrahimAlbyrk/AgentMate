import json

from pydantic import ValidationError

from DB.database import get_db
from fastapi.responses import JSONResponse
from Core.agent_manager import AgentManager
from sqlalchemy.ext.asyncio import AsyncSession
from DB.Schemas.gmail_config import GmailConfig
from Engines.ai_engine import EmailMemorySummarizerEngine
from Connectors.omi_connector import OmiConnector, MemoryData
from DB.Services.user_settings_service import UserSettingsService
from DB.Services.processed_gmail_service import ProcessedGmailService
from fastapi import APIRouter, Request, HTTPException, status, Depends

from Core.config import settings

from Subscribers.gmail_subscriber import event_bus

router = APIRouter(tags=["Unified Service Webhook"])

agent_manager = AgentManager()
memory_engine = EmailMemorySummarizerEngine()
omi = OmiConnector()


@router.get("/{service}/get-settings")
async def get_settings(service: str, session: AsyncSession = Depends(get_db)):
    uid = request.query_params.get("uid")
    if not uid:
        raise HTTPException(status_code=400, detail=f"UID not provided")

    config = await UserSettingsService.get_config(session, uid, service)
    default = settings.DEFAULT_CONFIGS.get(service, {})

    if not config:
        return default

    return {
        key: config.get(key, default.get(key))
        for key in default
    }


@router.post("/{service}/update-settings")
async def update_settings(service: str, request: Request, db: AsyncSession = Depends(get_db)):
    uid = request.query_params.get("uid")
    if not uid:
        raise HTTPException(status_code=400, detail=f"UID not provided")

    try:
        data = await request.json()
    except Exception:
        return {"error": "Invalid or empty JSON body."}

    config_data = data.get("config")

    config_model = settings.CONFIG_MODELS.get(service)
    if config_model:
        try:
            config = config_model(**config_data).model_dump()
        except ValidationError as e:
            raise HTTPException(status_code=400, detail=f"Invalid {service} config: {str(e)}")
    else:
        config = config_data

    await UserSettingsService.set_config(db, uid, service, config)
    await agent_manager.restart_agent(uid, service)

    return {"status": f"{service} agent restarted with new config"}


@router.get("/gmail/get-email-subjects")
async def get_email_subjects(offset: int = 0, limit: int = 10, session: AsyncSession = Depends(get_db)):
    uid = request.query_params.get("uid")
    if not uid:
        raise HTTPException(status_code=400, detail=f"UID not provided")

    user = await UserSettingsService.get_user(session, uid)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    config = user.get("config")
    service = GmailService(uid, config)
    subjects = await service.fetch_email_subjects_paginated(offset, limit)

    return {"subjects": subjects}


@router.post("/gmail/convert-to-memory")
async def convert_to_memories(request: Request, session: AsyncSession = Depends(get_db)):
    uid = request.query_params.get("uid")
    if not uid:
        raise HTTPException(status_code=400, detail="Missing uid")

    data = await request.json()
    mode = data.get("mode", "count")
    service = GmailService(uid)

    if mode == "count":
        count = int(data.get("count", 0))
        if not count:
            raise HTTPException(status_code=400, detail="Missing count")
        emails = await service.fetch_latest_emails(limit=count)

    elif mode == "selection":
        selected = data.get("selectedSubjects", [])
        if not selected:
            raise HTTPException(status_code=400, detail="No emails selected")
        ids = [item["id"] for item in selected]
        emails = await service.fetch_emails_by_ids(ids)

    else:
        raise HTTPException(status_code=400, detail="Invalid mode")

    event_bus.publish("gmail.inbox.summary", emails)

    return {"status": "done", "converted emails": len(emails)}


@router.get("/setup-complete")
async def is_setup_completed(session: AsyncSession = Depends(get_db)):
    uid = request.query_params.get("uid")
    if not uid:
        raise HTTPException(status_code=400, detail="Missing uid")

    has_user = await UserSettingsService.has_user(session, uid)
    return {"is_setup_completed": has_user}
