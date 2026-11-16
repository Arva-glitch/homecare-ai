from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.deps import get_current_user
from app.core.security import (
    create_access_token,
    generate_reset_token,
    hash_password,
    hash_reset_token,
    verify_password,
)
from app.db.session import get_db
from app.models import User
from app.schemas.auth import (
    ForgotPasswordRequest,
    ForgotPasswordResponse,
    LoginRequest,
    RegisterRequest,
    ResetPasswordRequest,
    TokenResponse,
    UserOut,
)
from app.schemas.common import Message
from app.services.notification_service import notify
from app.utils.email import send_email

router = APIRouter(prefix="/auth", tags=["Authentication"])


def _token_response(user: User) -> TokenResponse:
    return TokenResponse(access_token=create_access_token(user.id, user.token_version),
                         user=UserOut.model_validate(user))


def _authenticate(db: Session, email: str, password: str) -> User:
    user = db.scalar(select(User).where(User.email == email.lower()))
    if not user or not verify_password(password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Incorrect email or password")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account is disabled")
    return user


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def register(payload: RegisterRequest, db: Session = Depends(get_db)):
    email = payload.email.lower()
    if db.scalar(select(User.id).where(User.email == email)):
        raise HTTPException(status_code=409, detail="An account with this email already exists")
    user = User(full_name=payload.full_name.strip(), email=email, hashed_password=hash_password(payload.password),
                household_name=payload.household_name)
    db.add(user)
    db.commit()
    db.refresh(user)
    notify(db, user, type="system", severity="info", title="Welcome to HomeCare AI",
           message="Start by adding your household appliances so the predictive engine can assess them.",
           link="/appliances", key="welcome")
    return _token_response(user)


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    return _token_response(_authenticate(db, payload.email, payload.password))


@router.post("/token", response_model=TokenResponse, include_in_schema=True,
             summary="OAuth2 password flow (used by the Swagger 'Authorize' button)")
def token(form: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    return _token_response(_authenticate(db, form.username, form.password))


@router.post("/logout", response_model=Message)
def logout(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Invalidates every token issued to this user so far (server-side logout)."""
    user.token_version += 1
    db.commit()
    return Message(message="Logged out successfully")


@router.get("/me", response_model=UserOut)
def me(user: User = Depends(get_current_user)):
    return user


@router.post("/forgot-password", response_model=ForgotPasswordResponse)
def forgot_password(payload: ForgotPasswordRequest, db: Session = Depends(get_db)):
    generic = "If an account exists for that email, a password reset link has been sent."
    user = db.scalar(select(User).where(User.email == payload.email.lower()))
    if not user:
        return ForgotPasswordResponse(message=generic)  # do not reveal whether the email exists

    raw, hashed = generate_reset_token()
    user.reset_token_hash = hashed
    user.reset_token_expires = datetime.now() + timedelta(minutes=settings.PASSWORD_RESET_EXPIRE_MINUTES)
    db.commit()

    link = f"{settings.FRONTEND_URL}/reset-password?token={raw}"
    sent = send_email(user.email, "Reset your HomeCare AI password",
                      f"Hello {user.full_name},\n\nUse this link to reset your password "
                      f"(valid for {settings.PASSWORD_RESET_EXPIRE_MINUTES} minutes):\n{link}\n\n"
                      "If you did not request this, you can ignore this email.")
    dev_token = raw if (not sent and settings.EXPOSE_RESET_TOKEN_IN_DEV
                        and settings.ENVIRONMENT != "production") else None
    return ForgotPasswordResponse(message=generic, dev_reset_token=dev_token)


@router.post("/reset-password", response_model=Message)
def reset_password(payload: ResetPasswordRequest, db: Session = Depends(get_db)):
    user = db.scalar(select(User).where(User.reset_token_hash == hash_reset_token(payload.token)))
    if not user or not user.reset_token_expires or user.reset_token_expires < datetime.now():
        raise HTTPException(status_code=400, detail="Reset link is invalid or has expired")
    user.hashed_password = hash_password(payload.new_password)
    user.reset_token_hash = None
    user.reset_token_expires = None
    user.token_version += 1  # sign out other sessions
    db.commit()
    return Message(message="Password has been reset. You can now log in.")
