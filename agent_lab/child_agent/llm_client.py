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
REASONING_EFFORTS: list[Optional[str]] = ["high", "xhigh", "medium", None]


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

    def _create_response(self, client: Any, model_name: str, system_prompt: str, user_prompt: str) -> Any:
        for effort in REASONING_EFFORTS:
            kwargs: dict[str, Any] = {
                "model": model_name,
                "input": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
            }
            if effort is not None:
                kwargs["reasoning"] = {"effort": effort}
            try:
                return client.responses.create(**kwargs)
            except Exception as exc:
                body = str(exc)
                # Try next effort level if this model rejects current reasoning effort.
                if "reasoning.effort" in body and "unsupported_value" in body:
                    continue
                raise
        return None

    def generate_patch(self, system_prompt: str, user_prompt: str) -> Optional[str]:
        client = self._ensure_client()
        if client is None:
            return None

        for model_name in self._candidate_models():
            try:
                response = self._create_response(client, model_name, system_prompt, user_prompt)
                if response is None:
                    continue
                text = getattr(response, "output_text", "")
                return text.strip() if text else None
            except Exception as exc:  # fallback on model-not-found only
                body = str(exc)
                if "model_not_found" in body or "does not exist" in body:
                    continue
                raise

        # If all model names fail because unavailable, degrade gracefully.
        return None
