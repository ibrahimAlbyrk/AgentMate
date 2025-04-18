import json
import asyncio
import hashlib
from openai import AsyncOpenAI
from Core.config import settings
from typing import Optional, Literal
from Core.logger import LoggerCreator
from tiktoken import encoding_for_model
from Core.task_runner import TaskRunner

from Engines.task_queue_manager import queue_manager

from Core.Retry.decorator import retryable


class AIRequest:
    def __init__(self, *,
                 messages: list[dict],
                 model: Optional[str] = "gpt-4.1-nano",
                 temperature: Optional[float] = 0.5,
                 tools: Optional[list[dict]] = None,
                 tool_choice: Optional[dict] = None,
                 estimated_response_tokens: Optional[int] = 500):
        self.model = model
        self.messages = messages
        self.temperature = temperature
        self.tools = tools
        self.tool_choice = tool_choice
        self.estimated_response_tokens = estimated_response_tokens


class BaseAIEngine:
    def __init__(self, name: str):
        self.logger = LoggerCreator.create_advanced_console(name)
        self.client = AsyncOpenAI(api_key=settings.api.openai_api_key)
        self.cache = {}
        self.cache_lock = asyncio.Lock()

    @staticmethod
    def _has_prompt(messages: list[dict]) -> str:
        prompt_str = json.dumps(messages, sort_keys=True)
        return hashlib.sha256(prompt_str.encode("utf-8")).hexdigest()

    @staticmethod
    def estimate_total_tokens(messages: list[dict], estimated_response_tokens: int) -> int:
        try:
            enc = encoding_for_model("gpt-4.1-nano")
            prompt_text = json.dumps(messages, sort_keys=True)
            prompt_tokens = len(enc.encode(prompt_text))
            return prompt_tokens + estimated_response_tokens
        except Exception:
            return 1000 + estimated_response_tokens

    @retryable(max_retries=5, delay=2, backoff=True)
    async def run(self, request: AIRequest) -> str:
        try:
            prompt_hash = self._has_prompt(request.messages)

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
            result = choice.tool_calls[0].function.arguments if choice.tool_calls else (choice.content.strip() if choice.content else "")

            async with self.cache_lock:
                self.cache[prompt_hash] = result

            return result

        except Exception as e:
            self.logger.error(f"AI run error: {str(e)}")
            return ""


class BaseEmailEngine(BaseAIEngine):
    def __init__(self, name: str):
        super().__init__(name)


class EmailClassifierEngine(BaseEmailEngine):
    def __init__(self):
        super().__init__(name="EmailClassifier")

    async def classify(self,
                       email: dict,
                       important_categories: Optional[list[str]],
                       ignored_categories: Optional[list[str]]) -> dict:
        tool = self._build_classify_tool(important_categories, ignored_categories)

        prompt = self._build_classification_prompt(email)

        request = AIRequest(
            messages=[{"role": "user", "content": prompt}],
            tools=[tool],
            tool_choice={"type": "function", "function": {"name": "classify_email"}}
        )

        try:
            result = await self.run(request)
            return json.loads(result)
        except Exception as e:
            self.logger.error(f"Taxonomy JSON conversion error: {str(e)}")
            return {}

    async def classify_batch(self,
                             uid: str,
                             emails: list[dict],
                             important_categories: Optional[list[str]] = None,
                             ignored_categories: Optional[list[str]] = None) -> list[dict]:

        results = [None] * len(emails)
        queue = queue_manager.get_or_create_queue(
            user_id=uid,
            texts=[e["body"] for e in emails]
        )

        for index, email in enumerate(emails):
            async def task(i=index, e=email):
                result = await self.classify(e, important_categories, ignored_categories)
                results[i] = result

            email_body = email["body"]

            await queue.enqueue(task, content=email_body)

        while any(r is None for r in results):
            await asyncio.sleep(0.2)

        return results

    @staticmethod
    def _build_classification_prompt(email: dict) -> str:
        subject = email.get("subject", "")
        sender = email.get("sender", "Unknown")

        email_body = email["body"]

        return f"Title: {subject}\nFrom: {sender}\nContent: {email_body[:1000]}"

    @staticmethod
    def _build_classify_tool(important_categories: list[str], ignored_categories: list[str]) -> dict:
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


class EmailMemorySummarizerEngine(BaseEmailEngine):
    def __init__(self, character_limit: Optional[int] = 200):
        super().__init__(name="EmailMemorySummarizer")
        self.character_limit = character_limit

    async def summarize(self, email: dict) -> str:
        subject = email.get("subject", None)
        email_body = email["body"]
        content = email_body
        if not subject or not content:
            return ""

        system_prompt = f"""
        You are building long-term memory about the user from emails.
        Focus on what the email reveals about their behavior, relationships, or decisions.
        Output one paragraph of max {self.character_limit} chars, deeply user-centric.
        Avoid summaries. Be concise and insightful.
        Always act like you're building an evolving, personal profile to better serve and understand the user over time.
        """

        user_prompt = f"""
        Title: {subject}
        Content: {content}
        """

        request = AIRequest(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.3
        )

        result = await self.run(request)
        if len(result) > self.character_limit:
            result = result[:self.character_limit] + "..."
        return result

    async def summarize_batch(self, uid: str, emails: list[dict]) -> list[str]:
        results = [None] * len(emails)

        queue = queue_manager.get_or_create_queue(
            user_id=uid,
            texts=[e["body"] for e in emails]
        )

        for index, email in enumerate(emails):
            async def task(i=index, e=email):
                result = await self.summarize(e)
                results[i] = result

            email_body = email["body"]

            await queue.enqueue(task, content=email_body)

        while any(r is None for r in results):
            await asyncio.sleep(0.2)

        return results
