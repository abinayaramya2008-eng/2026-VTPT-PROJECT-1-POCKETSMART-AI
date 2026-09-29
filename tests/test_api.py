from io import BytesIO

from fastapi.testclient import TestClient
from PIL import Image

from app.main import app


def test_health():
    with TestClient(app) as client:
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "ok"


def register_and_get_client():
    client = TestClient(app)
    client.__enter__()
    response = client.post("/api/auth/register", json={"email": "test@example.com", "password": "password123", "full_name": "Test User"})
    assert response.status_code == 201
    return client


def test_register_login_and_home_planner():
    with TestClient(app) as client:
        response = client.post("/api/auth/register", json={"email": "home@example.com", "password": "password123", "full_name": "Home User"})
        assert response.status_code == 201
        body = {
            "budget": 30000,
            "style": "modern",
            "city": "Pudukkottai",
            "notes": "simple setup",
            "rooms": [{"room_type": "Living Room", "lights": 2, "ceiling_fans": 1, "tables": 1, "chairs": 4, "decor_items": 2}],
        }
        result = client.post("/api/generate-home", json=body)
        assert result.status_code == 200
        data = result.json()
        assert data["planner"] == "home"
        assert data["estimated_total"] <= data["budget"]

        history = client.get("/api/history")
        assert history.status_code == 200
        assert len(history.json()) == 1


def test_party_planner():
    with TestClient(app) as client:
        response = client.post("/api/auth/register", json={"email": "party@example.com", "password": "password123"})
        assert response.status_code == 201
        body = {
            "budget": 25000,
            "guests": 30,
            "event_type": "birthday",
            "city": "Chennai",
            "venue_preference": "small hall",
            "food_preference": "mixed",
            "accommodation_needed": False,
            "notes": "",
        }
        result = client.post("/api/generate-party", json=body)
        assert result.status_code == 200
        assert result.json()["estimated_total"] <= 25000


def test_jewelry_planner():
    with TestClient(app) as client:
        response = client.post("/api/auth/register", json={"email": "jewelry@example.com", "password": "password123"})
        assert response.status_code == 201
        result = client.post("/api/generate-jewelry", data={"budget": "5000", "occasion": "festival", "style": "elegant"})
        assert result.status_code == 200
        data = result.json()
        assert data["planner"] == "jewelry"
        assert data["estimated_total"] <= 5000


def test_pages_and_auth_guard():
    with TestClient(app) as client:
        for path in ["/", "/login", "/register", "/planner/home", "/planner/party", "/planner/jewelry", "/recommendations", "/history", "/testimonials"]:
            response = client.get(path)
            assert response.status_code == 200
        protected = client.post("/api/generate-party", json={"budget": 10000, "guests": 10, "event_type": "birthday", "city": "India", "venue_preference": "flexible", "food_preference": "mixed", "accommodation_needed": False, "notes": ""})
        assert protected.status_code == 401


def test_jewelry_jpeg_upload():
    with TestClient(app) as client:
        response = client.post(
            "/api/auth/register",
            json={"email": "jpeg@example.com", "password": "password123"},
        )
        assert response.status_code == 201

        image = Image.new("RGB", (32, 32), "yellow")
        buffer = BytesIO()
        image.save(buffer, format="JPEG")
        buffer.seek(0)

        result = client.post(
            "/api/generate-jewelry",
            data={"budget": "5000", "occasion": "wedding", "style": "modern", "outfit_color": "yellow"},
            files={"outfit_image": ("outfit.jpeg", buffer.getvalue(), "image/jpeg")},
        )
        assert result.status_code == 200
        assert result.json()["planner"] == "jewelry"
