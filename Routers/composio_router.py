import json
import asyncio

from DB.database import get_db
from DB.Models.user_settings import UserSettings
from DB.Services.user_settings_service import UserSettingsService

from Core.agent_manager import agent_manager
from Core.agent_factory import AgentFactory

from Agents.agent_interface import IAgent

from sqlalchemy.ext.asyncio import AsyncSession

from fastapi import APIRouter, HTTPException, Depends, Request

router = APIRouter(prefix="/composio", tags=["Composio"])


@router.post("/webhook")
async def webhook(request: Request, session: AsyncSession = Depends(get_db)):
    payload = await request.json()

    if not payload:
        return {"status": "error", "message": "There is no payload"}

    data = payload.get("data", {})
    listener_type = payload.get("type")

    connection_id = data.get("connection_id")

    user: UserSettings = await UserSettingsService.get_by_service_id(session, connection_id)
    if not user:
        return {"status": "error", "message": "User not found"}

    uid = user.uid
    agent_name = user.service_name

    agent_type = AgentFactory.registry.get(agent_name, None)
    if not agent_type:
        return {"status": "error", "message": "Agent not found"}

    agent: IAgent = agent_manager.get_agent(uid, agent_name, agent_type)
    if not agent:
        return {"status": "error", "message": "Agent not found"}

    listener: callable = agent.listeners.get(listener_type)
    if not listener:
        return {"status": "error", "message": "Listener not found"}

    if asyncio.iscoroutinefunction(listener):
        await listener(data)
    else:
        listener(data)

    return {"status": "success", "message": f"{listener_type} is triggered"}
