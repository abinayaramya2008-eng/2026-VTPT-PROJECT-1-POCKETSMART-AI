from urllib.parse import quote_plus


PLATFORM_BASES = {
    "Amazon": "https://www.amazon.in/s?k={query}",
    "Flipkart": "https://www.flipkart.com/search?q={query}",
    "IKEA": "https://www.ikea.com/in/en/search/?q={query}",
    "Swiggy": "https://www.swiggy.com/search?query={query}",
    "Zomato": "https://www.zomato.com/search?q={query}",
    "OYO": "https://www.oyorooms.com/search?location={query}",
}

HOME_CATALOG = [
    {"title": "Warm LED Ceiling Light", "category": "lighting", "price": 1499, "platform": "Amazon", "tags": ["modern", "warm", "lighting"]},
    {"title": "Energy Efficient Ceiling Fan", "category": "fan", "price": 2399, "platform": "Flipkart", "tags": ["modern", "energy"]},
    {"title": "Compact 4-Seater Dining Table", "category": "dining", "price": 8999, "platform": "IKEA", "tags": ["modern", "dining"]},
    {"title": "Accent Wall Art Set", "category": "decor", "price": 1299, "platform": "Amazon", "tags": ["decor", "modern"]},
    {"title": "Cushion Cover Set", "category": "soft decor", "price": 799, "platform": "Flipkart", "tags": ["cozy", "decor"]},
    {"title": "Minimalist Floor Lamp", "category": "lighting", "price": 3299, "platform": "IKEA", "tags": ["minimal", "modern", "lighting"]},
    {"title": "Storage Cabinet", "category": "storage", "price": 5499, "platform": "IKEA", "tags": ["storage", "modern"]},
    {"title": "Indoor Plant Pot Set", "category": "decor", "price": 999, "platform": "Amazon", "tags": ["decor", "natural"]},
]

PARTY_CATALOG = [
    {"title": "Veg & Non-Veg Catering Package", "category": "catering", "price": 550, "platform": "Zomato", "unit": "per guest", "tags": ["birthday", "wedding", "corporate"]},
    {"title": "Party Snacks Combo", "category": "catering", "price": 180, "platform": "Swiggy", "unit": "per guest", "tags": ["birthday", "casual"]},
    {"title": "Balloon & Backdrop Decor", "category": "decoration", "price": 4500, "platform": "Amazon", "tags": ["birthday", "wedding"]},
    {"title": "Table Decor Kit", "category": "decoration", "price": 2200, "platform": "Flipkart", "tags": ["corporate", "birthday"]},
    {"title": "Banquet Hall Search Option", "category": "venue", "price": 12000, "platform": "OYO", "tags": ["corporate", "wedding"]},
    {"title": "Small Event Venue Search Option", "category": "venue", "price": 7000, "platform": "OYO", "tags": ["birthday", "casual"]},
]

JEWELRY_CATALOG = [
    {"title": "Minimal Gold-Tone Stud Earrings", "category": "earrings", "price": 699, "platform": "Amazon", "tags": ["elegant", "minimal", "gold"]},
    {"title": "Pearl Drop Earrings", "category": "earrings", "price": 1299, "platform": "Flipkart", "tags": ["elegant", "pearl"]},
    {"title": "Layered Pendant Necklace", "category": "necklace", "price": 1699, "platform": "Amazon", "tags": ["modern", "layered"]},
    {"title": "Oxidized Silver Necklace", "category": "necklace", "price": 899, "platform": "Flipkart", "tags": ["ethnic", "silver", "statement"]},
    {"title": "Classic Bangle Set", "category": "bangles", "price": 1099, "platform": "Amazon", "tags": ["traditional", "gold"]},
    {"title": "Statement Cocktail Ring", "category": "ring", "price": 999, "platform": "Flipkart", "tags": ["party", "statement"]},
]


def attach_link(item: dict) -> dict:
    copied = dict(item)
    query = quote_plus(copied["title"])
    copied["link"] = PLATFORM_BASES[copied["platform"]].format(query=query)
    return copied


def get_catalog(planner: str, keywords: list[str] | None = None) -> list[dict]:
    source = {
        "home": HOME_CATALOG,
        "party": PARTY_CATALOG,
        "jewelry": JEWELRY_CATALOG,
    }[planner]
    keywords = [k.lower() for k in (keywords or []) if k]
    items = []
    for item in source:
        if not keywords or any(keyword in {tag.lower() for tag in item.get("tags", [])} for keyword in keywords):
            items.append(attach_link(item))
    return items or [attach_link(item) for item in source]
