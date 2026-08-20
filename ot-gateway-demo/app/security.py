from datetime import UTC, datetime, timedelta
from secrets import compare_digest
from typing import Annotated

from fastapi import Header, HTTPException, Request, status
from jose import JWTError, jwt

from .config import Settings
from .models import Identity, Role

DEMO_ACCOUNTS = {
    "guest": {"password": "guest-demo", "role": "guest", "zone": None},
    "operator-a": {"password": "operator-a-demo", "role": "operator", "zone": "A"},
    "operator-b": {"password": "operator-b-demo", "role": "operator", "zone": "B"},
    "supervisor": {"password": "supervisor-demo", "role": "supervisor", "zone": None},
    "admin": {"password": "admin-demo", "role": "admin", "zone": None},
}


def authenticate(username: str, password: str) -> Identity | None:
    account = DEMO_ACCOUNTS.get(username)
    if account is None or not compare_digest(account["password"], password):
        return None
    return Identity(username=username, role=account["role"], zone=account["zone"])


def create_token(identity: Identity, settings: Settings) -> str:
    expires_at = datetime.now(UTC) + timedelta(minutes=settings.token_expire_minutes)
    payload = {
        "sub": identity.username,
        "role": identity.role,
        "zone": identity.zone,
        "iss": "iass-ot-gateway-demo",
        "exp": expires_at,
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_token(token: str, settings: Settings) -> Identity:
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret,
            algorithms=[settings.jwt_algorithm],
            issuer="iass-ot-gateway-demo",
        )
        username = payload.get("sub")
        role = payload.get("role")
        if not isinstance(username, str) or role not in {
            "guest",
            "operator",
            "supervisor",
            "admin",
        }:
            raise JWTError("Invalid identity claims")
        return Identity(username=username, role=role, zone=payload.get("zone"))
    except JWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired gateway token",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc


def optional_identity(
    request: Request,
    authorization: Annotated[str | None, Header()] = None,
) -> Identity | None:
    if authorization is None:
        return None
    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token:
        if request.app.state.settings.profile == "vulnerable":
            return None
        raise HTTPException(status_code=401, detail="Invalid authorization header")
    try:
        return decode_token(token, request.app.state.settings)
    except HTTPException:
        if request.app.state.settings.profile == "vulnerable":
            return None
        raise


def require_identity(
    request: Request,
    authorization: Annotated[str | None, Header()] = None,
) -> Identity:
    identity = optional_identity(request, authorization)
    if identity is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Gateway authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return identity


def require_role(identity: Identity, *roles: Role) -> None:
    if identity.role not in roles:
        raise HTTPException(status_code=403, detail="Insufficient gateway role")
