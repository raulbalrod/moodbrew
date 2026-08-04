from app import pipeline
from app.schemas.coffee import CoffeeShop, CoffeeShopCandidate, SearchResult
from app.schemas.intent import IntentProfile
from app.schemas.recommendation import CurationResult, Recommendation


def _candidate(name):
    return CoffeeShopCandidate(shop=CoffeeShop(id=1, name=name, lat=0.0, lon=0.0), distance_m=100.0)


async def test_pipeline_happy(monkeypatch):
    async def fake_parse_intent(text):
        return IntentProfile(area="Alfalfa", radius_m=1500)

    async def fake_search(session, intent):
        return SearchResult(candidates=[_candidate("Ozik"), _candidate("Nolan")], radius_m=2500)

    async def fake_curate(text, candidates):
        return CurationResult(
            curated=[Recommendation(candidate=candidates[0], reasoning="La mejor por cercania.")],
            nearby=[Recommendation(candidate=candidates[1], reasoning="Tambien cerca.")],
        )

    monkeypatch.setattr(pipeline, "parse_intent", fake_parse_intent)
    monkeypatch.setattr(pipeline, "search", fake_search)
    monkeypatch.setattr(pipeline, "curate", fake_curate)

    response = await pipeline.run_pipeline(None, "cafe en Alfalfa")

    assert response.query == "cafe en Alfalfa"
    assert [r.candidate.shop.name for r in response.recommendations] == ["Ozik"]
    assert [r.candidate.shop.name for r in response.nearby] == ["Nolan"]
    assert response.search_radius_m == 2500
    assert response.message is None


async def test_pipeline_sin_resultados_devuelve_mensaje(monkeypatch):
    async def fake_parse_intent(text):
        return IntentProfile(area="Reikiavik")

    async def fake_search(session, intent):
        return SearchResult(candidates=[], radius_m=5500)

    async def fake_curate(text, candidates):  # no deberia llamarse
        raise AssertionError("curate no debe invocarse sin candidatos")

    monkeypatch.setattr(pipeline, "parse_intent", fake_parse_intent)
    monkeypatch.setattr(pipeline, "search", fake_search)
    monkeypatch.setattr(pipeline, "curate", fake_curate)

    response = await pipeline.run_pipeline(None, "cafe en Reikiavik")

    assert response.recommendations == []
    assert response.message is not None
    assert "encontrado" in response.message.lower()
