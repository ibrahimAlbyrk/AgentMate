from fastapi import APIRouter, Depends

from sqlalchemy import select, func, distinct
from sqlalchemy.ext.asyncio import AsyncSession

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
