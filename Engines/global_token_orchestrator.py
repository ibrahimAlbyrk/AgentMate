import uuid
import asyncio
from Engines.token_estimator import TokenEstimator

class GlobalTokenOrchestrator:
    _instance = None
    _lock = asyncio.Lock()

    def __init__(self, model: str = "gpt-4.1-nano", max_token_budget: int = 90000, task_timeout: int = 120):
        self.model = model
        self.max_token_budget = max_token_budget
        self.token_estimator = TokenEstimator(model)
        self.current_token_usage = 0
        self.lock = asyncio.Lock()
        self.task_timeout = task_timeout  # seconds
        self.active_tasks = {}  # task_id: (used_tokens, timeout_task)

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    async def register_task(self, content: str) -> str:
        estimated_tokens = self.token_estimator.count_tokens(content)
        task_id = str(uuid.uuid4())

        while True:
            async with self.lock:
                if self.current_token_usage + estimated_tokens <= self.max_token_budget:
                    self.current_token_usage += estimated_tokens
                    break
            await asyncio.sleep(0.5)

        timeout_task = asyncio.create_task(self._timeout_release(task_id, estimated_tokens))
        self.active_tasks[task_id] = (estimated_tokens, timeout_task)
        return task_id

    async def complete_task(self, task_id: str):
        async with self.lock:
            if task_id in self.active_tasks:
                used_tokens, timeout_task = self.active_tasks.pop(task_id)
                self.current_token_usage = max(0, self.current_token_usage - used_tokens)
                timeout_task.cancel()

    async def _timeout_release(self, task_id: str, used_tokens: int):
        try:
            await asyncio.sleep(self.task_timeout)
            async with self.lock:
                if task_id in self.active_tasks:
                    self.active_tasks.pop(task_id)
                    self.current_token_usage = max(0, self.current_token_usage - used_tokens)
                    print(f"[TokenOrchestrator] Task {task_id} timeout, tokens released automatically.")
        except asyncio.CancelledError:
            pass