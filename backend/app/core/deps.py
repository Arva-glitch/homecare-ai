"""FastAPI dependencies: authenticated user resolution and ownership helpers."""
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.security import decode_access_token
from app.db.session import get_db
from app.models import Appliance, User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/token")


def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    credentials_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    payload = decode_access_token(token)
    if not payload:
        raise credentials_error
    try:
        user_id = int(payload["sub"])
    except (KeyError, ValueError):
        raise credentials_error
    user = db.get(User, user_id)
    if not user or not user.is_active or payload.get("tv") != user.token_version:
        raise credentials_error
    return user


def get_owned_appliance(db: Session, user: User, appliance_id: int) -> Appliance:
    """Fetch an appliance that belongs to the current user, or 404 (never leak other users' data)."""
    appliance = db.get(Appliance, appliance_id)
    if not appliance or appliance.user_id != user.id:
        raise HTTPException(status_code=404, detail="Appliance not found")
    return appliance
