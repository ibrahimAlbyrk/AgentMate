from DB.database import get_db
from sqlalchemy.future import select
from Core.agent_factory import AgentFactory
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from DB.Models.user_settings import UserSettings

router = APIRouter(prefix="/agent", tags=["Agents"])

@router.get("/status")
async def get_active_agents(uid: str = Query(...), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(UserSettings.service_name).where(UserSettings.uid == uid))
    user_services = [row[0] for row in result.all()]
    all_known_services = AgentFactory.registry.keys()

    status_report = []
    for service in user_services:
        is_supported = service in all_known_services
        status_report.append({
            "service": service,
            "agent_available": is_supported
        })

    return {
        "uid": uid,
        "services": status_report,
    }
