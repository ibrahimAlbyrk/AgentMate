from typing import Dict, Any, List, Optional

from Core.logger import LoggerCreator
from Core.Utils.email_utils import EmailUtils


class GmailProcessor:
    """
    This class encapsulates all the logic for processing and filtering
    email data retrieved from Gmail.
    """

    def __init__(self, default_email_filter: List[str] = None):
        self.DEFAULT_EMAIL_FILTER = default_email_filter or ["messageTimestamp", "messageId", "subject", "sender",
                                                             "payload"]

        self.logger = LoggerCreator.create_advanced_console("GmailProcessor")

    def process_emails(self, result: Dict[str, Any]) -> Dict[str, Any]:
        try:
            processed_result = result.copy()
            processed_response = []

            for email in result["data"]["messages"]:
                processed_response.append(
                    self._filter_and_process_email(email, fields=self.DEFAULT_EMAIL_FILTER)
                )

            processed_result["data"] = processed_response
            return processed_result
        except Exception as e:
            self.logger.error(f"Error processing emails: {str(e)}")
            return result

    def process_email(self, result: Dict[str, Any]) -> Dict[str, Any]:
        try:
            processed_result = result.copy()

            email = result["data"]
            processed_result["data"] = self._filter_and_process_email(email, fields=self.DEFAULT_EMAIL_FILTER)

            return processed_result
        except Exception as e:
            self.logger.error(f"Error processing email: {str(e)}")
            return result

    def process_email_subjects(self, result: Dict[str, Any]) -> Dict[str, Any]:
        try:
            return self._filter_gmail_fields(result, fields=["subject", "messageId"])
        except Exception as e:
            self.logger.error(f"Error processing email subjects: {str(e)}")
            return result

    def _filter_and_process_email(self, email: Dict[str, Any], fields: List[str]) -> Dict[str, Any]:
        filtered_email = {field: email[field] for field in fields if field in email}

        payload = filtered_email.get("payload")
        if payload:
            raw_body = EmailUtils.extract_message_body(payload)
            body = EmailUtils.strip_html_tags(raw_body or "")
            filtered_email["body"] = body
            del filtered_email["payload"]

        return filtered_email

    def _filter_gmail_fields(self, result: Dict[str, Any], fields: List[str]) -> Dict[str, Any]:
        processed_result = result.copy()
        processed_response = []

        for email in result["data"]["messages"]:
            filtered_email = {field: email[field] for field in fields if field in email}
            processed_response.append(filtered_email)

        processed_result["data"] = processed_response
        return processed_result