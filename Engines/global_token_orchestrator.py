import asyncio
from Engines.token_estimator import TokenEstimator

class GlobalTokenOrchestrator:
    _instance = None
    _lock = asyncio.Lock()

    def __init__(self, model: str = "gpt-4.1-nano", max_token_budget: int = 90000):
        self.model = model
        self.max_token_budget = max_token_budget
        self.token_estimator = TokenEstimator(model)
        self.current_token_usage = 0
        self.lock = asyncio.Lock()

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    async def register_task(self, content: str) -> None:
        estimated_tokens = self.token_estimator.count_tokens(content)

        while True:
            async with self.lock:
                if self.current_token_usage + estimated_tokens <= self.max_token_budget:
                    self.current_token_usage += estimated_tokens
                    break
            await asyncio.sleep(0.5)

        return estimated_tokens

    async def complete_task(self, used_tokens: int):
        async with self.lock:
            self.current_token_usage = max(0, self.current_token_usage - used_tokens)