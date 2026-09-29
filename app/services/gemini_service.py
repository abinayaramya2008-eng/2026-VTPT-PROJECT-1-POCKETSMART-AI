import json
import logging
import re
from typing import Any

from pydantic import ValidationError

from app.config import get_settings
from app.prompts import SYSTEM_INSTRUCTION, build_prompt
from app.schemas import RecommendationResponse

logger = logging.getLogger(__name__)


class GeminiService:
    def __init__(self) -> None:
        self.settings = get_settings()
        self._client = None

    def _get_client(self):
        if not self.settings.gemini_api_key:
            raise RuntimeError("GEMINI_API_KEY is not configured")
        try:
            from google import genai
        except ImportError as exc:
            raise RuntimeError("google-genai is not installed. Run: python -m pip install -r requirements.txt") from exc
        if self._client is None:
            self._client = genai.Client(api_key=self.settings.gemini_api_key)
        return self._client

    def generate(
        self,
        planner: str,
        payload: dict[str, Any],
        catalog: list[dict],
        image_bytes: bytes | None = None,
        image_mime_type: str | None = None,
    ) -> RecommendationResponse:
        client = self._get_client()
        image_note = (
            "The uploaded outfit image is available. Use it only for broad color and style coordination; do not identify the person."
            if image_bytes
            else ""
        )
        prompt = build_prompt(planner, payload, catalog, image_note=image_note)
        contents: list[Any] = [prompt]

        from google.genai import types

        if image_bytes and image_mime_type:
            contents.append(types.Part.from_bytes(data=image_bytes, mime_type=image_mime_type))

        response = client.models.generate_content(
            model=self.settings.gemini_model,
            contents=contents,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_INSTRUCTION,
                temperature=0.35,
                max_output_tokens=3500,
                response_mime_type="application/json",
                response_schema=RecommendationResponse,
            ),
        )

        raw = response.text or ""
        data = self._parse_json(raw)
        try:
            parsed = RecommendationResponse.model_validate(data)
        except ValidationError as exc:
            logger.exception("Gemini returned an invalid PocketSmart response: %s", exc)
            raise RuntimeError("Gemini returned data that did not match the PocketSmart response schema") from exc

        parsed.ai_generated = True
        return parsed

    @staticmethod
    def _parse_json(raw: str) -> dict:
        candidate = raw.strip()
        if candidate.startswith("```"):
            match = re.match(r"^```(?:json)?\s*(.*?)\s*```$", candidate, flags=re.DOTALL | re.IGNORECASE)
            if match:
                candidate = match.group(1).strip()

        try:
            data = json.loads(candidate)
        except json.JSONDecodeError as exc:
            raise RuntimeError("Gemini did not return valid JSON") from exc

        if not isinstance(data, dict):
            raise RuntimeError("Gemini JSON response was not an object")
        return data
