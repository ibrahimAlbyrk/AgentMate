import json
from dataclasses import dataclass
from typing import Optional, Generic, List, Dict, Any

from Engines.ai_engine import BaseAIEngine, AIRequest

class EmailClassifierEngine(BaseAIEngine):
    """
    This engine analyzes emails and classifies them based on importance,
    priority, sentiment, etc.
    """

    def __init__(self):
        super().__init__(name="EmailClassifier")

    async def classify(self,
                       email: Dict[str, Any],
                       important_categories: Optional[List[str]] = None,
                       ignored_categories: Optional[List[str]] = None) -> Dict[str, Any]:
        important_categories = important_categories or []
        ignored_categories = ignored_categories or []

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
            self.logger.error(f"Classification error: {str(e)}")
            return {}

    async def classify_batch(self,
                             uid: str,
                             emails: List[Dict[str, Any]],
                             important_categories: Optional[List[str]] = None,
                             ignored_categories: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        async def process_email(email: Dict[str, Any]) -> Dict[str, Any]:
            return await self.classify(email, important_categories, ignored_categories)

        return await self.process_batch(uid, emails, process_email)

    @staticmethod
    def _build_classification_prompt(email: Dict[str, Any]) -> str:
        subject = email.get("subject", "")
        sender = email.get("sender", "Unknown")
        email_body = email.get("body", "")

        return f"Title: {subject}\nFrom: {sender}\nContent: {email_body[:1000]}"

    @staticmethod
    def _build_classify_tool(important_categories: List[str], ignored_categories: List[str]) -> Dict[str, Any]:
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
