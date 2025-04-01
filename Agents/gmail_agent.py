import asyncio
import json
from typing import Optional

from Core.event_bus import EventBus
from Core.logger import LoggerCreator
from Gmail.gmail_service import GmailService
from DB.database import AsyncSessionLocal
from Interfaces.agent_interface import IAgent, agent_listener
from DB.Services.user_settings_service import UserSettingsService
from Connectors.omi_connector import OmiConnector, ConversationData
from DB.Services.processed_gmail_service import ProcessedGmailService

from composio_openai import App

from DB.Services.user_settings_service import UserSettingsService


class GmailAgent(IAgent):
    def __init__(self, uid: str, service_id):
        super().__init__(uid, service_id)
        self.app_name = App.GMAIL

    async def _run_impl(self):
        self.add_listener("GMAIL_NEW_GMAIL_MESSAGE", self._handle_new_email_messages)

    async def _stop_impl(self):
        pass

    def _handle_new_email_messages(self, event):
        print(event)

# class GmailAgent(IAgent):
#     def __init__(self, uid: str):
#         super().__init__(uid)
#         self.logger = LoggerCreator.create_advanced_console("GmailAgent")
#         self.active_tasks = {}  # {uid: asyncio.task}
#         self.stop_flags = {}  # {uid: asyncio.event}
#         self.event_bus = EventBus()
#
#     async def run(self, uid: str):
#         if uid in self.active_tasks:
#             self.logger.warning(f"GmailAgent already running for {uid}")
#             return
#
#         await self.event_bus.connect()
#
#         stop_event = asyncio.Event()
#         self.stop_flags[uid] = stop_event
#
#         task = asyncio.create_task(self._mail_loop(uid, stop_event))
#         self.active_tasks[uid] = task
#
#     async def stop(self, uid: str):
#         if uid in self.stop_flags:
#             self.stop_flags[uid].set()
#             self.logger.debug(f"Stop signal sent to GmailAgent for {uid}")
#
#         if uid in self.active_tasks:
#             await self.active_tasks[uid]
#             del self.active_tasks[uid]
#             del self.stop_flags[uid]
#             self.logger.debug(f"GmailAgent fully stopped for {uid}")
#
#     async def _mail_loop(self, uid: str, stop_event: asyncio.Event):
#         self.logger.debug(f"GmailAgent loop started for {uid}")
#
#         while not stop_event.is_set():
#             try:
#                 async with AsyncSessionLocal() as session:
#                     config = await UserSettingsService.get_config(session, uid, "gmail")
#                     if not config:
#                         self.logger.warning(f"No config found for GmailAgent uid: {uid}")
#                         break
#                     interval = config.get("mail_check_interval", 60)
#                     mail_count = config.get("mail_count", 3)
#
#                     service = GmailService(uid)
#                     emails = await service.fetch_latest_emails(limit=mail_count)
#
#                     new_emails = []
#
#                     for email in emails:
#                         gmail_id = email.get("id")
#                         if await ProcessedGmailService.has(session, uid, gmail_id):
#                             continue
#
#                         new_emails.append(email)
#
#                     event_data = {
#                         "uid": uid,
#                         "emails": new_emails,
#                     }
#                     await self.event_bus.publish("gmail.inbox.classify", json.dumps(event_data))
#
#                 await asyncio.sleep(interval)
#             except Exception as e:
#                 self.logger.error(f"GmailAgent loop error for {uid}: {str(e)}")
#                 await asyncio.sleep(2)
