from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ApplicationError
from app.core.security import create_access_token, hash_password, verify_password
from app.models.user import User
from app.schemas.user import UserRegister


INVALID_CREDENTIALS = "Invalid email or password"


async def get_user_by_email(session: AsyncSession, email: str) -> User | None:
    result = await session.execute(select(User).where(User.email == email.lower()))
    return result.scalar_one_or_none()


async def get_user_by_id(session: AsyncSession, user_id: int) -> User | None:
    return await session.get(User, user_id)


async def register_user(session: AsyncSession, payload: UserRegister) -> User:
    if await get_user_by_email(session, payload.email):
        raise ApplicationError(
            "An account with this email already exists",
            status_code=409,
        )

    user = User(
        full_name=payload.name,
        email=payload.email,
        password_hash=hash_password(payload.password),
        phone=payload.phone or None,
    )
    session.add(user)
    try:
        await session.commit()
    except IntegrityError as error:
        await session.rollback()
        raise ApplicationError(
            "An account with this email already exists",
            status_code=409,
        ) from error

    await session.refresh(user)
    return user


async def authenticate_user(session: AsyncSession, email: str, password: str) -> User:
    user = await get_user_by_email(session, email)
    if user is None or not verify_password(password, user.password_hash):
        raise ApplicationError(INVALID_CREDENTIALS, status_code=401)
    if not user.is_active:
        raise ApplicationError("Account is disabled", status_code=403)
    return user


def issue_user_token(user: User) -> str:
    return create_access_token(user.user_id, {"email": user.email})
