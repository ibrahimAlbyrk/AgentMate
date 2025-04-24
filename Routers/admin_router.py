from typing import Any, Dict

from fastapi import APIRouter, Depends

from sqlalchemy import select, func, distinct
from sqlalchemy.ext.asyncio import AsyncSession

from DB.Services.user_settings_service import UserSettingsService
from DB.database import get_db
from DB.Models.user_settings import UserSettings

router = APIRouter(prefix="/admin", tags=["Admin"])


@router.get("/user-count")
async def get_user_count(session: AsyncSession = Depends(get_db)):
    count = await _get_user_count(session)
    return {"user_count": count}

@router.get("/users-info")
async def get_users_info(session: AsyncSession = Depends(get_db)):
    users_data = await UserSettingsService.get_all_users(session)

    users: Dict[str, list[Dict[str, Any]]] = {}

    for user_data in users_data:
        uid = user_data.uid
        service_info = {
            "service": user_data.service_name,
            "is_logged_in": user_data.is_logged_in
        }

        if uid not in users:
            users[uid] = []

        users[uid].append(service_info)

    user_count = await _get_user_count(session)

    return {
        "count": user_count,
        "data": users
    }

async def _get_user_count(session: AsyncSession = Depends(get_db)):
    result = await session.execute(
        select(func.count(distinct(UserSettings.uid)))
    )
    return result.scalar()
