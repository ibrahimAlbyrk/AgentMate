import json

from Core.EventBus import EventBus
from Core.logger import LoggerCreator
from Core.Models.domain import Event, EventType

from Routers.websocket_router import send_message_to_active_connection

from Subscribers.base_subscriber import BaseSubscriber
from Subscribers.subscriber_plugin import SubscriberPlugin, register_subscriber_plugin

logger = LoggerCreator.create_advanced_console("WebSocketSubscriber")


class WebSocketSubscriber(BaseSubscriber, SubscriberPlugin):
    subscriber_name = "websocket"
    priority = 80
    dependencies = ["event_bus"]
    enabled_by_default = True

    def __init__(self):
        self.event_bus = None

    async def setup(self, **services):
        self.event_bus = services['event_bus']

        await self.event_bus.subscribe(EventType.WEBSOCKET_GMAIL_MEMORY, self._handle_memory_send)

    async def _handle_memory_send(self, event: Event):
        data = event.data

        uid = data.get("uid", "")
        memories = data.get("memories", [])

        await send_message_to_active_connection(uid, message_type="gmail.memory", message={"memories": memories})

    @classmethod
    def create_subscriber(cls, **kwargs) -> BaseSubscriber:
        return cls()


register_subscriber_plugin("websocket", WebSocketSubscriber)
