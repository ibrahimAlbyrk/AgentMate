from Core.EventBus.broker import BrokerFactory
from Core.EventBus.redis_broker import RedisBroker
BrokerFactory.register('redis', RedisBroker)

import uvicorn
import asyncio

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from contextlib import asynccontextmanager

from Core.logger import LoggerCreator
from Core.task_runner import TaskRunner
from Core.startup import start_all_user_agents, stop_all_user_agents

from DB.database import AsyncSessionLocal

from Engines.task_queue_manager import queue_manager

from Subscribers.subscriber_manager import start_all_subscribers, stop_all_subscribers

from Routers import user_settings_router, websocket_router, omi_router, auth_router, agent_status_router, gmail_router, settings_router

logger = LoggerCreator.create_advanced_console("Main")
task_runner = TaskRunner()

@asynccontextmanager
async def lifespan(app: FastAPI):
    await queue_manager.start()

    await start_all_subscribers()

    async with AsyncSessionLocal() as session:
        await start_all_user_agents(session)

    yield
    async with AsyncSessionLocal() as session:
        await stop_all_user_agents(session)

    await stop_all_subscribers()

    task_runner.executor.shutdown(wait=False)
    logger.info("Shutdown complete.")


app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _include_routers(routers: []):
    for router in routers:
        app.include_router(router)


_include_routers([
    user_settings_router.router,
    agent_status_router.router,
    auth_router.router,
    websocket_router.router,
    omi_router.router,
    settings_router.router,
    gmail_router.router
])

if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=5000)
