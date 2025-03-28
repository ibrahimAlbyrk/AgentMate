import asyncio
import uvicorn

from fastapi import FastAPI
from contextlib import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware

from Core.event_bus import EventBus
from Core.logger import LoggerCreator
from Core.task_runner import TaskRunner
from Core.startup import start_all_user_agents

from DB.Routers import user_settings, agent_status, webhook, auth_router
from DB.database import AsyncSessionLocal

from Subscribers.subscriber_manager import start_all_subscribers, stop_all_subscribers

logger = LoggerCreator.create_advanced_console("Main")
event_bus = EventBus()
task_runner = TaskRunner()


@asynccontextmanager
async def lifespan(app: FastAPI):
    await start_all_subscribers()

    async with AsyncSessionLocal() as session:
        await start_all_user_agents(session)

    yield
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

app.include_router(user_settings.router)
app.include_router(agent_status.router)
app.include_router(auth_router.router)
app.include_router(webhook.router)

if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=6000, proxy_headers=True)
