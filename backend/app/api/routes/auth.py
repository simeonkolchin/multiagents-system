from fastapi import APIRouter, HTTPException

from app.api.deps import CurrentUser, SessionDep, SettingsDep
from app.repositories import users as users_repo
from app.schemas.auth import (
    LoginRequest,
    RegisterRequest,
    TokenResponse,
    UserRead,
)
from app.services.security import create_access_token, hash_password, verify_password

router = APIRouter(prefix="/auth", tags=["auth"])


def _token(settings, user) -> TokenResponse:
    token = create_access_token(settings, user.id, user.email)
    return TokenResponse(
        access_token=token,
        user=UserRead(id=user.id, email=user.email, name=user.name),
    )


@router.post("/register", response_model=TokenResponse)
async def register(
    payload: RegisterRequest, session: SessionDep, settings: SettingsDep
) -> TokenResponse:
    email = payload.email.strip().lower()
    if "@" not in email:
        raise HTTPException(status_code=422, detail="некорректный email")
    if await users_repo.get_by_email(session, email):
        raise HTTPException(status_code=409, detail="email уже зарегистрирован")
    user = await users_repo.create(
        session, email, hash_password(payload.password), payload.name
    )
    return _token(settings, user)


@router.post("/login", response_model=TokenResponse)
async def login(
    payload: LoginRequest, session: SessionDep, settings: SettingsDep
) -> TokenResponse:
    email = payload.email.strip().lower()
    user = await users_repo.get_by_email(session, email)
    if user is None or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="неверный email или пароль")
    return _token(settings, user)


@router.get("/me", response_model=UserRead)
async def me(user: CurrentUser) -> UserRead:
    return UserRead(id=user.id, email=user.email, name=user.name)
