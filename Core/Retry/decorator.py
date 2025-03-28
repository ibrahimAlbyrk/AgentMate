import asyncio
from functools import wraps
from Core.Retry.policy import RetryPolicy
from Core.Retry.manager import RetryManager

def retryable(max_retries=5,
              delay = 1,
              backoff = True,
              fallback=None,
              retry_exceptions=(Exception,)):

    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            policy = RetryPolicy(
                max_retries=max_retries,
                delay=delay,
                backoff=backoff,
                fallback=fallback
            )
            manager = RetryManager(policy, retry_exceptions)
            return await manager.execute(func, *args, **kwargs)

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            policy = RetryPolicy(
                max_retries=max_retries,
                delay=delay,
                backoff=backoff,
                fallback=fallback
            )
            manager = RetryManager(policy, retry_exceptions)
            return asyncio.run(manager.execute(func, *args, **kwargs))

        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper

    return decorator