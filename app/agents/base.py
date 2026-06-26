import uuid
from google import genai
from google.genai import types
from typing import Optional, Type, TypeVar
from pydantic import BaseModel
from app.configs.common import get_settings
from app.db.session import session_scope
from app.db.models.llm_usage import LLMUsage

T = TypeVar("T", bound=BaseModel)

# Gemini 2.0 Flash pricing (per 1M tokens)
_PRICE_INPUT_PER_M = 0.075
_PRICE_OUTPUT_PER_M = 0.30


class BaseAgent:
    """All AI agents extend this. Gemini call + billing auto-tracked."""

    agent_name: str = "base_agent"

    def __init__(self):
        settings = get_settings()
        self.client = genai.Client(api_key=settings.GEMINI_API_KEY)
        self.model = settings.GEMINI_MODEL

    def _run(
        self,
        prompt: str,
        response_schema: Type[T],
        files: Optional[list] = None,
        reference_id: Optional[str] = None,
        reference_type: Optional[str] = None,
    ) -> T:
        contents = files + [prompt] if files else [prompt]

        response = self.client.models.generate_content(
            model=self.model,
            contents=contents,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=response_schema,
            ),
        )

        self._track_usage(response, reference_id, reference_type)
        return response_schema.model_validate_json(response.text)

    def _track_usage(self, response, reference_id: Optional[str], reference_type: Optional[str]):
        try:
            meta = response.usage_metadata
            input_tokens = meta.prompt_token_count or 0
            output_tokens = meta.candidates_token_count or 0
            total_tokens = meta.total_token_count or 0
            cost = (input_tokens / 1_000_000 * _PRICE_INPUT_PER_M) + \
                   (output_tokens / 1_000_000 * _PRICE_OUTPUT_PER_M)

            with session_scope() as db:
                db.add(LLMUsage(
                    id=uuid.uuid4(),
                    agent_name=self.agent_name,
                    model_name=self.model,
                    input_tokens=input_tokens,
                    output_tokens=output_tokens,
                    total_tokens=total_tokens,
                    cost_usd=round(cost, 8),
                    reference_id=str(reference_id) if reference_id else None,
                    reference_type=reference_type,
                ))
        except Exception:
            pass  # billing failure should never break the main flow
