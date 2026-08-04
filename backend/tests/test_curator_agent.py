from app.agents import curator_agent
from app.schemas.coffee import CoffeeShop, CoffeeShopCandidate
from app.schemas.recommendation import CurationResult


def _candidate(name, dist, is_open=None, wifi=False):
    return CoffeeShopCandidate(
        shop=CoffeeShop(id=1, name=name, lat=0.0, lon=0.0, has_wifi=wifi),
        is_open=is_open,
        distance_m=dist,
    )


_CANDIDATES = [_candidate("A", 100), _candidate("B", 200), _candidate("C", 300)]


async def test_curate_separa_destacadas_y_cercanas(monkeypatch):
    async def fake_chat_json(messages, schema, name):
        return {
            "curated": [{"index": 0, "reasoning": "La mejor."}],
            "nearby": [{"index": 2, "reasoning": "Tambien cerca."}],
        }

    monkeypatch.setattr(curator_agent, "chat_json", fake_chat_json)
    result = await curator_agent.curate("cafe cerca", _CANDIDATES)

    assert isinstance(result, CurationResult)
    assert [r.candidate.shop.name for r in result.curated] == ["A"]
    assert [r.candidate.shop.name for r in result.nearby] == ["C"]


async def test_curate_clampa_ambos_grupos(monkeypatch):
    candidates = [_candidate(str(i), i * 100) for i in range(20)]

    async def fake_chat_json(messages, schema, name):
        return {
            "curated": [{"index": i, "reasoning": "x"} for i in range(10)],
            "nearby": [{"index": i, "reasoning": "y"} for i in range(10, 20)],
        }

    monkeypatch.setattr(curator_agent, "chat_json", fake_chat_json)
    result = await curator_agent.curate("q", candidates)
    assert len(result.curated) == curator_agent._CURATED_MAX
    assert len(result.nearby) == curator_agent._NEARBY_MAX


async def test_curate_nearby_no_repite_curadas(monkeypatch):
    async def fake_chat_json(messages, schema, name):
        return {
            "curated": [{"index": 0, "reasoning": "destacada"}],
            "nearby": [{"index": 0, "reasoning": "repetida"}, {"index": 1, "reasoning": "ok"}],
        }

    monkeypatch.setattr(curator_agent, "chat_json", fake_chat_json)
    result = await curator_agent.curate("q", _CANDIDATES)
    assert [r.candidate.shop.name for r in result.curated] == ["A"]
    assert [r.candidate.shop.name for r in result.nearby] == ["B"]


async def test_curate_ignora_indices_invalidos(monkeypatch):
    async def fake_chat_json(messages, schema, name):
        return {
            "curated": [{"index": 99, "reasoning": "no existe"}, {"index": 1, "reasoning": "ok"}],
            "nearby": [],
        }

    monkeypatch.setattr(curator_agent, "chat_json", fake_chat_json)
    result = await curator_agent.curate("q", _CANDIDATES)
    assert [r.candidate.shop.name for r in result.curated] == ["B"]
    assert result.nearby == []


async def test_curate_fallback_si_llm_falla(monkeypatch):
    async def boom(*args, **kwargs):
        raise RuntimeError("LLM caido")

    monkeypatch.setattr(curator_agent, "chat_json", boom)
    result = await curator_agent.curate("q", _CANDIDATES)
    assert len(result.curated) == 3
    assert result.nearby == []
    assert "A" in result.curated[0].reasoning


async def test_curate_fallback_reparte_en_ambos_grupos(monkeypatch):
    candidates = [_candidate(str(i), i * 100) for i in range(12)]

    async def boom(*args, **kwargs):
        raise RuntimeError("LLM caido")

    monkeypatch.setattr(curator_agent, "chat_json", boom)
    result = await curator_agent.curate("q", candidates)
    assert len(result.curated) == curator_agent._CURATED_MAX
    assert len(result.nearby) == curator_agent._NEARBY_MAX


async def test_curate_sin_candidatos():
    result = await curator_agent.curate("q", [])
    assert result.curated == []
    assert result.nearby == []
