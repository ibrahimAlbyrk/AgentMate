import asyncio
from Core.config import settings
from concurrent.futures import ThreadPoolExecutor

class TaskRunner:
    def __init__(self):
        max_workers = settings.async_settings.max_workers
        self.executor = ThreadPoolExecutor(max_workers)

    @staticmethod
    async def run_async_tasks(tasks):
        return await asyncio.gather(*tasks)

    async def run_in_thread(self, func, *args):
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(self.executor, func, *args)