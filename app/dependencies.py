from typing import Annotated

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.auth import decode_access_token
from app.database import get_db
from app.models import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/token", auto_error=False)
DbSession = Annotated[Session, Depends(get_db)]


def get_current_user(request: Request, db: DbSession, bearer_token: str | None = Depends(oauth2_scheme)) -> User:
    user_id: int | None = None

    session_user_id = request.session.get("user_id")
    if session_user_id:
        user_id = int(session_user_id)

    if user_id is None and bearer_token:
        try:
            payload = decode_access_token(bearer_token)
            user_id = int(payload["sub"])
        except (KeyError, ValueError, TypeError, Exception) as exc:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token") from exc

    if user_id is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required")

    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return user
