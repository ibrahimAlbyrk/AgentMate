from typing import Dict, Any, List, Optional

from Core.logger import LoggerCreator
from Core.Utils.email_utils import EmailUtils


class OutlookProcessor:
    """Process Outlook email data."""

    def __init__(self, default_email_filter: Optional[List[str]] = None):
        self.DEFAULT_EMAIL_FILTER = default_email_filter or [
            "id",
            "subject",
            "from",
            "body",
        ]
        self.logger = LoggerCreator.create_advanced_console("OutlookProcessor")

    def process_emails(self, result: Dict[str, Any]) -> Dict[str, Any]:
        try:
            processed_result = result.copy()
            processed_response = [
                self._filter_email(email, self.DEFAULT_EMAIL_FILTER)
                for email in result.get("data", {}).get("messages", [])
            ]
            processed_result["data"] = processed_response
            return processed_result
        except Exception as e:
            self.logger.error(f"Error processing emails: {str(e)}")
            return result

    def process_email(self, result: Dict[str, Any]) -> Dict[str, Any]:
        try:
            processed_result = result.copy()
            email = result.get("data", {})
            processed_result["data"] = self._filter_email(email, self.DEFAULT_EMAIL_FILTER)
            return processed_result
        except Exception as e:
            self.logger.error(f"Error processing email: {str(e)}")
            return result

    def process_email_subjects(self, result: Dict[str, Any]) -> Dict[str, Any]:
        try:
            processed_result = result.copy()
            processed_result["data"] = [
                {"subject": email.get("subject"), "id": email.get("id")}
                for email in result.get("data", {}).get("messages", [])
            ]
            return processed_result
        except Exception as e:
            self.logger.error(f"Error processing email subjects: {str(e)}")
            return result

    def _filter_email(self, email: Dict[str, Any], fields: List[str]) -> Dict[str, Any]:
        filtered = {field: email.get(field) for field in fields if field in email}
        body = filtered.get("body")
        if isinstance(body, dict):
            raw_body = body.get("content", "")
            filtered["body"] = EmailUtils.strip_html_tags(raw_body)
        return filtered
