import asyncio
import inspect
import traceback

from Core.logger import LoggerCreator
from Core.Retry.policy import RetryPolicy
from Core.Retry.exceptions import RetryException
from Core.logger import LoggerCreator
from typing import Callable, Any, Type, Tuple

logger = LoggerCreator.create_advanced_console("RetryManager")


class RetryManager:
    def __init__(self,
                 policy: RetryPolicy,
                 retry_exceptions: Tuple[Type[RetryException], ...] = (Exception,)):
        self.policy = policy
        self.retry_exceptions = retry_exceptions

    async def execute(self, func: Callable, *args, **kwargs) -> Any:
        attempt = 0
        delay = self.policy.delay
        last_exception = None

        while attempt < self.policy.max_retries:
            try:
                logger.debug(f"Attempt {attempt + 1} for {func.__name__}")
                if inspect.iscoroutinefunction(func):
                    return await func(*args, **kwargs)
                return func(*args, **kwargs)
            except self.retry_exceptions as e:
                last_exception = e
                logger.warning(f"[Retry {attempt + 1}]/{self.policy.max_retries} Exception in {func.__name__}: {str(e)}")
                traceback.print_exc()

                attempt += 1
                if attempt < self.policy.max_retries:
                    await asyncio.sleep(delay)
                    if self.policy.backoff:
                        delay *= 2
                else:
                    break

        logger.error(f"{func.__name__} failed after {self.policy.max_retries} attempts")

        if self.policy.fallback:
            logger.debug(f"Executing fallback for {func.__name__}")
            try:
                if inspect.iscoroutinefunction(self.policy.fallback):
                    return await self.policy.fallback(*args, **kwargs)
                return self.policy.fallback(*args, **kwargs)
            except Exception as fallback_err:
                # logger.error(f"Fallback failed for {func.__name__}: {str(fallback_err)}")
                pass

        raise RetryException(last_exception, attempt)