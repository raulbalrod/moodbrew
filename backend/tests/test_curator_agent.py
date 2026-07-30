from app.agents import curator_agent
from app.schemas.coffee import CoffeeShop, CoffeeShopCandidate
from app.schemas.recommendation import Recommendation


def _candidate(name, dist, is_open=None, wifi=False):
    return CoffeeShopCandidate(
        shop=CoffeeShop(id=1, name=name, lat=0.0, lon=0.0, has_wifi=wifi),
        is_open=is_open,
        distance_m=dist,
    )


_CANDIDATES = [_candidate("A", 100), _candidate("B", 200), _candidate("C", 300)]


async def test_curate_elige_y_razona(monkeypatch):
    async def fake_chat_json(messages, schema, name):
        return {"selections": [{"index": 0, "reasoning": "La mas cercana."},
                               {"index": 2, "reasoning": "Buena alternativa."}]}

    monkeypatch.setattr(curator_agent, "chat_json", fake_chat_json)
    recs = await curator_agent.curate("cafe cerca", _CANDIDATES)

    assert len(recs) == 2
    assert all(isinstance(r, Recommendation) for r in recs)
    assert recs[0].candidate.shop.name == "A"
    assert recs[1].candidate.shop.name == "C"


async def test_curate_clampa_a_3(monkeypatch):
    async def fake_chat_json(messages, schema, name):
        return {"selections": [{"index": i, "reasoning": "x"} for i in range(3)] + [{"index": 0, "reasoning": "extra"}]}

    monkeypatch.setattr(curator_agent, "chat_json", fake_chat_json)
    recs = await curator_agent.curate("q", _CANDIDATES)
    assert len(recs) == 3


async def test_curate_ignora_indices_invalidos(monkeypatch):
    async def fake_chat_json(messages, schema, name):
        return {"selections": [{"index": 99, "reasoning": "no existe"}, {"index": 1, "reasoning": "ok"}]}

    monkeypatch.setattr(curator_agent, "chat_json", fake_chat_json)
    recs = await curator_agent.curate("q", _CANDIDATES)
    assert len(recs) == 1
    assert recs[0].candidate.shop.name == "B"


async def test_curate_fallback_si_llm_falla(monkeypatch):
    async def boom(*args, **kwargs):
        raise RuntimeError("LLM caido")

    monkeypatch.setattr(curator_agent, "chat_json", boom)
    recs = await curator_agent.curate("q", _CANDIDATES)
    assert len(recs) == 3
    assert "A" in recs[0].reasoning


async def test_curate_sin_candidatos():
    recs = await curator_agent.curate("q", [])
    assert recs == []
