from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware

from app.config import get_settings
from app.database import init_db
from app.routes.auth import router as auth_router
from app.routes.pages import router as pages_router
from app.routes.planners import router as planner_router

BASE_DIR = Path(__file__).resolve().parents[1]
settings = get_settings()


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    yield


app = FastAPI(title=settings.app_name, version="1.0.0", description="Budget-aware GenAI recommendation assistant", lifespan=lifespan)

app.add_middleware(
    SessionMiddleware,
    secret_key=settings.secret_key,
    https_only=settings.session_https_only,
    same_site="lax",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")
app.include_router(pages_router)
app.include_router(auth_router)
app.include_router(planner_router)


@app.get("/health", tags=["system"])
def health() -> dict:
    return {"status": "ok", "service": settings.app_name, "environment": settings.app_env}


@app.get("/api/session-info", tags=["session"])
def session_info(request: Request):
    user_id = request.session.get("user_id")
    if not user_id:
        return {"authenticated": False, "user_id": None, "email": None, "full_name": None}
    from app.database import SessionLocal
    from app.models import User

    db = SessionLocal()
    try:
        user = db.get(User, int(user_id))
        if not user:
            request.session.clear()
            return {"authenticated": False, "user_id": None, "email": None, "full_name": None}
        return {"authenticated": True, "user_id": user.id, "email": user.email, "full_name": user.full_name}
    finally:
        db.close()


@app.get("/api/session-data", tags=["session"])
def session_data(request: Request):
    info = session_info(request)
    if not info["authenticated"]:
        return {"authenticated": False, "data": {}}
    from app.database import SessionLocal
    from app.models import RecommendationHistory
    import json

    db = SessionLocal()
    try:
        rows = db.query(RecommendationHistory).filter(RecommendationHistory.user_id == info["user_id"]).order_by(RecommendationHistory.created_at.desc()).limit(10).all()
        return {
            "authenticated": True,
            "data": {
                "user": info,
                "recent_recommendations": [json.loads(row.result_json) for row in rows],
            },
        }
    finally:
        db.close()


@app.exception_handler(Exception)
async def unhandled_error(_: Request, exc: Exception):
    return JSONResponse(status_code=500, content={"detail": "Unexpected server error", "type": exc.__class__.__name__})
