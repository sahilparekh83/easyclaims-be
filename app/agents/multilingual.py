from pydantic import BaseModel
from .base import BaseAgent
from .prompts import MULTILINGUAL


class TranslationResult(BaseModel):
    translated_text: str
    language: str


class MultilingualAgent(BaseAgent):
    agent_name = "multilingual"

    def translate(self, text: str, target_language: str = "Hindi") -> TranslationResult:
        prompt = MULTILINGUAL.format(text=text, target_language=target_language)
        return self._run(
            prompt=prompt,
            response_schema=TranslationResult,
        )
