"""
AI Engine for AgentMate

This module provides AI engines for various natural language processing tasks
such as classification, summarization, and generation.
"""

import json
import asyncio
import hashlib
from typing import Optional, Literal, TypeVar, Generic, Callable, List, Dict, Any, Awaitable, Union, Type
from dataclasses import dataclass

from openai import AsyncOpenAI
from openai.types.chat import ChatCompletion
from openai.types.chat.chat_completion import Choice
from openai.error import OpenAIError

from Core.config import settings
from Core.logger import LoggerCreator
from tiktoken import encoding_for_model

from Engines.task_queue_manager import queue_manager
from Core.Retry.decorator import retryable

T = TypeVar('T')


@dataclass
class AIRequest:
    """
    Represents a request to an AI model.

    This class encapsulates all the parameters needed for an AI request,
    such as messages, model, temperature, tools, etc.
    """
    messages: List[Dict[str, str]]
    model: str = "gpt-4.1-nano"
    temperature: float = 0.5
    tools: Optional[List[Dict[str, Any]]] = None
    tool_choice: Optional[Dict[str, Any]] = None
    estimated_response_tokens: int = 500


class BaseAIEngine:
    """
    Base class for AI engines.

    This class provides common functionality for AI engines, such as
    caching, token estimation, and request handling.
    """

    def __init__(self, name: str):
        """
        Initialize the AI engine.

        Args:
            name: The name of the engine
        """
        self.logger = LoggerCreator.create_advanced_console(name)
        self.client = AsyncOpenAI(api_key=settings.api.openai_api_key)
        self.cache = {}
        self.cache_lock = asyncio.Lock()
        self.name = name

    @staticmethod
    def _hash_prompt(messages: List[Dict[str, str]]) -> str:
        """
        Generate a hash for a prompt.

        Args:
            messages: The messages to hash

        Returns:
            A hash of the messages
        """
        prompt_str = json.dumps(messages, sort_keys=True)
        return hashlib.sha256(prompt_str.encode("utf-8")).hexdigest()

    @staticmethod
    def estimate_total_tokens(messages: List[Dict[str, str]], estimated_response_tokens: int) -> int:
        """
        Estimate the total number of tokens in a request.

        Args:
            messages: The messages in the request
            estimated_response_tokens: The estimated number of tokens in the response

        Returns:
            The estimated total number of tokens
        """
        try:
            enc = encoding_for_model("gpt-4.1-nano")
            prompt_text = json.dumps(messages, sort_keys=True)
            prompt_tokens = len(enc.encode(prompt_text))
            return prompt_tokens + estimated_response_tokens
        except Exception:
            return 1000 + estimated_response_tokens

    @retryable(max_retries=5, delay=2, backoff=True)
    async def run(self, request: AIRequest) -> str:
        """
        Run an AI request.

        Args:
            request: The AI request to run

        Returns:
            The result of the request
        """
        try:
            prompt_hash = self._hash_prompt(request.messages)

            # Check cache
            async with self.cache_lock:
                if prompt_hash in self.cache:
                    return self.cache[prompt_hash]

            # Prepare request parameters
            params = {
                "model": request.model,
                "messages": request.messages,
                "temperature": request.temperature,
            }
            if request.tools:
                params["tools"] = request.tools
            if request.tool_choice:
                params["tool_choice"] = request.tool_choice

            # Make API request
            try:
                response: ChatCompletion = await self.client.chat.completions.create(**params)
            except OpenAIError as e:
                if "rate_limit" in str(e).lower():
                    self.logger.warning("[429] Rate limit exceeded. Waiting before retrying...")
                    await asyncio.sleep(2)
                raise e

            # Extract result
            choice = response.choices[0].message
            result = choice.tool_calls[0].function.arguments if choice.tool_calls else (choice.content.strip() if choice.content else "")

            # Cache result
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
        """
        Process a batch of items using a queue.

        Args:
            uid: The user ID
            items: The items to process
            process_func: The function to process each item
            content_extractor: A function to extract content from each item for queue prioritization

        Returns:
            A list of results
        """
        results = [None] * len(items)

        # Create or get queue for this user
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

        # Wait for all tasks to complete
        while any(r is None for r in results):
            await asyncio.sleep(0.2)

        return results


class EmailClassifierEngine(BaseAIEngine):
    """
    Engine for classifying emails.

    This engine analyzes emails and classifies them based on importance,
    priority, sentiment, etc.
    """

    def __init__(self):
        """Initialize the email classifier engine."""
        super().__init__(name="EmailClassifier")

    async def classify(self,
                       email: Dict[str, Any],
                       important_categories: Optional[List[str]] = None,
                       ignored_categories: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Classify an email.

        Args:
            email: The email to classify
            important_categories: Categories that indicate important emails
            ignored_categories: Categories that indicate emails to ignore

        Returns:
            A dictionary with classification results
        """
        # Use empty lists if categories are None
        important_categories = important_categories or []
        ignored_categories = ignored_categories or []

        # Build tool and prompt
        tool = self._build_classify_tool(important_categories, ignored_categories)
        prompt = self._build_classification_prompt(email)

        # Create and run request
        request = AIRequest(
            messages=[{"role": "user", "content": prompt}],
            tools=[tool],
            tool_choice={"type": "function", "function": {"name": "classify_email"}}
        )

        try:
            result = await self.run(request)
            return json.loads(result)
        except Exception as e:
            self.logger.error(f"Classification error: {str(e)}")
            return {}

    async def classify_batch(self,
                             uid: str,
                             emails: List[Dict[str, Any]],
                             important_categories: Optional[List[str]] = None,
                             ignored_categories: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """
        Classify a batch of emails.

        Args:
            uid: The user ID
            emails: The emails to classify
            important_categories: Categories that indicate important emails
            ignored_categories: Categories that indicate emails to ignore

        Returns:
            A list of classification results
        """
        # Create a process function that captures the categories
        async def process_email(email: Dict[str, Any]) -> Dict[str, Any]:
            return await self.classify(email, important_categories, ignored_categories)

        # Use the common batch processing method
        return await self.process_batch(uid, emails, process_email)

    @staticmethod
    def _build_classification_prompt(email: Dict[str, Any]) -> str:
        """
        Build a prompt for email classification.

        Args:
            email: The email to classify

        Returns:
            A prompt string
        """
        subject = email.get("subject", "")
        sender = email.get("sender", "Unknown")
        email_body = email.get("body", "")

        return f"Title: {subject}\nFrom: {sender}\nContent: {email_body[:1000]}"

    @staticmethod
    def _build_classify_tool(important_categories: List[str], ignored_categories: List[str]) -> Dict[str, Any]:
        """
        Build a tool definition for email classification.

        Args:
            important_categories: Categories that indicate important emails
            ignored_categories: Categories that indicate emails to ignore

        Returns:
            A tool definition
        """
        return {
            "type": "function",
            "function": {
                "name": "classify_email",
                "description": (
                    f"""
                       You are an advanced email classifier. Analyze the given email thoroughly based on:

                       IMPORTANT CATEGORIES (exactly match the main purpose or intent): {', '.join(important_categories)}
                       IGNORED CATEGORIES (emails that are promotional, generic, or low priority): {', '.join(ignored_categories)}

                       If both important and ignored categories seem applicable, always prioritize IGNORED.
                       Return language using ISO 639-1 format
                       Determine priority and sender importance based on urgency, deadlines, or identity.
                       Make sure sentiment, tags, and suggested actions are accurate based on content.
                       """
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "answer": {"type": "boolean",
                                   "description": "Set true if email clearly matches an IMPORTANT CATEGORY; otherwise false"},

                        "important": {"type": ["string", "null"],
                                      "description": "Identify exactly one matched IMPORTANT CATEGORY or Null if none match clearly."},

                        "priority": {"type": ["string", "null"], "description": """Determine based on urgency, sender's importance, deadlines, and the potential impact:
                           "high": Immediate action required, urgent issues, critical deadlines, security alerts.
                           "medium": Moderate urgency, needs attention soon (e.g., meetings, project updates).
                           "low": Minor urgency, informational updates, invoices with distant due dates.
                           null: If no clear priority."""},

                        "sender_importance": {"type": "string", "description": """Based on sender identity and context:
                           "critical": Important clients, management, executives, known critical contacts.
                           "regular": Known contacts, standard business emails.
                           "unknown": Unrecognized or new sender."""},

                        "summary": {"type": "string",
                                    "description": "Provide a concise, single-sentence summary clearly capturing the core intent or action required."},

                        "sentiment": {"type": ["string", "null"], "description": """Analyze overall tone:
                           "positive": Clearly good news, approval, confirmations.
                           "neutral": Informational, factual, balanced.
                           "negative": Complaints, problems, urgent warnings or negative issues."""},

                        "has_attachment": {"type": "boolean",
                                           "description": "Set true if the email explicitly mentions or clearly indicates attachments; otherwise false."},

                        "has_links": {"type": "boolean",
                                      "description": "Set true if email clearly contains clickable URLs or mentions external links explicitly; otherwise false."},

                        "suggested_actions": {"type": "array", "items": {"type": "string"},
                                              "description": "Suggest relevant actions explicitly based on email content. Examples: [reply, schedule_meeting, pay_invoice, reset_password, review_document, follow_up, verify_account, check_security, track_shipping]"},

                        "tags": {"type": "array", "items": {"type": "string",
                                                            "description": "Include precise tags reflecting email context, content, industry, and keywords clearly relevant to help categorize effectively."}},

                        "reply_required": {"type": "boolean",
                                           "description": "Set true only if email explicitly requests a reply, confirmation, or clearly needs response; otherwise false."},

                        "language": {"type": "string",
                                     "description": "Use ISO 639-1 codes like 'tr' for Turkish, 'en' for English."},

                        "ignored": {"type": ["string", "null"],
                                    "description": "Clearly identify exactly one IGNORED CATEGORY if the email matches any. If it also matches an IMPORTANT CATEGORY, IGNORED takes precedence."}
                    },
                    "required": ["answer", "important", "priority", "sender_importance", "summary", "sentiment",
                                 "has_attachment", "has_links", "suggested_actions", "tags", "reply_required",
                                 "language", "ignored"]
                }
            }
        }


class EmailMemorySummarizerEngine(BaseAIEngine):
    """
    Engine for summarizing emails for memory purposes.

    This engine creates concise summaries of emails that can be used
    for building long-term memory about the user.
    """

    def __init__(self, character_limit: int = 200):
        """
        Initialize the email memory summarizer engine.

        Args:
            character_limit: The maximum number of characters in the summary
        """
        super().__init__(name="EmailMemorySummarizer")
        self.character_limit = character_limit

    async def summarize(self, email: Dict[str, Any]) -> str:
        """
        Summarize an email for memory purposes.

        Args:
            email: The email to summarize

        Returns:
            A summary of the email
        """
        subject = email.get("subject", "")
        email_body = email.get("body", "")

        if not subject or not email_body:
            return ""

        # Create prompts
        system_prompt = f"""
        You are building long-term memory about the user from emails.
        Focus on what the email reveals about their behavior, relationships, or decisions.
        Output one paragraph of max {self.character_limit} chars, deeply user-centric.
        Avoid summaries. Be concise and insightful.
        Always act like you're building an evolving, personal profile to better serve and understand the user over time.
        """

        user_prompt = f"""
        Title: {subject}
        Content: {email_body}
        """

        # Create and run request
        request = AIRequest(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.3
        )

        # Get and truncate result if necessary
        result = await self.run(request)
        if len(result) > self.character_limit:
            result = result[:self.character_limit] + "..."

        return result

    async def summarize_batch(self, uid: str, emails: List[Dict[str, Any]]) -> List[str]:
        """
        Summarize a batch of emails.

        Args:
            uid: The user ID
            emails: The emails to summarize

        Returns:
            A list of email summaries
        """
        # Use the common batch processing method
        return await self.process_batch(uid, emails, self.summarize)
