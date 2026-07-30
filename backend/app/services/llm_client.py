import json
from typing import Any

import httpx

from app.config import settings

LLM_TIMEOUT_SECONDS = 30.0


def _json_schema_format(schema: dict[str, Any], name: str) -> dict[str, Any]:
    """Construye el `response_format` de salida estructurada estricta de Cerebras."""
    return {
        "type": "json_schema",
        "json_schema": {"name": name, "strict": True, "schema": schema},
    }


def _build_payload(
    messages: list[dict], response_format: dict[str, Any] | None = None
) -> dict[str, Any]:
    payload: dict[str, Any] = {"model": settings.llm_model, "messages": messages}
    if response_format is not None:
        payload["response_format"] = response_format
    return payload


async def _post(payload: dict[str, Any]) -> str:
    async with httpx.AsyncClient(timeout=LLM_TIMEOUT_SECONDS) as client:
        response = await client.post(
            f"{settings.llm_base_url}/chat/completions",
            headers={"Authorization": f"Bearer {settings.llm_api_key}"},
            json=payload,
        )
    response.raise_for_status()
    return response.json()["choices"][0]["message"]["content"]


async def chat(messages: list[dict]) -> str:
    """Chat completion de texto libre (usado por el Agente 3)."""
    return await _post(_build_payload(messages))


async def chat_json(
    messages: list[dict], schema: dict[str, Any], schema_name: str = "response"
) -> dict[str, Any]:
    """Chat completion con salida estructurada JSON estricta (usado por el Agente 1)."""
    content = await _post(_build_payload(messages, _json_schema_format(schema, schema_name)))
    return json.loads(content)
