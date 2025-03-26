import json
from openai import AsyncOpenAI
from Core.config import settings
from typing import Optional, Literal
from Core.logger import LoggerCreator
from Core.task_runner import TaskRunner


class AIRequest:
    def __init__(self, *,
                 messages: list[dict],
                 model: Optional[str] = "gpt-4o-mini",
                 temperature: Optional[float] = 0.5,
                 tools: Optional[list[dict]] = None,
                 tool_choice: Optional[dict] = None):
        self.model = model
        self.messages = messages
        self.temperature = temperature
        self.tools = tools
        self.tool_choice = tool_choice


class BaseAIEngine:
    def __init__(self, name: str):
        self.logger = LoggerCreator.create_advanced_console(name)
        self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

    async def run(self, request: AIRequest) -> str:
        try:
            params = {
                "model": request.model,
                "messages": request.messages,
                "temperature": request.temperature,
            }
            if request.tools:
                params["tools"] = request.tools
            if request.tool_choice:
                params["tool_choice"] = request.tool_choice

            response: ChatCompletion = await self.client.chat.completions.create(**params)
            choice = response.choices[0].message

            if choice.tool_calls:
                return choice.tool_calls[0].function.arguments
            return choice.content.strip if choice.content else ""
        except Exception as e:
            self.logger.error(f"AI run error: {str(e)}")
            return ""


class EmailClassifierEngine(BaseAIEngine):
    def __init__(self):
        super().__init__(name="EmailClassifier")
        self.task_runner = TaskRunner()

    async def classify(self,
                       email: dict,
                       important_categories: Optional[list[str]] = None,
                       ignored_categories: Optional[list[str]] = None) -> dict:
        important_categories = important_categories or self.default_important
        ignored_categories = ignored_categories or self.default_ignored
        tool = self._build_classify_tool(important_categories, ignored_categories)

        subject = email.get("subject", "")
        sender = email.get("from", "")
        content = email.get("body", "")
        prompt = f"Title: {subject}\nFrom: {sender}\nContent: {content[:1000]}"

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
                             emails: list[dict],
                             important_categories: Optional[list[str]] = None,
                             ignored_categories: Optional[list[str]] = None) -> list[dict]:
        return await self.task_runner.run_async_tasks([
            self.classify(email, important_categories=important_categories, ignored_categories=ignored_categories)
            for email in emails
        ])

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

                       IMPORTANT CATEGORIES: {important_categories}
                       IGNORED CATEGORIES: {ignored_categories}
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
    def __init__(self, character_limit: Optional[int] = 300):
        super().__init__(name="EmailMemorySummarizer")
        self.task_runner = TaskRunner()
        self.character_limit = character_limit

    async def summarize(self, email: dict) -> str:
        subject = email.get("subject", None)
        content = email.get("body", None)
        if not subject or not content:
            return ""

        system_prompt = f"""
        You are an intelligent assistant that builds long-term memory about the user based on the emails they receive or send.
        Your goal is not just to summarize the email, but to deeply understand what it reveals about the user's life,
        priorities, behaviors, goals, and environment.
        You are always learning and updating your understanding of who the user is.

        YOUR TASK:
        From each email you process, extract valuable, context-rich insights that help you form a more complete picture of the user over time.
        These are not summaries - they are memory entries.
        Think of them as memories you'd remember if you were a human assistant trying to truly support and anticipate the user's needs.

        EACH MEMORY ENTRY SHOULD:
        - Reflect what this message reveals about the user's current status, relationships, tasks, interests, habits, challenges, or decisions
        - Capture the underlying dynamics (e.g. the user is leading a project, made a choice, needs something, is being waited on)
        - Focus only on the user, not others unless relevant to the user's world
        - Be written like an internal note, not like a summary or reply

        RULES:
        1) Output only one memory entry per email.
        2) It must be deeply user-centric and suitable for long-term use.
        3) It should not exceed {self.character_limit} characters.
        4) No formatting, lists, or markdown - just a natural, concise paragraph that feels like a meaningful observation.
        5) Do not repeat the email's wording - interpret and condense meaning.

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

    async def summarize_batch(self, emails: list[dict]) -> list[str]:
        return await self.task_runner.run_async_tasks([
            self.summarize(email) for email in emails
        ])
