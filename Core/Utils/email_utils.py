import base64
from bs4 import BeautifulSoup

class EmailUtils:
    @staticmethod
    def extract_message_body(payload, prefer_html=True):
        def decode(data):
            return base64.urlsafe_b64decode(data.encode("ASCII")).decode("utf-8")

        def get_part(parts):
            for part in parts:
                mime_type = part.get("mimeType", "")
                data = part.get("body", {}).get("data")

                if part.get("parts"):
                    result = get_part(part["parts"])
                    if result:
                        return result
                elif (prefer_html and mime_type == "text/html") or (not prefer_html and mime_type == "text/plain"):
                    if data:
                        return decode(data)
            return None

        if payload.get("body", {}).get("data"):
            return decode(payload["body"]["data"])

        if "parts" in payload:
            return get_part(payload["parts"])

        return ""

    @staticmethod
    def strip_html_tags(html: str) -> str:
        return BeautifulSoup(html, "html.parser").get_text()

    @staticmethod
    def decode_email(payload: dict) -> dict:
        date = payload.get("messageTimestamp")
        msg_id = payload.get("messageId")
        subject = payload.get("subject")
        sender = payload.get("sender")
        payload = payload.get("payload")

        raw_body = EmailUtils.extract_message_body(payload)
        body = EmailUtils.strip_html_tags(raw_body or "")

        return {
            'id': msg_id,
            'date': date,
            'subject': subject,
            'sender': sender,
            'body': body
        }