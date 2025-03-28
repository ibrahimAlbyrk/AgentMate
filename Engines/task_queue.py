import asyncio
from typing import Callable, Awaitable, Any
from Engines.global_token_orchestrator import GlobalTokenOrchestrator

from Core.logger import LoggerCreator

logger = LoggerCreator.create_advanced_console("TaskQueue")

class TaskQueue:
    def __init__(self, max_concurrent_tasks: int = 5, orchestrator: GlobalTokenOrchestrator = None):
        self.queue = asyncio.Queue()
        self.semaphore = asyncio.Semaphore(max_concurrent_tasks)
        self.max_concurrent = max_concurrent_tasks
        self.running = False
        self.orchestrator = orchestrator

    def update_concurrency(self, new_limit: int):
        diff = new_limit - self.max_concurrent
        self.max_concurrent = new_limit
        if diff > 0:
            for _ in range(diff):
                self.semaphore.release()
        elif diff < 0:
            self.semaphore = asyncio.Semaphore(new_limit)

    async def enqueue(self, task_func: Callable[[], Awaitable[Any]], content: str = ""):
        await self.queue.put((task_func(), content))
        if not self.running:
            asyncio.create_task(self._start())

    async def _start(self):
        self.running = True
        while not self.queue.empty():
            task_func, content = await self.queue.get()
            await self.semaphore.acquire()
            asyncio.create_task(self._run_task(task_func, content))
        self.running = False

    async def _run_task(self, task_func: Callable[[], Awaitable[Any]], content: str):
        used_tokens = 0
        try:
            if self.orchestrator:
                used_tokens = await self.orchestrator.register_task(content)

            await task_func()
        except Exception as e:
            logger.error(f"Task Failed: {str(e)}")
        finally:
            if self.orchestrator:
                await self.orchestrator.complete_task(used_tokens)
            self.semaphore.release()
