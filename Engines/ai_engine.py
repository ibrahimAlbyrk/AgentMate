import json
import asyncio
import hashlib
from dataclasses import dataclass
from typing import Optional, TypeVar, Callable, List, Dict, Any, Awaitable, Type

from openai import AsyncOpenAI
from openai import OpenAIError
from openai.types.chat import ChatCompletion
from openai.types.chat.chat_completion import Choice

from Core.config import settings
from Core.logger import LoggerCreator
from Core.Retry.decorator import retryable

from tiktoken import encoding_for_model

from Engines.task_queue_manager import queue_manager

T = TypeVar('T')


@dataclass
class AIRequest:
    """
    This class encapsulates all the parameters needed for an AI request,
    such as messages, model, temperature, tools, etc.
    """
    messages: List[Dict[str, str]]
    model: str = "gpt-4.1-mini"
    temperature: float = 0.5
    tools: Optional[List[Dict[str, Any]]] = None
    tool_choice: Optional[Dict[str, Any]] = None
    estimated_response_tokens: int = 500


class BaseAIEngine:
    """
    This class provides common functionality for AI engines, such as
    caching, token estimation, and request handling.
    """

    def __init__(self, name: str):
        self.logger = LoggerCreator.create_advanced_console(name)
        self.client = AsyncOpenAI(api_key=settings.api.openai_api_key)
        self.cache = {}
        self.cache_lock = asyncio.Lock()
        self.name = name

    @staticmethod
    def _hash_prompt(messages: List[Dict[str, str]]) -> str:
        prompt_str = json.dumps(messages, sort_keys=True)
        return hashlib.sha256(prompt_str.encode("utf-8")).hexdigest()

    @staticmethod
    def estimate_total_tokens(messages: List[Dict[str, str]], estimated_response_tokens: int) -> int:
        try:
            enc = encoding_for_model(settings.gpt_model)
            prompt_text = json.dumps(messages, sort_keys=True)
            prompt_tokens = len(enc.encode(prompt_text))
            return prompt_tokens + estimated_response_tokens
        except Exception:
            return 1000 + estimated_response_tokens

    @retryable(max_retries=5, delay=2, backoff=True)
    async def run(self, request: AIRequest) -> str:
        try:
            prompt_hash = self._hash_prompt(request.messages)

            async with self.cache_lock:
                if prompt_hash in self.cache:
                    return self.cache[prompt_hash]

            params = {
                "model": request.model,
                "messages": request.messages,
                "temperature": request.temperature,
            }
            if request.tools:
                params["tools"] = request.tools
            if request.tool_choice:
                params["tool_choice"] = request.tool_choice

            try:
                response: ChatCompletion = await self.client.chat.completions.create(**params)
            except OpenAIError as e:
                if "rate_limit" in str(e).lower():
                    self.logger.warning("[429] Rate limit exceeded. Waiting before retrying...")
                    await asyncio.sleep(2)
                raise e

            choice = response.choices[0].message
            result = choice.tool_calls[0].function.arguments if choice.tool_calls else (
                choice.content.strip() if choice.content else "")

            async with self.cache_lock:
                self.cache[prompt_hash] = result

            return result

        except Exception as e:
            self.logger.error(f"AI run error: {str(e)}")
            return ""

    async def process_batch(self,
                            uid: str,
                            items: List[Any],
                            process_func: Callable[[Any], Awaitable[T]],
                            content_extractor: Callable[[Any], str] = lambda x: x.get("body", "")) -> List[T]:
        results = [None] * len(items)

        queue = queue_manager.get_or_create_queue(
            user_id=uid,
            texts=[content_extractor(item) for item in items]
        )

        # Enqueue tasks
        for index, item in enumerate(items):
            async def task(i=index, item=item):
                result = await process_func(item)
                results[i] = result

            content = content_extractor(item)
            await queue.enqueue(task, content=content)

        while any(r is None for r in results):
            await asyncio.sleep(0.2)

        return results
