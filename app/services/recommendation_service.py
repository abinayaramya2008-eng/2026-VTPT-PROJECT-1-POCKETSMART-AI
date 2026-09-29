from datetime import datetime, timezone
from typing import Any

from sqlalchemy.orm import Session

from app.config import get_settings
from app.models import RecommendationHistory, User
from app.schemas import HomePlannerInput, JewelryPlannerInput, PartyPlannerInput, RecommendationResponse
from app.services.catalog_service import get_catalog
from app.services.gemini_service import GeminiService


class RecommendationService:
    def __init__(self) -> None:
        self.settings = get_settings()
        self.gemini = GeminiService()

    def generate_home(self, payload: HomePlannerInput, user: User, db: Session) -> RecommendationResponse:
        data = payload.model_dump()
        keywords = [payload.style]
        catalog = get_catalog("home", keywords)
        result = self._generate_or_fallback("home", data, catalog, None, None)
        return self._save_history("home", data, result, user, db)

    def generate_party(self, payload: PartyPlannerInput, user: User, db: Session) -> RecommendationResponse:
        data = payload.model_dump()
        keywords = [payload.event_type]
        catalog = get_catalog("party", keywords)
        # Cost context per guest is simulated, so the AI or fallback multiplies it by guest count.
        result = self._generate_or_fallback("party", data, catalog, None, None)
        return self._save_history("party", data, result, user, db)

    def generate_jewelry(
        self,
        payload: JewelryPlannerInput,
        user: User,
        db: Session,
        image_bytes: bytes | None = None,
        image_mime_type: str | None = None,
    ) -> RecommendationResponse:
        data = payload.model_dump()
        keywords = [payload.style, payload.metal_preference, payload.occasion]
        catalog = get_catalog("jewelry", keywords)
        result = self._generate_or_fallback("jewelry", data, catalog, image_bytes, image_mime_type)
        return self._save_history("jewelry", data, result, user, db)

    def get_history(self, db: Session, user: User) -> list[RecommendationHistory]:
        return (
            db.query(RecommendationHistory)
            .filter(RecommendationHistory.user_id == user.id)
            .order_by(RecommendationHistory.created_at.desc())
            .all()
        )

    def _generate_or_fallback(
        self,
        planner: str,
        payload: dict[str, Any],
        catalog: list[dict],
        image_bytes: bytes | None,
        image_mime_type: str | None,
    ) -> RecommendationResponse:
        if not self.settings.mock_ai and self.settings.gemini_api_key:
            try:
                ai_result = self.gemini.generate(planner, payload, catalog, image_bytes, image_mime_type)
                return self._normalize(ai_result)
            except Exception as exc:
                import logging
                logging.getLogger(__name__).exception(
                    "Gemini request failed for planner=%s; using local fallback: %s", planner, exc
                )
        return self._fallback(planner, payload, catalog)

    def _fallback(self, planner: str, payload: dict[str, Any], catalog: list[dict]) -> RecommendationResponse:
        budget = float(payload["budget"])
        now = datetime.now(timezone.utc)
        full_catalog = get_catalog(planner)

        if planner == "home":
            rows = []
            room_count = max(len(payload["rooms"]), 1)
            target = budget * 0.9
            for room in payload["rooms"]:
                requested = [
                    ("lighting", room["lights"], "Warm LED Ceiling Light"),
                    ("fan", room["ceiling_fans"], "Energy Efficient Ceiling Fan"),
                    ("dining", room["tables"], "Compact 4-Seater Dining Table"),
                    ("decor", room["decor_items"], "Indoor Plant Pot Set"),
                ]
                for category, qty, wanted in requested:
                    if qty <= 0:
                        continue
                    match = next((x for x in full_catalog if x["title"] == wanted), full_catalog[0])
                    per_qty = min(float(match["price"]), max(1.0, target / max(room_count * 3, 1)))
                    rows.append({**match, "price": round(per_qty, 2), "quantity": qty, "room": room["room_type"]})
            items = self._fit_rows(rows, target, catalog)
            breakdown = {"rooms": round(sum(item["price"] * item["quantity"] for item in items), 2)}
            return RecommendationResponse(
                planner="home", title="Your Home Budget Plan", summary=f"A {payload['style']} room setup within your INR budget, using a practical mix of essentials and decor.", budget=budget,
                estimated_total=round(sum(i["price"] * i["quantity"] for i in items), 2),
                savings=0, budget_breakdown=breakdown,
                recommendations=[self._item_schema(i, f"Fits your {payload['style']} style and stays budget-aware.") for i in items],
                tips=["Buy high-use items first, then add decorative pieces with the remaining budget.",
                      "Measure rooms before ordering furniture or lighting.",
                      "Use the simulated platform links as search starting points; confirm live prices before buying."],
                ai_generated=False, created_at=now,
            )

        if planner == "party":
            guests = int(payload["guests"])
            target = budget * 0.92
            rows = []
            catering = next(x for x in full_catalog if x["category"] == "catering")
            decoration = next(x for x in full_catalog if x["category"] == "decoration")
            venue = next(x for x in full_catalog if x["category"] == "venue")
            food_price = min(float(catering["price"]), target * 0.55 / max(guests, 1))
            rows.append({**catering, "price": round(food_price, 2), "quantity": guests})
            rows.append({**decoration, "price": min(float(decoration["price"]), target * 0.2), "quantity": 1})
            rows.append({**venue, "price": min(float(venue["price"]), target * 0.2), "quantity": 1})
            if payload["accommodation_needed"]:
                rows.append({"title": "Optional accommodation search", "category": "accommodation", "price": 0, "quantity": 1,
                             "platform": "OYO", "link": "https://www.oyorooms.com/", "description": "Use OYO as a search starting point for nearby stays."})
            items = self._fit_rows(rows, target, catalog)
            total = sum(i["price"] * i["quantity"] for i in items)
            breakdown: dict[str, float] = {}
            for item in items:
                category = str(item.get("category", "other"))
                breakdown[category] = round(
                    breakdown.get(category, 0.0) + float(item["price"]) * int(item.get("quantity", 1)),
                    2,
                )
            return RecommendationResponse(
                planner="party", title=f"{payload['event_type'].title()} Party Budget Plan", summary=f"A starting budget allocation for about {guests} guests, with emphasis on food, venue, and decoration.", budget=budget,
                estimated_total=round(total, 2), savings=round(max(budget - total, 0), 2),
                budget_breakdown=breakdown,
                recommendations=[self._item_schema(i, f"Suitable for approximately {guests} guests.") for i in items],
                tips=["Reserve venue and catering before optional extras.", "Keep a 5-10% contingency for last-minute changes.", "Confirm availability and final prices directly with the vendor platform."],
                ai_generated=False, created_at=now,
            )

        target = budget * 0.92
        items = [
            {**next(x for x in full_catalog if x["category"] == "earrings"), "price": min(1299.0, target * 0.45), "quantity": 1},
            {**next(x for x in full_catalog if x["category"] == "necklace"), "price": min(1699.0, target * 0.40), "quantity": 1},
        ]
        items = self._fit_rows(items, target, catalog)
        total = sum(i["price"] * i["quantity"] for i in items)
        outfit_note = payload.get("outfit_color") or "your outfit"
        return RecommendationResponse(
            planner="jewelry", title=f"{payload['occasion'].title()} Jewelry Plan", summary=f"A {payload['style']} jewelry pairing plan for your {payload['occasion']} occasion.", budget=budget,
            estimated_total=round(total, 2), savings=round(max(budget - total, 0), 2),
            budget_breakdown={"earrings": round(items[0]["price"], 2) if items else 0, "necklace": round(items[1]["price"], 2) if len(items) > 1 else 0},
            recommendations=[self._item_schema(i, f"Chosen as a style-friendly option for {outfit_note}.") for i in items],
            tips=["Match statement jewelry with simpler supporting pieces.", "For an uploaded outfit image, treat color coordination as a style suggestion rather than a guarantee.", "Verify metal, size, material, and live seller details before purchasing."],
            ai_generated=False, created_at=now,
        )

    def _normalize(self, result: RecommendationResponse) -> RecommendationResponse:
        total = sum(item.price * item.quantity for item in result.recommendations)
        if total > result.budget:
            kept = []
            running = 0.0
            for item in sorted(result.recommendations, key=lambda x: x.price):
                line_total = item.price * item.quantity
                if running + line_total <= result.budget:
                    kept.append(item)
                    running += line_total
            result.recommendations = kept
            total = running
        result.estimated_total = round(total, 2)
        result.savings = round(max(result.budget - total, 0), 2)
        result.created_at = datetime.now(timezone.utc)
        result.ai_generated = True
        return result

    @staticmethod
    def _fit_rows(rows: list[dict], target: float, catalog: list[dict]) -> list[dict]:
        result = []
        running = 0.0
        for row in rows:
            line = float(row["price"]) * int(row.get("quantity", 1))
            if line <= 0:
                result.append(row)
                continue
            if running + line <= target:
                result.append(row)
                running += line
        if not result and catalog:
            fallback = dict(catalog[0])
            fallback["price"] = min(float(fallback["price"]), max(target, 0))
            fallback["quantity"] = 1
            result.append(fallback)
        return result

    @staticmethod
    def _item_schema(item: dict, reason: str):
        from app.schemas import RecommendationItem

        return RecommendationItem(
            title=item["title"], category=item["category"], description=item.get("description", "Simulated catalog option."),
            platform=item["platform"], price=round(float(item["price"]), 2), quantity=int(item.get("quantity", 1)),
            reason=reason, link=item["link"],
        )

    @staticmethod
    def _save_history(planner: str, payload: dict, result: RecommendationResponse, user: User, db: Session) -> RecommendationResponse:
        import json

        row = RecommendationHistory(
            user_id=user.id, planner_type=planner,
            request_json=json.dumps(payload), result_json=result.model_dump_json(),
        )
        db.add(row)
        db.commit()
        return result
