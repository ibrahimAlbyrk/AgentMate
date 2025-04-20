from Core.logger import LoggerCreator
from Core.Models.domain import Event, EventType

from Routers.websocket_router import send_message_to_active_connection

from Plugins.plugin_interface import IPlugin
from Plugins.subscriber_plugin import SubscriberPlugin

logger = LoggerCreator.create_advanced_console("WebSocketSubscriber")


class WebSocketSubscriber(SubscriberPlugin):
    subscriber_name = "websocket"
    priority = 80
    dependencies = ["event_bus"]
    enabled_by_default = True

    def __init__(self):
        self.event_bus = None

    @classmethod
    async def create(cls, **kwargs) -> IPlugin:
        instance = cls()

        instance.event_bus = kwargs['event_bus']

        await instance.event_bus.subscribe(EventType.WEBSOCKET_GMAIL_MEMORY, instance._handle_memory_send)

        return instance


    async def _handle_memory_send(self, event: Event):
        data = event.data

        uid = data.get("uid", "")
        memories = data.get("memories", [])

        await send_message_to_active_connection(uid, message_type="gmail.memory", message={"memories": memories})
