import json

from DB.database import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import APIRouter, HTTPException, Depends, Request

router = APIRouter(prefix="/composio", tags=["Composio"])


@router.post("/webhook")
async def webhook(request: Request, session: AsyncSession = Depends(get_db)):
    payload = await request.json()

    if not payload:
        return {"status": "error", "message": "There is no payload"}

    webhook_type = payload.get("type")
    connection_id = payload.get("data", {}).get("connection_id")

    print(f"webhook_type: {webhook_type}")
    print(f"connection_id: {connection_id}")

    return {"status": "success", "message": "Webhook received"}
