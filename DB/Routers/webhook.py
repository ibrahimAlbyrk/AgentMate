from DB.database import get_db
from DB.Schemas.gmail_config import GmailConfig
from fastapi import APIRouter, Request, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from Core.agent_starter import agent_manager, start_user_agents
from DB.Services.user_settings_service import UserSettingsService

router = APIRouter(prefix="/webhook", tags=["Webhook Events"])

@router.post("/update-settings")
async def update_settings(request: Request, db: AsyncSession = Depends(get_db)):
    try:
        data = await request.json()
    except Exception:
        return {"error": "Invalid or empty JSON body."}

    uid = data.get("uid")
    service = data.get("service")
    config = data.get("config")

    if not all([uid, service, config]):
        return {"error", "UID, service and config are required"}

    if service == "gmail":
        try:
            GmailConfig(**config)
        except Exception as e:
            return {"error": f"Invalid Gmail config: {str(e)}"}

    await UserSettingsService.set_config(db, uid, service, config)
    await agent_manager.restart_agent(uid, service)

    return {"status": f"{service} agent restarted with new config"}

@router.post("/logged-in")
async def logged_in(request: Request, db: AsyncSession = Depends(get_db)):
    try:
        data = await request.json()
    except Exception:
        return {"error": "Invalid or empty JSON body."}

    uid = data.get("uid")

    if not uid:
        return {"error", "UID required"}

    has_any_services = await UserSettingsService.has_any(db, uid)

    if not has_any_services:
        return {"error", "Could not connect to any service yet"}

    await start_user_agents(uid, db)
    return {"status": "user agents started"}

@router.post("/connect-service")
async def connect_service(request: Request, db: AsyncSession = Depends(get_db)):
    try:
        data = await request.json()
    except Exception:
        return {"error": "Invalid or empty JSON body."}

    uid = data.get("uid")
    service = data.get("service")
    config = data.get("config")

    if not all([uid, service, config]):
        return {"error": "UID, service and config are required"}

    await UserSettingsService.set_config(db, uid, service, config)
    await agent_manager.start_agent(uid, service)

    return {"status": f"{service} agent started"}