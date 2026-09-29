from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, field_validator


PlannerType = Literal["home", "party", "jewelry"]


class RoomInput(BaseModel):
    room_type: str = Field(min_length=2, max_length=50)
    lights: int = Field(default=1, ge=0, le=20)
    ceiling_fans: int = Field(default=1, ge=0, le=10)
    tables: int = Field(default=0, ge=0, le=10)
    chairs: int = Field(default=0, ge=0, le=30)
    decor_items: int = Field(default=0, ge=0, le=30)


class HomePlannerInput(BaseModel):
    budget: float = Field(gt=0, le=10_000_000)
    style: str = Field(default="modern", min_length=2, max_length=60)
    city: str = Field(default="India", min_length=2, max_length=80)
    notes: str = Field(default="", max_length=500)
    rooms: list[RoomInput] = Field(min_length=1, max_length=8)


class PartyPlannerInput(BaseModel):
    budget: float = Field(gt=0, le=10_000_000)
    guests: int = Field(gt=0, le=5000)
    event_type: str = Field(min_length=2, max_length=60)
    city: str = Field(default="India", min_length=2, max_length=80)
    venue_preference: str = Field(default="flexible", max_length=100)
    food_preference: str = Field(default="mixed", max_length=100)
    accommodation_needed: bool = False
    notes: str = Field(default="", max_length=500)

    @field_validator("event_type", "city", "venue_preference", "food_preference", mode="before")
    @classmethod
    def strip_text(cls, value: object) -> object:
        return str(value).strip()


class JewelryPlannerInput(BaseModel):
    budget: float = Field(gt=0, le=10_000_000)
    occasion: str = Field(min_length=2, max_length=80)
    style: str = Field(default="elegant", min_length=2, max_length=80)
    metal_preference: str = Field(default="any", max_length=60)
    outfit_color: str = Field(default="", max_length=60)
    outfit_description: str = Field(default="", max_length=500)


class RecommendationItem(BaseModel):
    title: str
    category: str
    description: str
    platform: str
    price: float = Field(ge=0)
    quantity: int = Field(default=1, ge=1)
    reason: str
    link: str


class RecommendationResponse(BaseModel):
    planner: PlannerType
    title: str
    summary: str
    budget: float
    estimated_total: float = Field(ge=0)
    savings: float = Field(ge=0)
    budget_breakdown: dict[str, float] = Field(default_factory=dict)
    recommendations: list[RecommendationItem] = Field(default_factory=list)
    tips: list[str] = Field(default_factory=list)
    ai_generated: bool = False
    created_at: datetime | None = None


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class SessionInfo(BaseModel):
    authenticated: bool
    user_id: int | None = None
    email: str | None = None
    full_name: str | None = None


class HistoryListItem(BaseModel):
    id: int
    planner_type: PlannerType
    created_at: datetime
    title: str
    estimated_total: float
