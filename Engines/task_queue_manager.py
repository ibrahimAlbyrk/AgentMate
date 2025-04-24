import time
import asyncio

from Engines.task_queue import TaskQueue
from Engines.concurrency_limiter import ConcurrencyLimiter
from Engines.global_token_orchestrator import GlobalTokenOrchestrator

from Core.logger import LoggerCreator

logger = LoggerCreator.create_advanced_console("TaskQueueManager")


class TaskQueueManager:
    def __init__(self, token_limit_per_minute: int = 90000, queue_idle_timeout: int = 600):
        self.queues: dict[str, dict] = {}  # user_id: {"queue": TaskQueue, "last_used": timestamp}
        self.token_limit_per_minute = token_limit_per_minute
        self.queue_idle_timeout = queue_idle_timeout
        self.orchestrator = GlobalTokenOrchestrator.get_instance()
        self._cleanup_started = False

    async def start(self):
        if not self._cleanup_started:
            self._cleanup_started = True
            asyncio.create_task(self._cleanup_loop())

    def get_or_create_queue(self, user_id: str, texts: list[str]) -> TaskQueue:
        now = time.time()
        if user_id in self.queues:
            self.queues[user_id]["last_used"] = now
            return self.queues[user_id]["queue"]

        limiter = ConcurrencyLimiter(self.token_limit_per_minute)
        max_concurrent = limiter.calculate_max_concurrent_tasks(texts)

        logger.debug(f"Created queue for {user_id} with max {max_concurrent} concurrency")

        queue = TaskQueue(max_concurrent_tasks=max_concurrent, orchestrator=self.orchestrator)
        self.queues[user_id] = {"queue": queue, "last_used": now}
        return queue

    async def _cleanup_loop(self):
        while True:
            now = time.time()
            to_remove = []
            for user_id, data in self.queues.items():
                if now - data["last_used"] > self.queue_idle_timeout:
                    to_remove.append(user_id)
            for user_id in to_remove:
                queue = self.queues.pop(user_id, None)
                if queue:
                    await queue.stop()
                logger.debug(f"Queue for {user_id} removed due to inactivity.")
            await asyncio.sleep(60)

queue_manager = TaskQueueManager(token_limit_per_minute=50000)