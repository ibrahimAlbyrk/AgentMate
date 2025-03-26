import os
import pickle
import base64
from email import message_from_bytes
from Core.logger import LoggerCreator
from googleapiclient.discovery import build
from email.utils import parsedate_to_datetime
from google.auth.transport.requests import Request

class GmailService:
    def __init__(self, uid: str):
        self.uid = uid
        self.service = self._get_gmail_service()
        self.logger = LoggerCreator.create_advanced_console("GmailService")

    def _get_gmail_service(self):
        creds = None
        token_path = f"tokens/{self.uid}.pickle"

        if os.path.exists(token_path):
            with open(token_path, 'rb') as token_file:
                creds = pickle.load(token_file)

        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
                with open(token_path, 'wb') as token_file:
                    pickle.dump(creds, token_file)
            else:
                raise Exception("Gmail credentials not found or invalid.")

        return build('gmail', 'v1', credentials=creds)

    async def fetch_latest_emails(self, limit: int = 5) -> list[dict]:
        self.logger.debug(f"Fetching {limit} emails for UID: {self.uid}")
        results = self.service.users().messages().list(userId='me', maxResults=limit, q='in:inbox').execute()
        messages = results.get('messages', [])

        emails = []
        for msg in messages:
            email = await self._get_email_details(msg['id'])
            emails.append(email)

        return emails

    async def fetch_emails_by_ids(self, ids: list[str]) -> list[dict]:
        self.logger.debug(f"Fetching emails by ID for UID: {self.uid}: {ids}")
        return [await self._get_email_details(msg_id) for msg_id in ids]

    async def fetch_email_subjects_paginated(self, offset: int = 0, limit: int = 10) -> list[str]:
        self.logger.debug(f"Fetching email subjects (offset={offset}, limit={limit}) for UID: {self.uid}")
        result = self.service.users().messages().list(userId='me', maxResults=offset + limit, q='in:inbox').execute()
        messages = result.get('messages', [])

        subjects = []
        for i in range(offset, offset + limit):
            if i >= len(messages):
                break

            msg_id = messages[i]['id']
            msg = await self._get_email_details(msg_id)

            subject = "No Subject"
            headers = msg.get("payload", {}).get("headers", [])
            for h in headers:
                if h.get("name", "").lower() == "subject":
                    subject = h["value"]
                    break

            subjects.append({
                "id": msg_id,
                "subject": subject
            })

        return subjects

    async def _get_email_details(self, msg_id: str) -> dict:
        message = self.service.users().messages().get(userId='me', id=msg_id, format='full').execute()
        payload = message.get('payload', {})
        headers = payload.get('headers', [])

        date = next((h["value"] for h in headers if h["name"].lower() == "date"), "No Date")
        try:
            date_obj = parsedate_to_datetime(date).astimezone(timezone.utc)
            date_iso = date_obj.isoformat()
        except Exception:
            date_iso = date

        subject = next((h["value"] for h in headers if h["name"].lower() == "subject"), "No Subject")
        sender = next((h["value"] for h in headers if h["name"].lower() == "from"), "Unknown Sender")
        body = self._decode_email_body(payload)

        return {
            'id': msg_id,
            'date': date_iso,
            'subject': subject,
            'from': sender,
            'body': body
        }

    @staticmethod
    def _decode_email_body(payload: dict) -> str:
        decoded_parts = []
        if "body" in payload and "data" in payload["body"]:
            try:
                decoded_parts.append(base64.urlsafe_b64decode(payload["body"]["data"]).decode("utf-8"))
            except Exception as e:
                decoded_parts.append(f"[Error decoding body: {e}]")
        if "parts" in payload:
            for part in payload["parts"]:
                if "body" in part and "data" in part["body"]:
                    try:
                        decoded_parts.append(base64.urlsafe_b64decode(part["body"]["data"]).decode("utf-8"))
                    except Exception as e:
                        decoded_parts.append(f"[Error decoding part: {e}]")
        return "\n\n".join(decoded_parts) if decoded_parts else "[Content couldn't be read]"
