import asyncio
import json

from pydantic import ValidationError

from DB.database import get_db
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from DB.Schemas.gmail_config import GmailConfig
from Engines.email_memory_summarizer_engine import EmailMemorySummarizerEngine
from Connectors.omi_connector import OmiConnector, MemoryData
from DB.Services.user_settings_service import UserSettingsService
from DB.Services.processed_gmail_service import ProcessedGmailService
from fastapi import APIRouter, Request, HTTPException, status, Depends

from Agents.Gmail.gmail_agent import GmailAgent
from Core.agent_manager import AgentManager

from Core.config import settings
from Core.EventBus import EventBus
from Core.Models.domain import Event, EventType

router = APIRouter(tags=["Unified Service Webhook"])

agent_manager = AgentManager()

memory_engine = EmailMemorySummarizerEngine()
omi = OmiConnector()

event_bus = EventBus()


@router.get("/{service}/get-settings")
async def get_settings(uid: str, service: str, session: AsyncSession = Depends(get_db)):
    if not uid:
        raise HTTPException(status_code=400, detail=f"UID not provided")

    config = await UserSettingsService.get_config(session, uid, service)
    default = settings.get_config(service)

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

    config_model = settings.get_config_model(service)
    if config_model:
        try:
            config_instance = config_model_cls(**config_data)
            config = config_instance.model_dump()
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


@router.get("/gmail/get-email-subjects")
async def get_email_subjects(uid: str, offset: int = 0, limit: int = 10):
    if not uid:
        raise HTTPException(status_code=400, detail=f"UID not provided")

    mail_count = offset + limit

    agent = agent_manager.get_agent(uid, "gmail", GmailAgent)
    emails = await agent.get_emails_subjects(mail_count)
    subjects: list[dict[str, str]] = []
    for email in emails:
        email_id = email.get("messageId")
        email_subject = email.get("subject")
        data = {"id": email_id, "subject": email_subject}
        subjects.append(data)

    return {"subjects": subjects[offset: mail_count]}


@router.post("/gmail/convert-to-memory")
async def convert_to_memories(uid: str, request: Request):
    if not uid:
        raise HTTPException(status_code=400, detail="Missing uid")

    data = await request.json()
    mode = data.get("mode", "count")
    agent = agent_manager.get_agent(uid, "gmail", GmailAgent)

    emails: list[dict] = []
    if mode == "count":
        count = int(data.get("count", 0))
        if not count:
            raise HTTPException(status_code=400, detail="Missing count")
        emails = await agent.get_emails(limit=count)


    elif mode == "selection":
        ids = data.get("selectedIds", [])
        if not ids:
            raise HTTPException(status_code=400, detail="No emails selected")
        agent = agent_manager.get_agent(uid, "gmail", GmailAgent)
        tasks = [agent.get_email_by_message_id(m_id) for m_id in ids]
        emails = await asyncio.gather(*tasks)

    else:
        raise HTTPException(status_code=400, detail="Invalid mode")

    await event_bus.publish_event(Event(
        type=EventType.GMAIL_SUMMARY,
        data={"uid": uid, "emails": emails}
    ))

    return {"status": "done", "memories": len(emails)}


@router.get("/setup-complete")
async def is_setup_completed(uid: str, session: AsyncSession = Depends(get_db)):
    if not uid:
        raise HTTPException(status_code=400, detail="Missing uid")

    has_user = await UserSettingsService.has_any(session, uid)
    return {"is_setup_completed": has_user}
