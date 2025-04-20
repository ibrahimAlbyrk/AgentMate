from DB.database import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from DB.Services.user_settings_service import UserSettingsService
from fastapi import APIRouter, HTTPException, Depends

router = APIRouter(tags=["Omi"])


@router.get("/setup-complete")
async def is_setup_completed(uid: str, session: AsyncSession = Depends(get_db)):
    if not uid:
        raise HTTPException(status_code=400, detail="Missing uid")

    has_user = await UserSettingsService.has_any(session, uid)
    return {"is_setup_completed": has_user}
