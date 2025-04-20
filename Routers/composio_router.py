from DB.database import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import APIRouter, HTTPException, Depends, Request

router = APIRouter(prefix="/composio", tags=["Composio"])


@router.get("/webhook")
async def webhook(request: Request, session: AsyncSession = Depends(get_db)):
    payload = await request.json()

    print("Received webhook payload:")
    print(json.dumps(payload, indent=2))

    return {"status": "success", "message": "Webhook received"}
