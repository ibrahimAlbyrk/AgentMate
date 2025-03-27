import os
import pickle
from Core.config import settings
from Core.logger import LoggerCreator
from google_auth_oauthlib.flow import Flow
from fastapi.responses import RedirectResponse
from fastapi import APIRouter, Request, HTTPException
from google.auth.transport.requests import Request as GoogleRequest

router = APIRouter(tags=["Unified Auth"])
logger = LoggerCreator.create_advanced_console("AuthRouter")

OAUTH_FLOW_CACHE: dict[str, dict] = {}


@router.get("/{service}/is-logged-in")
async def is_logged_in(service: str, uid: str):
    provider = settings.AUTH_PROVIDERS.get(service)
    if not provider:
        raise HTTPException(status_code=400, detail="Unknown service")

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

    _save_token(credentials)


@router.get("/{service}/login")
async def service_login(uid: str, service: str, request: Request):
    if not uid:
        raise HTTPException(status_code=400, detail="Missing uid")

    provider = settings.AUTH_PROVIDERS.get(service)
    if not provider:
        raise HTTPException(status_code=400, detail=f"Unknown service: {service}")

    client_secret_path =  provider["client_secret"]
    if not client_secret_path:
        raise HTTPException(status_code=400, detail="Missing client_secret")

    with open(client_secret_path, "rb") as client_secret_file:
        client_secret = json.load(client_secret_file)

    flow = Flow.from_client_config(
        client_secret,
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

    provider = settings.AUTH_PROVIDERS.get(service)
    if not provider:
        raise HTTPException(status_code=400, detail=f"Unknown service: {service}")



    flow.fetch_token(authorization_response=str(request.url))
    credentials = flow.credentials

    _save_token(credentials)

    del OAUTH_FLOW_CACHE[state]

    redirect_uri = settings.POST_LOGIN_REDIRECT.format(uid=uid, service=service)
    return RedirectResponse(url=redirect_uri)


def _save_token(credentials):
    token_path = settings.TOKEN_PATH.format(uid=uid, service=service)
    os.makedirs(os.path.dirname(token_path), exist_ok=True)
    with open(token_path, "wb") as token_file:
        pickle.dump(credentials, token_file)

    logger.debug(f"[{service}] Credentials stored for UID: {uid}")
