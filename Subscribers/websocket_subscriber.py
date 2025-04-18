import json

from Core.event_bus import EventBus
from Core.logger import LoggerCreator

from Routers.websocket_router import send_message_to_active_connection

from Subscribers.base_subscriber import BaseSubscriber

logger = LoggerCreator.create_advanced_console("WebSocketSubscriber")


class WebSocketSubscriber(BaseSubscriber):
    def __init__(self):
        self.event_bus = None

    async def setup(self, **services):
        self.event_bus = services['event_bus']

        self.event_bus.subscribe("websocket.gmail.memory", self._handle_memory_send)

    async def _handle_memory_send(self, raw_data: str):
        data = self._get_data(raw_data)
        if not data:
            return

        uid = data.get("uid", "")
        memories = data.get("memories", [])

        await send_message_to_active_connection(uid, message_type="gmail.memory", message={"memories": memories})

    @staticmethod
    def _get_data(raw_data: str) -> dict:
        try:
            payload = json.loads(raw_data)
            uid = payload["uid"]
            memories = payload["memories"]
            return {"uid": uid, "memories": memories}
        except Exception as e:
            logger.error(f"Error handling memory data: {str(e)}")
