import json
import asyncio

from abc import ABC, abstractmethod

from typing import Dict, Any, Optional, Callable

from Core.Models import Event, EventType
from Core.EventBus import EventBus
from Core.logger import LoggerCreator


class AgentEventHandler(ABC):
    def __init__(self, handler_name: str, uid: str, event_bus: Optional[EventBus] = None):
        self.handler_name = handler_name
        self.uid = uid
        self.event_bus = event_bus or EventBus()
        self.logger = LoggerCreator.create_advanced_console(f"{handler_name}EventHandler")

    @abstractmethod
    def get_event_handlers(self) -> Dict[str, Callable[[Dict[str, Any]], None]]:
        ...