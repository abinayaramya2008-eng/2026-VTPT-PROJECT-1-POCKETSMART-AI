import json

SYSTEM_INSTRUCTION = """
You are PocketSmart AI, a budget-aware lifestyle planning assistant.
Return ONLY valid JSON matching the requested schema.
Never invent live prices or claim a product is currently in stock.
Treat the provided catalog as simulated/offline data.
Keep the total recommendation cost within the user's budget.
Prefer practical, culturally appropriate, concise suggestions.
For jewelry image inputs, use the image only to infer broad color/style coordination, not identity.
""".strip()

OUTPUT_SHAPE = {
    "planner": "home | party | jewelry",
    "title": "short title",
    "summary": "2-4 sentence summary",
    "budget": 0,
    "estimated_total": 0,
    "savings": 0,
    "budget_breakdown": {"category": 0},
    "recommendations": [
        {
            "title": "item",
            "category": "category",
            "description": "description",
            "platform": "platform",
            "price": 0,
            "quantity": 1,
            "reason": "reason",
            "link": "https://example.com/search?q=item",
        }
    ],
    "tips": ["tip"],
    "ai_generated": True,
}


def build_prompt(planner: str, payload: dict, catalog: list[dict], image_note: str = "") -> str:
    return f"""
Create a {planner} budget plan from the request and simulated catalog below.

REQUEST:
{json.dumps(payload, indent=2)}

SIMULATED CATALOG:
{json.dumps(catalog, indent=2)}

IMAGE CONTEXT:
{image_note or "No image supplied."}

Rules:
1. Use only catalog items for concrete product/service recommendations.
2. You may group items by category and quantity.
3. The sum of price * quantity must not exceed the budget.
4. Keep recommendations useful and diverse across the listed platforms.
5. Prefer 4-8 recommendations.
6. Use platform search links already supplied in the catalog.
7. Do not state that links or prices were fetched live.
8. Output exactly one JSON object using this shape:
{json.dumps(OUTPUT_SHAPE, indent=2)}
""".strip()
