import os
import pickle
from Core.config import settings
from Core.logger import LoggerCreator
from google_auth_oauthlib.flow import Flow
from fastapi.responses import RedirectResponse
from fastapi import APIRouter, Request, HTTPException
from google.auth.transport.requests import Request as GoogleRequest

router = APIRouter(prefix="auth/gmail", tags="Gmail Auth")
logger = LoggerCreator.create_advanced_console("GmailAuth")

OAUTH_FLOW_CACHE: Dict[str, dict] = {}


@router.get("/{service}/login")
async def gmail_login(service: str, request: Request):
    uid = request.query_params.get("uid")
    if not uid:
        raise HTTPException(status_code=400, detail="Missing uid")

    provider = AUTH_PROVIDERS.get(service)
    if not provider:
        raise HTTPException(status_code=400, detail=f"Unknown service: {service}")

    flow = Flow.from_client_config(
        provider["client_secret"],
        scopes=provider["scopes"],
        redirect_uri=provider["redirect_uri"],
    )

    auth_url, state = flow.authorization_url(prompt="consent", include_granted_scopes="true")
    OAUTH_FLOW_CACHE[state] = {"flow": flow, "uid": uid, "service": service}

    logger.debug(f"[{service}] Redirecting UID {uid} to OAuth flow")
    return RedirectResponse(auth_url)


@router.get("/{service}/callback")
async def service_callback(service: str, request: Request):
    state = request.query_params.get("state")
    if not state or state not in OAUTH_FLOW_CACHE:
        raise HTTPException(status_code=400, detail=f"Invalid or expired OAuth state: {state}")

    cache = OAUTH_FLOW_CACHE[state]
    flow = cache["flow"]
    uid = cache["uid"]
    cached_service = cache["service"]

    if cached_service != service:
        raise HTTPException(status_code=400, detail=f"Service mismatch in OAuth state")

    provider = AUTH_PROVIDERS.get(service)
    if not provider:
        raise HTTPException(status_code=400, detail=f"Unknown service: {service}")

    flow.fetch_token(authorization_response=str(request.url))
    credentials = flow.credentials

    token_path = settings.TOKEN_PATH.format(uid=uid, service=service)
    os.makedirs(os.path.dirname(token_path), exist_ok=True)
    with open(token_path, "wb") as token_file:
        pickle.dump(credentials, token_file)

    logger.debug(f"[{service}] Credentials stored for UID: {uid}")
    del OAUTH_FLOW_CACHE[state]

    redirect_uri = settings.POST_LOGIN_REDIRECT.format(uid=uid, service=service)
    return RedirectResponse(url=redirect_uri)
