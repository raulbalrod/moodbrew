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


async def test_find_nearby_wifi_es_preferencia_no_filtro():
    Session = await _session_with(
        [
            CoffeeShop(name="Sin wifi", lat=_LAT + 0.001, lon=_LON, has_wifi=False),
            CoffeeShop(name="Con wifi", lat=_LAT + 0.0015, lon=_LON, has_wifi=True),
        ]
    )
    async with Session() as session:
        results = await find_nearby(session, _LAT, _LON, radius_m=1000, needs_wifi=True)

    nombres = [shop.name for shop, _ in results]
    assert nombres == ["Con wifi", "Sin wifi"]


async def _session_with(shops):
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    Session = async_sessionmaker(engine, expire_on_commit=False)
    async with Session() as session:
        session.add_all(shops)
        await session.commit()
    return Session


async def test_find_nearby_proximidad_manda_entre_bandas():
    Session = await _session_with(
        [
            CoffeeShop(name="Generica cerca", lat=_LAT + 0.002, lon=_LON, specialty_score=0),
            CoffeeShop(name="Especialidad lejos", lat=_LAT + 0.005, lon=_LON, specialty_score=4),
        ]
    )
    async with Session() as session:
        results = await find_nearby(session, _LAT, _LON, radius_m=1000)

    assert [shop.name for shop, _ in results][0] == "Generica cerca"


async def test_find_nearby_coffee_shop_primero_en_banda():
    Session = await _session_with(
        [
            CoffeeShop(name="Generico cerca", lat=_LAT + 0.001, lon=_LON, is_coffee_shop=False),
            CoffeeShop(name="Coffee shop", lat=_LAT + 0.0015, lon=_LON, is_coffee_shop=True),
        ]
    )
    async with Session() as session:
        results = await find_nearby(session, _LAT, _LON, radius_m=1000)

    assert [shop.name for shop, _ in results][0] == "Coffee shop"


async def test_find_nearby_coffee_shop_manda_sobre_cercania():
    # coffee_shop pesa mas que cualquier filtro: va primero aunque un generico este mas cerca.
    Session = await _session_with(
        [
            CoffeeShop(name="Generico cercano", lat=_LAT + 0.001, lon=_LON, is_coffee_shop=False),
            CoffeeShop(name="Coffee shop lejano", lat=_LAT + 0.008, lon=_LON, is_coffee_shop=True),
        ]
    )
    async with Session() as session:
        results = await find_nearby(session, _LAT, _LON, radius_m=1000)

    assert [shop.name for shop, _ in results][0] == "Coffee shop lejano"


async def test_find_nearby_especialidad_desempata_misma_banda():
    Session = await _session_with(
        [
            CoffeeShop(name="Generica", lat=_LAT + 0.001, lon=_LON, specialty_score=0),
            CoffeeShop(name="Especialidad", lat=_LAT + 0.0015, lon=_LON, specialty_score=4),
        ]
    )
    async with Session() as session:
        results = await find_nearby(session, _LAT, _LON, radius_m=1000)

    assert [shop.name for shop, _ in results][0] == "Especialidad"
