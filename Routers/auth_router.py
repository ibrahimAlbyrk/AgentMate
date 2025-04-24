import os
import json
import pickle
import requests

from DB.database import get_db

from Core.config import settings
from Core.logger import LoggerCreator
from Core.EventBus import EventBus
from Core.Models.domain import Event, EventType

from google_auth_oauthlib.flow import Flow
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import APIRouter, Request, HTTPException, Depends
from DB.Services.user_settings_service import UserSettingsService
from google.auth.transport.requests import Request as GoogleRequest

from Core.agent_starter import start_user_agents

from composio_openai import ComposioToolSet, App, Action

router = APIRouter(tags=["Unified Auth"])
logger = LoggerCreator.create_advanced_console("AuthRouter")

OAUTH_FLOW_CACHE: dict[str, dict] = {}

toolset = ComposioToolSet(api_key=settings.api.composio_api_key)

event_bus = EventBus()

@router.get("/{service}/is-logged-in")
async def is_logged_in(service: str, uid: str, session: AsyncSession = Depends(get_db)):
    user_settings = await UserSettingsService.get(session, uid, service)
    if not user_settings:
        return {"is_logged_in": False}

    service_id = user_settings.service_id
    is_logged_in = user_settings.is_logged_in

    if not is_logged_in:
        return {"is_logged_in": False}

    entity = toolset.get_entity(uid)
    connection = entity.get_connection(connected_account_id=service_id)
    if not connection:
        return {"is_logged_in": False}

    return {"is_logged_in": True}


@router.post("/{service}/login-directly")
async def service_login_directly(uid: str, service: str, service_id: str, session: AsyncSession = Depends(get_db)):
    logger.debug(f"Logging in: {uid}/{service}/{service_id}")
    redirect_url = await _service_login_handler(uid, service, service_id, session)
    return RedirectResponse(url=redirect_url)


@router.post("/{service}/logout")
async def service_logout(uid: str, service: str, session: AsyncSession = Depends(get_db)):
    if not uid:
        raise HTTPException(status_code=400, detail="Missing uid")

    user_settings = await UserSettingsService.get(session, uid, service)
    if not user_settings:
        return {
            "success": False,
            "info": f"There is no user settings for this user or service",
        }

    is_logged_in = user_settings.is_logged_in
    service_id = user_settings.service_id

    if not is_logged_in:
        return {
            "success": True,
            "info": "Already logged out"
        }

    try:
        url = f"https://backend.composio.dev/api/v1/connectedAccounts/{service_id}"
        headers = {"x-api-key": settings.api.composio_api_key}
        response = requests.delete(url, headers=headers)
        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail=response.text)

        logout_success = True
        info = "Successfully logged out"
    except Exception as e:
        logout_success = False
        info = f"An error occurred: {str(e)}"


    if logout_success:
        await UserSettingsService.set_logged_in(session, uid, service, False)
        await event_bus.publish_event(Event(
            type=EventType.STOP_AGENT,
            data={"uid": uid, "service": service},
        ))

    return {
        "success": logout_success,
        "info": info
    }


@router.get("/{service}/login")
async def service_login(uid: str, service: str, session: AsyncSession = Depends(get_db)):
    if not uid:
        raise HTTPException(status_code=400, detail="Missing uid")

    is_logged_in = await UserSettingsService.is_logged_in(session, uid, service)
    if is_logged_in:
        redirect_uri = settings.post_login_redirect.format(uid=uid, service=service)
        return RedirectResponse(url=redirect_uri)


    app = settings.get_app(service)
    conn_req = toolset.initiate_connection(app=app, entity_id=uid, redirect_url=f"{settings.base_uri}/api/{service}/callback?uid={uid}")
    redirect_uri = conn_req.redirectUrl

    logger.debug(f"[{service}] Redirecting UID {uid} to OAuth flow")
    return RedirectResponse(redirect_uri)


@router.get("/{service}/callback")
async def service_callback(uid: str, service: str, request: Request, session: AsyncSession = Depends(get_db)):
    status = request.query_params.get("status")
    if status != "success":
       return RedirectResponse(settings.base_uri)

    service_id = request.query_params.get("connectedAccountId")

    redirect_url = await _service_login_handler(uid, service, service_id, session)

    return RedirectResponse(url=redirect_url)

async def _service_login_handler(uid: str, service: str, service_id: str, session: AsyncSession = Depends(get_db)) -> str:
    if not uid:
        raise HTTPException(status_code=400, detail="Missing uid")

    if not service_id:
        raise HTTPException(status_code=400, detail="Missing service_id")

    has_service = await UserSettingsService.has_service(session, uid, serice)

    if has_service:
        await UserSettingsService.set_logged_in(session, uid, service, True)
        await UserSettingsService.change_service_id(session, uid, service, service_id)
    else:
        default_config = settings.get_service_config(service)
        if default_config:
            await UserSettingsService.set_config(session, uid, service_id, service, default_config)
        else:
            logger.debug(f"No configuration found for service: {service}")

    await start_user_agents(uid, session)

    redirect_uri = settings.post_login_redirect.format(uid=uid, service=service)
    return redirect_uri
