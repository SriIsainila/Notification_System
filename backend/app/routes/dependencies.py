from typing import Annotated

from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ApplicationError
from app.core.config import settings
from app.core.security import TokenValidationError, decode_access_token
from app.database import get_db_session
from app.models.user import User
from app.services.auth import get_user_by_id


bearer_scheme = HTTPBearer(auto_error=False)
DatabaseSession = Annotated[AsyncSession, Depends(get_db_session)]


async def get_current_user(
    request: Request,
    session: DatabaseSession,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
) -> User:
    token = None
    if credentials is not None and credentials.scheme.lower() == "bearer":
        token = credentials.credentials
    if token is None:
        token = request.cookies.get(settings.auth_cookie_name)
    if token is None:
        raise ApplicationError("Authentication required", status_code=401)

    try:
        payload = decode_access_token(token)
        user_id = int(payload["sub"])
    except (TokenValidationError, TypeError, ValueError, KeyError) as error:
        raise ApplicationError("Invalid or expired token", status_code=401) from error

    user = await get_user_by_id(session, user_id)
    if user is None or not user.is_active:
        raise ApplicationError("Invalid or expired token", status_code=401)
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]
