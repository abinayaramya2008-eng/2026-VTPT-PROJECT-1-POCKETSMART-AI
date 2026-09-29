from pathlib import Path

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

BASE_DIR = Path(__file__).resolve().parents[2]
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))
router = APIRouter(tags=["pages"])


def render(request: Request, name: str, **context):
    return templates.TemplateResponse(request=request, name=name, context={"request": request, **context})


@router.get("/", response_class=HTMLResponse)
def home(request: Request):
    return render(request, "index.html", title="PocketSmart AI")


@router.get("/login", response_class=HTMLResponse)
def login(request: Request):
    return render(request, "login.html", title="Login")


@router.get("/register", response_class=HTMLResponse)
def register(request: Request):
    return render(request, "register.html", title="Create account")


@router.get("/dashboard", response_class=HTMLResponse)
def dashboard(request: Request):
    return render(request, "dashboard.html", title="Dashboard")


@router.get("/planner/home", response_class=HTMLResponse)
def home_planner(request: Request):
    return render(request, "home_planner.html", title="Home Budget Planner")


@router.get("/planner/party", response_class=HTMLResponse)
def party_planner(request: Request):
    return render(request, "party_planner.html", title="Party Budget Planner")


@router.get("/planner/jewelry", response_class=HTMLResponse)
def jewelry_planner(request: Request):
    return render(request, "jewelry_planner.html", title="Jewelry Budget Planner")


@router.get("/recommendations", response_class=HTMLResponse)
def recommendations(request: Request):
    return render(request, "recommendations.html", title="Recommendations")


@router.get("/history", response_class=HTMLResponse)
def history_page(request: Request):
    return render(request, "history.html", title="Recommendation History")


@router.get("/testimonials", response_class=HTMLResponse)
def testimonials(request: Request):
    return render(request, "testimonials.html", title="Testimonials")
