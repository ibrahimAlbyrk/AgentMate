from dataclasses import dataclass
from typing import List, Dict, Any, Type

from Engines.ai_engine import BaseAIEngine, AIRequest


class EmailMemorySummarizerEngine(BaseAIEngine):
    """
    This engine creates concise summaries of emails that can be used
    for building long-term memory about the user.
    """

    def __init__(self, character_limit: int = 200):
        super().__init__(name="EmailMemorySummarizer")
        self.character_limit = character_limit

    async def summarize(self, email: Dict[str, Any]) -> str:
        subject = email.get("subject", "")
        email_body = email.get("body", "")

        if not subject or not email_body:
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
        Content: {email_body}
        """

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
        return await self.process_batch(uid, emails, self.summarize)
