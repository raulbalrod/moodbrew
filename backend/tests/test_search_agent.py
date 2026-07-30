from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.agents import search_agent
from app.db.base import Base
from app.db.models import CoffeeShop
from app.schemas.intent import IntentProfile

_LAT, _LON = 40.4168, -3.7038


async def _session_with(shops):
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    Session = async_sessionmaker(engine, expire_on_commit=False)
    async with Session() as session:
        session.add_all(shops)
        await session.commit()
    return Session


def _patch_maps(monkeypatch, opening_hours="24/7", is_open=True):
    async def fake_geocode(text):
        return (_LAT, _LON)

    async def fake_fetch(external_id):
        return opening_hours

    async def fake_ingest(session, lat, lon, radius_m=1500, limit=50):
        return 0

    monkeypatch.setattr(search_agent, "geocode", fake_geocode)
    monkeypatch.setattr(search_agent, "fetch_opening_hours", fake_fetch)
    monkeypatch.setattr(search_agent, "is_open_now", lambda oh, now=None: is_open)
    monkeypatch.setattr(search_agent, "ingest_area", fake_ingest)


async def test_search_devuelve_candidatos_ordenados(monkeypatch):
    _patch_maps(monkeypatch)
    Session = await _session_with(
        [
            CoffeeShop(name="A", lat=_LAT + 0.001, lon=_LON, external_id="a"),
            CoffeeShop(name="B", lat=_LAT + 0.003, lon=_LON, external_id="b"),
        ]
    )
    async with Session() as session:
        result = await search_agent.search(session, IntentProfile(area="Centro", radius_m=1500))

    assert [c.shop.name for c in result.candidates] == ["A", "B"]
    assert result.candidates[0].distance_m < result.candidates[1].distance_m
    assert result.radius_m == 1500


async def test_radio_progresivo_amplia_hasta_encontrar(monkeypatch):
    _patch_maps(monkeypatch)
    Session = await _session_with(
        [CoffeeShop(name="Lejana", lat=_LAT + 0.018, lon=_LON, external_id="x")]
    )
    async with Session() as session:
        result = await search_agent.search(session, IntentProfile(area="Centro", radius_m=1500))

    assert len(result.candidates) == 1
    assert result.radius_m > 1500 


async def test_sin_area_devuelve_vacio(monkeypatch):
    _patch_maps(monkeypatch)
    Session = await _session_with([CoffeeShop(name="A", lat=_LAT, lon=_LON, external_id="a")])
    async with Session() as session:
        result = await search_agent.search(session, IntentProfile(area=None))

    assert result.candidates == []


async def test_autoseed_en_cache_miss(monkeypatch):
    _patch_maps(monkeypatch)
    Session = await _session_with([])

    async def fake_ingest(session, lat, lon, radius_m=1500, limit=50):
        session.add(CoffeeShop(name="Nueva", lat=_LAT + 0.001, lon=_LON, external_id="n"))
        await session.commit()
        return 1

    monkeypatch.setattr(search_agent, "ingest_area", fake_ingest)
    async with Session() as session:
        result = await search_agent.search(session, IntentProfile(area="Centro", radius_m=1500))

    assert [c.shop.name for c in result.candidates] == ["Nueva"]


async def test_open_now_descarta_cerrados(monkeypatch):
    _patch_maps(monkeypatch, is_open=False)
    Session = await _session_with(
        [CoffeeShop(name="Cerrada", lat=_LAT + 0.001, lon=_LON, external_id="a")]
    )
    async with Session() as session:
        result = await search_agent.search(
            session, IntentProfile(area="Centro", open_now=True, radius_m=1500)
        )

    assert result.candidates == []
