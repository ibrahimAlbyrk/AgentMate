import asyncio

from fastapi import APIRouter, Request, HTTPException

from Agents.Gmail.gmail_agent import GmailAgent

from Core.config import settings
from Core.EventBus import EventBus
from Core.agent_manager import AgentManager
from Core.Models.domain import Event, EventType

router = APIRouter(prefix="/gmail", tags=["Gmail"])

agent_manager = AgentManager()

event_bus = EventBus()


@router.get("/get-email-subjects")
async def get_email_subjects(uid: str, offset: int = 0, limit: int = 10):
    if not uid:
        raise HTTPException(status_code=400, detail=f"UID not provided")

    mail_count = offset + limit

    agent = agent_manager.get_agent(uid, "gmail", GmailAgent)
    emails = await agent.get_emails_subjects(mail_count)
    subjects: list[dict[str, str]] = []
    for email in emails:
        email_id = email.get("messageId")
        email_subject = email.get("subject")
        data = {"id": email_id, "subject": email_subject}
        subjects.append(data)

    return {"subjects": subjects[offset: mail_count]}


@router.post("/convert-to-memory")
async def convert_to_memories(uid: str, request: Request):
    if not uid:
        raise HTTPException(status_code=400, detail="Missing uid")

    data = await request.json()
    mode = data.get("mode", "count")
    agent = agent_manager.get_agent(uid, "gmail", GmailAgent)

    emails: list[dict] = []
    if mode == "count":
        count = int(data.get("count", 0))
        if not count:
            raise HTTPException(status_code=400, detail="Missing count")
        emails = await agent.get_emails(limit=count)


    elif mode == "selection":
        ids = data.get("selectedIds", [])
        if not ids:
            raise HTTPException(status_code=400, detail="No emails selected")
        agent = agent_manager.get_agent(uid, "gmail", GmailAgent)
        tasks = [agent.get_email_by_message_id(m_id) for m_id in ids]
        emails = await asyncio.gather(*tasks)

    else:
        raise HTTPException(status_code=400, detail="Invalid mode")

    await event_bus.publish_event(Event(
        type=EventType.GMAIL_SUMMARY,
        data={"uid": uid, "emails": emails}
    ))

    return {"status": "done", "memories": len(emails)}
