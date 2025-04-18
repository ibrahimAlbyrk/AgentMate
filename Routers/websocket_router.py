from Core.logger import LoggerCreator
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

logger = LoggerCreator.create_advanced_console("WebSocketRouter")
router = APIRouter(tags=["WebSocket"])

active_connections: dict[str, WebSocket] = {}

async def send_message_to_active_connection(uid: str, message_type: str, message: dict):
    if not uid in active_connections:
        return

    await active_connections[uid].send_json({
        "type": message_type,
        "message": message
    })

@router.websocket("/ws/{uid}")
async def websocket_endpoint(websocket: WebSocket, uid: str):
    await websocket.accept()
    active_connections[uid] = websocket
    logger.debug(f"Websocket connected: {uid}")

    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        logger.debug(f"Websocket disconnected: {uid}")
        active_connections.pop(uid, None)
