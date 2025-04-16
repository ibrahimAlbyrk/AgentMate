import asyncio
import uvicorn

from fastapi import FastAPI
from contextlib import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware

from Core.EventBus import EventBus
from Core.logger import LoggerCreator
from Core.task_runner import TaskRunner
from Core.startup import start_all_user_agents, stop_all_user_agents

from Engines.task_queue_manager import queue_manager

from DB.Routers import user_settings, agent_status, webhook, auth_router, websocket_router
from DB.database import AsyncSessionLocal

from Subscribers.subscriber_manager import start_all_subscribers, stop_all_subscribers

logger = LoggerCreator.create_advanced_console("Main")
event_bus = EventBus()
task_runner = TaskRunner()


@asynccontextmanager
async def lifespan(app: FastAPI):
    await queue_manager.start()

    await start_all_subscribers()

    async with AsyncSessionLocal() as session:
        await start_all_user_agents(session)

    yield
    stop_all_subscribers()
    async with AsyncSessionLocal() as session:
        await stop_all_user_agents(session)

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
    user_settings.router,
    agent_status.router,
    auth_router.router,
    webhook.router,
    websocket_router.router,
])

if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=6000)
