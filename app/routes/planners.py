import mimetypes
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models import RecommendationHistory, User
from app.schemas import HomePlannerInput, JewelryPlannerInput, PartyPlannerInput, RecommendationResponse
from app.services.recommendation_service import RecommendationService

router = APIRouter(prefix="/api", tags=["planners"])
service = RecommendationService()


@router.post("/generate-home", response_model=RecommendationResponse)
def generate_home(payload: HomePlannerInput, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return service.generate_home(payload, user, db)


@router.post("/generate-party", response_model=RecommendationResponse)
def generate_party(payload: PartyPlannerInput, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return service.generate_party(payload, user, db)


def _normalize_image_mime(upload: UploadFile) -> str | None:
    """Normalize common browser variations using both MIME type and filename."""
    raw_mime = (upload.content_type or "").lower().strip()
    if raw_mime == "image/jpg":
        raw_mime = "image/jpeg"
    if raw_mime in {"image/jpeg", "image/png", "image/webp"}:
        return raw_mime

    guessed, _ = mimetypes.guess_type(upload.filename or "")
    if guessed == "image/jpg":
        guessed = "image/jpeg"
    if guessed in {"image/jpeg", "image/png", "image/webp"}:
        return guessed
    return None


def _validate_image_bytes(data: bytes, mime_type: str) -> None:
    """Validate that the bytes are a real image, not only a renamed file."""
    try:
        from PIL import Image
        from io import BytesIO

        with Image.open(BytesIO(data)) as image:
            image.verify()
    except Exception as exc:
        raise HTTPException(status_code=400, detail="The uploaded file is not a valid JPG, PNG, or WEBP image") from exc

    expected_formats = {
        "image/jpeg": {"JPEG"},
        "image/png": {"PNG"},
        "image/webp": {"WEBP"},
    }
    try:
        from PIL import Image
        from io import BytesIO

        with Image.open(BytesIO(data)) as image:
            if image.format not in expected_formats.get(mime_type, set()):
                raise HTTPException(status_code=400, detail="The image format does not match its file type")
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=400, detail="Unable to validate the uploaded image") from exc


@router.post("/generate-jewelry", response_model=RecommendationResponse)
async def generate_jewelry(
    budget: float = Form(...),
    occasion: str = Form(...),
    style: str = Form("elegant"),
    metal_preference: str = Form("any"),
    outfit_color: str = Form(""),
    outfit_description: str = Form(""),
    outfit_image: UploadFile | None = File(default=None),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    payload = JewelryPlannerInput(
        budget=budget,
        occasion=occasion,
        style=style,
        metal_preference=metal_preference,
        outfit_color=outfit_color,
        outfit_description=outfit_description,
    )

    image_bytes = None
    image_mime = None

    if outfit_image is not None and outfit_image.filename:
        image_mime = _normalize_image_mime(outfit_image)
        if image_mime is None:
            raise HTTPException(status_code=400, detail="Use a JPG, JPEG, PNG, or WEBP image")

        image_bytes = await _read_upload(outfit_image)
        if len(image_bytes) > service.settings.max_image_bytes:
            raise HTTPException(
                status_code=413,
                detail=f"Image must be <= {service.settings.max_image_mb} MB",
            )
        if not image_bytes:
            raise HTTPException(status_code=400, detail="The uploaded image is empty")

        _validate_image_bytes(image_bytes, image_mime)

    return service.generate_jewelry(payload, user, db, image_bytes, image_mime)


async def _read_upload(upload: UploadFile) -> bytes:
    # UploadFile.read() is async in FastAPI/Starlette.
    return await upload.read()


@router.post("/recommendations-details", response_model=RecommendationResponse)
def recommendations_details(payload: dict, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    planner = payload.get("planner")
    data = payload.get("data")
    if not isinstance(data, dict):
        raise HTTPException(status_code=400, detail="data must be an object")
    if planner == "home":
        return service.generate_home(HomePlannerInput.model_validate(data), user, db)
    if planner == "party":
        return service.generate_party(PartyPlannerInput.model_validate(data), user, db)
    if planner == "jewelry":
        return service.generate_jewelry(JewelryPlannerInput.model_validate(data), user, db)
    raise HTTPException(status_code=400, detail="planner must be home, party, or jewelry")


@router.get("/history")
def history(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    rows = service.get_history(db, user)
    output = []
    for row in rows:
        import json

        result = json.loads(row.result_json)
        output.append(
            {
                "id": row.id,
                "planner_type": row.planner_type,
                "created_at": row.created_at,
                "title": result.get("title", "Recommendation Plan"),
                "estimated_total": result.get("estimated_total", 0),
                "result": result,
            }
        )
    return output


@router.delete("/history/{history_id}")
def delete_history(history_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    row = (
        db.query(RecommendationHistory)
        .filter(RecommendationHistory.id == history_id, RecommendationHistory.user_id == user.id)
        .first()
    )
    if not row:
        raise HTTPException(status_code=404, detail="History entry not found")
    db.delete(row)
    db.commit()
    return {"message": "History entry deleted"}
