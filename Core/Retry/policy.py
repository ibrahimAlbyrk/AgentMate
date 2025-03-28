from dataclasses import dataclass
from typing import Optional, Callable

@dataclass
class RetryPolicy:
    max_retries: int = 5
    delay: float = 1
    backoff: bool = True
    fallback: Optional[Callable] = None