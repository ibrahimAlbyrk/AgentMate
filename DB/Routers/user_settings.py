from DB.database import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import APIRouter, Depends, HTTPException
from DB.Repositories.user_settings import UserSettingsRepository
from DB.Schemas.user_settings import UserSettingsCreate, UserSettingsOut

router = APIRouter(prefix="/settings", tags=["User Settings"])

@router.post("/", response_model=UserSettingsOut)
async def create_or_update_settings(
    payload: UserSettingsCreate,
    db: AsyncSession = Depends(get_db)
):
    return await UserSettingsRepository.create_or_update(db, payload)

@router.get("/{uid}/{service_name}", response_model=UserSettingsOut)
async def get_settings(
    uid: str,
    service_name: str,
    db: AsyncSession = Depends(get_db)
):
    settings = await UserSettingsRepository.get_by_uid_and_service(db, uid, service_name)
    if not settings:
        raise HTTPException(status_code=404, detail="Settings not found.")
    return settings