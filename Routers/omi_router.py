from Core.logger import LoggerCreator

from sqlalchemy.ext.asyncio import AsyncSession

from DB.database import get_db
from DB.Services.user_settings_service import UserSettingsService

from fastapi import APIRouter, HTTPException, Depends

router = APIRouter(tags=["Omi"])

logger = LoggerCreator.create_advanced_console("OmiRouter")

@router.get("/setup-complete")
async def is_setup_completed(uid: str, session: AsyncSession = Depends(get_db)):
    if not uid:
        raise HTTPException(status_code=400, detail="Missing uid")

    has_user = await UserSettingsService.has_any(session, uid)
    return {"is_setup_completed": has_user}

@router.post("/transcript-processed")
async def transcript_processed(uid: str, transcript: dict, session: AsyncSession = Depends(get_db)):
    logger.debug(transcript)