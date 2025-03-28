import json

from Core.event_bus import EventBus
from Core.logger import LoggerCreator

from DB.Routers.websocket_router import send_message_to_active_connection

from Subscribers.base_subscriber import BaseSubscriber

logger = LoggerCreator.create_advanced_console("WebSocketSubscriber")

event_bus = EventBus()


class WebSocketSubscriber(BaseSubscriber):
    async def register(self):
        self.event_bus.subscribe("websocket.gmail.memory", _handle_memory_send)


async def _handle_memory_send(raw_data: str):
    data = _get_data(raw_data)
    if not data:
        return

    uid = data.get("uid", "")
    memories = data.get("memories", [])

    await send_message_to_active_connection(uid, message_type="gmail.memory", message={"memories": memories})


def _get_data(raw_data: str) -> dict:
    try:
        payload = json.loads(raw_data)
        uid = payload["uid"]
        memories = payload["memories"]
        return {"uid": uid, "memories": memories}
    except Exception as e:
        logger.error(f"Error handling memory data: {str(e)}")
