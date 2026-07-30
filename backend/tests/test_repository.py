from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.db.base import Base
from app.db.models import CoffeeShop
from app.db.repository import _haversine_m, find_nearby

# Centro de referencia (Puerta del Sol, Madrid)
_LAT, _LON = 40.4168, -3.7038


def test_haversine_m():
    # ~111 m por 0.001 grados de latitud
    dist = _haversine_m(_LAT, _LON, _LAT + 0.001, _LON)
    assert 100 < dist < 125


async def _seed_session():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    Session = async_sessionmaker(engine, expire_on_commit=False)
    async with Session() as session:
        session.add_all(
            [
                CoffeeShop(name="Cerca con wifi", lat=_LAT + 0.002, lon=_LON, has_wifi=True),
                CoffeeShop(name="Cerca sin wifi", lat=_LAT + 0.003, lon=_LON, has_wifi=False),
                CoffeeShop(name="Lejos", lat=_LAT + 0.05, lon=_LON, has_wifi=True),
            ]
        )
        await session.commit()
    return Session


async def test_find_nearby_ordena_y_filtra_radio():
    Session = await _seed_session()
    async with Session() as session:
        results = await find_nearby(session, _LAT, _LON, radius_m=1000)

    nombres = [shop.name for shop, _ in results]
    assert nombres == ["Cerca con wifi", "Cerca sin wifi"]  # "Lejos" fuera de radio, ordenadas
    assert results[0][1] < results[1][1]


async def test_find_nearby_filtra_wifi():
    Session = await _seed_session()
    async with Session() as session:
        results = await find_nearby(session, _LAT, _LON, radius_m=1000, needs_wifi=True)

    nombres = [shop.name for shop, _ in results]
    assert nombres == ["Cerca con wifi"]
