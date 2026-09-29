# PocketSmart AI

A complete FastAPI + Jinja2 Generative AI budget and recommendation assistant based on the supplied project documentation.

## What is included

- FastAPI backend
- Jinja2 + HTML/CSS/JavaScript frontend
- Gemini multimodal integration for text and optional outfit images
- Home, Party, and Jewelry planners
- Register/login/logout, JWT token endpoint, and session-based protected pages
- SQLite persistence for users and recommendation history
- Mock/simulated catalog adapters for Amazon, Flipkart, IKEA, Swiggy, Zomato, and OYO
- Budget-aware post-processing so displayed recommendation totals stay within the submitted budget
- Responsive UI
- API and service tests
- `.env.example` configuration

## Important implementation choices

The source document contains an architectural inconsistency: its early overview calls the backend Flask, while the later workflow and backend milestones consistently specify FastAPI, Jinja2, and routes such as `/generate-home`, `/generate-party`, and `/generate-jewelry`. This project follows the later FastAPI design because it is the more detailed and repeated implementation direction in the document.

The document also explicitly asks for mock API calls or simulated scraping. Therefore, this project does not pretend to have live Amazon/Flipkart/IKEA/Swiggy/Zomato/OYO partner API access. Instead, it keeps a local simulated catalog and generates platform search links. Replace `catalog_service.py` with approved partner APIs when credentials/contracts are available.

The documentation names Gemini 1.5 Flash Pro. Google’s current Gemini API documentation recommends newer models for new projects, so the application uses an environment-configurable model with `gemini-3.8-flash` as the default. Set `GEMINI_MODEL` to another model available to your API account when needed.

## 1. Create a virtual environment

### Windows PowerShell

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### Windows CMD

```cmd
py -3.11 -m venv .venv
.venv\Scripts\activate
```

### macOS/Linux

```bash
python3.11 -m venv .venv
source .venv/bin/activate
```

## 2. Install dependencies

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

## 3. Configure environment

Copy `.env.example` to `.env`.

For real Gemini calls, add your Gemini Developer API key:

```env
GEMINI_API_KEY=your_key_here
MOCK_AI=false
GEMINI_MODEL=gemini-3.8-flash
```

For a completely local demo without an API key:

```env
MOCK_AI=true
```

The app will then use the deterministic recommendation engine while preserving the same API/UI flow.

## 4. Run

```bash
python run.py
```

Open:

- http://127.0.0.1:8000/
- API docs: http://127.0.0.1:8000/docs

## 5. Test

```bash
pytest -q
```

## Main API routes

- `POST /api/auth/register`
- `POST /api/auth/login`
- `POST /api/auth/logout`
- `POST /api/auth/token`
- `GET /api/session-info`
- `GET /api/session-data`
- `POST /api/generate-home`
- `POST /api/generate-party`
- `POST /api/generate-jewelry`
- `POST /api/recommendations-details`
- `GET /api/history`
- `DELETE /api/history/{history_id}`
- `GET /health`

## Notes for production

This is a complete educational/project implementation, not a production financial system. For production deployment, add HTTPS, secure secret management, CSRF protection for cookie-authenticated state-changing requests, rate limiting, centralized logging, database migrations, and approved partner/product APIs.


## Troubleshooting

### `pip` is not recognized on Windows
Use the active virtual environment and call pip through Python:

```powershell
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

### `SettingsError` for `cors_origins`
`CORS_ORIGINS` accepts either a JSON list or comma-separated values. The recommended `.env` form is:

```env
CORS_ORIGINS=["http://127.0.0.1:8000","http://localhost:8000"]
```

### Jewelry image upload
JPG/JPEG, PNG, and WEBP files up to `MAX_IMAGE_MB` are accepted and validated using Pillow before Gemini receives the image.

### `Local fallback`
The UI shows `Local fallback` when `MOCK_AI=true`, the Gemini key is missing, or the Gemini request/validation fails. The backend logs the underlying Gemini error in the terminal so it can be diagnosed without exposing the API key in the browser.
