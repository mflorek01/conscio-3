from __future__ import annotations

import importlib
import importlib.util
import os
from typing import Any, Optional

DEFAULT_MODEL = "gpt-5.2-chat-latest"
MODEL_FALLBACKS = [
    DEFAULT_MODEL,
    "gpt-5.2",
    "gpt-5",
    "gpt-4.1",
]


class LLMClient:
    def __init__(self, model: str = DEFAULT_MODEL) -> None:
        api_key = os.environ.get("OPENAI_API_KEY")
        has_openai = importlib.util.find_spec("openai") is not None
        self._enabled = bool(api_key) and has_openai
        self._api_key = api_key
        self._client: Any = None
        self._model = model

    @property
    def enabled(self) -> bool:
        return self._enabled

    def _ensure_client(self) -> Any:
        if self._client is not None:
            return self._client
        if not self._enabled:
            return None
        openai_module = importlib.import_module("openai")
        self._client = openai_module.OpenAI(api_key=self._api_key)
        return self._client

    def _candidate_models(self) -> list[str]:
        models = [self._model]
        models.extend(m for m in MODEL_FALLBACKS if m not in models)
        return models

    def generate_patch(self, system_prompt: str, user_prompt: str) -> Optional[str]:
        client = self._ensure_client()
        if client is None:
            return None

        for model_name in self._candidate_models():
            try:
                response = client.responses.create(
                    model=model_name,
                    reasoning={"effort": "high"},
                    input=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                )
                text = getattr(response, "output_text", "")
                return text.strip() if text else None
            except Exception as exc:  # fallback on model-not-found only
                body = str(exc)
                if "model_not_found" in body or "does not exist" in body:
                    continue
                raise

        # If all model names fail because unavailable, degrade gracefully.
        return None
