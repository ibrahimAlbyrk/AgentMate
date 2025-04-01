import os
import json
import pickle
import requests
from DB.database import get_db
from Core.config import settings
from Core.logger import LoggerCreator
from google_auth_oauthlib.flow import Flow
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import APIRouter, Request, HTTPException, Depends
from DB.Services.user_settings_service import UserSettingsService
from google.auth.transport.requests import Request as GoogleRequest

from composio_openai import ComposioToolSet, App, Action

router = APIRouter(tags=["Unified Auth"])
logger = LoggerCreator.create_advanced_console("AuthRouter")

OAUTH_FLOW_CACHE: dict[str, dict] = {}

toolset = ComposioToolSet(api_key=settings.COMPOSIO_API_KEY)

@router.get("/{service}/is-logged-in")
async def is_logged_in(service: str, uid: str, session: AsyncSession = Depends(get_db)):
    provider = settings.AUTH_PROVIDERS.get(service)
    if not provider:
        raise HTTPException(status_code=400, detail="Unknown service")

    is_logged_in = await UserSettingsService.is_logged_in(session, uid, service)
    if not is_logged_in:
        return {"is_logged_in": False}

    token_path = settings.TOKEN_PATH.format(uid=uid, service=service)
    if not os.path.exists(token_path):
        return {"is_logged_in": False}

    try:
        with open(token_path, "rb") as token_file:
            credentials = pickle.load(token_file)
        if credentials and credentials.valid:
            return {"is_logged_in": True}
        elif credentials and credentials.expired and credentials.refresh_token:
            credentials.refresh(GoogleRequest())
            with open(token_path, "wb") as token_file:
                pickle.dump(credentials, token_file)
            return {"is_logged_in": True}
    except Exception as e:
        logger.warning(f"[{service}] Login check failed for {uid}: {str(e)}")

    return {"is_logged_in": False}


@router.post("/{service}/login-directly")
async def service_login_directly(uid: str, service: str, credentials: str):
    if not uid:
        raise HTTPException(status_code=400, detail="Missing uid")

    provider = settings.AUTH_PROVIDERS.get(service)
    if not provider:
        raise HTTPException(status_code=400, detail=f"Unknown service: {service}")

    _save_token(uid, service, credentials)


@router.post("/{service}/logout")
async def service_logout(uid: str, service: str, session: AsyncSession = Depends(get_db)):
    """
    Return:
        - Success
        - Info
    """
    if not uid:
        raise HTTPException(status_code=400, detail="Missing uid")

    user_settings = await UserSettingsService.get(session, uid, service)
    is_logged_in = user_settings.is_logged_in
    service_id = user_settings.service_id

    if not is_logged_in:
        return {
            "success": True,
            "info": "Already logged out"
        }

    try:
        await UserSettingsService.set_logged_in(session, uid, service, True)

        url = f"https://backend.composio.dev/api/v1/connectedAccounts/{service_id}"
        headers = {"x-api-key": settings.COMPOSIO_API_KEY}
        response = requests.delete(url, headers=headers)
        print(response.status_code)
        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail=response.text)

        logout_success = True
        info = "Successfully logged out"
    except Exception as e:
        logout_success = False
        info = f"An error occurred: {str(e)}"


    if logout_success:
        await UserSettingsService.set_logged_in(session, uid, service, False)

    return {
        "success": logout_success,
        "info": info
    }


@router.get("/{service}/login")
async def service_login(uid: str, service: str, session: AsyncSession = Depends(get_db)):
    if not uid:
        raise HTTPException(status_code=400, detail="Missing uid")

    provider = settings.AUTH_PROVIDERS.get(service)
    if not provider:
        raise HTTPException(status_code=400, detail=f"Unknown service: {service}")

    is_logged_in = await UserSettingsService.is_logged_in(session, uid, service)
    if is_logged_in:
        data = await UserSettingsService.get(session, uid, service)
        print(data.service_id)
        redirect_uri = settings.POST_LOGIN_REDIRECT.format(uid=uid, service=service)
        return RedirectResponse(url=redirect_uri)

    service_name = settings.SERVICES.get(service)
    entity = toolset.get_entity(uid)
    conn_req = entity.initiate_connection(service_name, redirect_url=f"{settings.BASE_URI}/api/{service}/callback?uid={uid}")
    redirect_uri = conn_req.redirectUrl

    logger.debug(f"[{service}] Redirecting UID {uid} to OAuth flow")
    return RedirectResponse(redirect_uri)


@router.get("/{service}/callback")
async def service_callback(uid: str, service: str, request: Request, session: AsyncSession = Depends(get_db)):
    status = request.query_params.get("status")
    if status != "success":
       return RedirectResponse(settings.BASE_URI)

    if not uid:
        raise HTTPException(status_code=400, detail="Missing uid")

    service_id = request.query_params.get("connectedAccountId")
    if not service_id:
        raise HTTPException(status_code=400, detail="Missing service_id")

    has_user = UserSettingsService.has_any(session, uid)

    if has_user:
        print("has user")
        await UserSettingsService.set_logged_in(session, uid, service, True)
    else:
        default_config = settings.DEFAULT_CONFIGS.get(service, {})
        await UserSettingsService.set_config(session, uid, service_id, service, default_config)

    redirect_uri = settings.POST_LOGIN_REDIRECT.format(uid=uid, service=service)
    return RedirectResponse(url=redirect_uri)


def _save_token(uid: str, service, credentials):
    token_path = settings.TOKEN_PATH.format(uid=uid, service=service)
    os.makedirs(os.path.dirname(token_path), exist_ok=True)
    with open(token_path, "wb") as token_file:
        pickle.dump(credentials, token_file)

    logger.debug(f"[{service}] Credentials stored for UID: {uid}")
