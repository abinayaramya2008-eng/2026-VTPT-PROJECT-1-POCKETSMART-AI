from fastapi import APIRouter, Depends, Form, HTTPException, Request, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth import create_access_token, hash_password, verify_password
from app.database import get_db
from app.models import User
from app.schemas import TokenResponse

router = APIRouter(prefix="/api/auth", tags=["auth"])


def find_user(db: Session, email: str) -> User | None:
    return db.scalar(select(User).where(User.email == email.lower().strip()))


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def register(request: Request, payload: dict, db: Session = Depends(get_db)) -> TokenResponse:
    email = str(payload.get("email", "")).strip().lower()
    password = str(payload.get("password", ""))
    full_name = str(payload.get("full_name", "")).strip()[:120]
    if "@" not in email or len(email) > 255:
        raise HTTPException(status_code=400, detail="Enter a valid email address")
    if len(password) < 8:
        raise HTTPException(status_code=400, detail="Password must contain at least 8 characters")
    if find_user(db, email):
        raise HTTPException(status_code=409, detail="An account with this email already exists")
    user = User(email=email, full_name=full_name, password_hash=hash_password(password))
    db.add(user)
    db.commit()
    db.refresh(user)
    request.session["user_id"] = user.id
    token = create_access_token(user.id, user.email)
    return TokenResponse(access_token=token)


@router.post("/login", response_model=TokenResponse)
def login(request: Request, payload: dict, db: Session = Depends(get_db)) -> TokenResponse:
    email = str(payload.get("email", "")).strip().lower()
    password = str(payload.get("password", ""))
    user = find_user(db, email)
    if not user or not verify_password(password, user.password_hash):
        raise HTTPException(status_code=401, detail="Incorrect email or password")
    request.session["user_id"] = user.id
    return TokenResponse(access_token=create_access_token(user.id, user.email))


@router.post("/token", response_model=TokenResponse)
def token(request: Request, form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)) -> TokenResponse:
    user = find_user(db, form_data.username)
    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Incorrect email or password")
    request.session["user_id"] = user.id
    return TokenResponse(access_token=create_access_token(user.id, user.email))


@router.post("/logout")
def logout(request: Request) -> dict:
    request.session.clear()
    return {"message": "Logged out successfully"}
