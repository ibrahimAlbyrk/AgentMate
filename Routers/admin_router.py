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
    result = await session.execute(
        select(func.count(distinct(UserSettings.uid)))
    )
    count = result.scalar()
    return {"user_count": count}

@router.get("/users-info")
async def get_users_info(session: AsyncSession = Depends(get_db)):
    users_data = await UserSettingsService.get_all_users(session)

    users: Dict[str, Dict[str, Any]] = {}

    for user_data in users_data:
        if user_data.uid in users.keys():
            users[user_data.uid] = {"service": user_data.service_name, "is logged in": user_data.is_logged_in}

    return {"users": users}
