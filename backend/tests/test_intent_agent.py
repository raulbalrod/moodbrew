from app.agents import intent_agent
from app.schemas.intent import IntentProfile


async def test_parse_intent_happy(monkeypatch):
    async def fake_chat_json(messages, schema, name):
        return {"area": "Malasana", "needs_wifi": True, "open_now": True}

    monkeypatch.setattr(intent_agent, "chat_json", fake_chat_json)
    result = await intent_agent.parse_intent("cafe con wifi en Malasana abierto ahora")

    assert isinstance(result, IntentProfile)
    assert result.area == "Malasana"
    assert result.needs_wifi is True
    assert result.open_now is True
    assert result.radius_m == 1000


async def test_parse_intent_fallback(monkeypatch):
    async def boom(*args, **kwargs):
        raise RuntimeError("LLM caido")

    monkeypatch.setattr(intent_agent, "chat_json", boom)
    result = await intent_agent.parse_intent("lo que sea")

    assert isinstance(result, IntentProfile)
    assert result.area is None
    assert result.needs_wifi is False
