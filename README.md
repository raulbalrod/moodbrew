# MoodBrew

Recomendador de cafeterias de especialidad basado en un pipeline multiagente
secuencial (intencion → busqueda/validacion → curacion).

## Limitaciones conocidas (MVP)

Los datos provienen de OpenStreetMap (via Geoapify), que **no incluye ratings ni
reseñas**. Por eso:

- Se filtra por la categoria `catering.cafe.coffee_shop` (mejor proxy objetivo de
  "especialidad") y se excluyen cadenas comerciales (detectadas por el tag OSM
  `brand`/`brand:wikidata`). Funciona bien en zonas urbanas bien mapeadas; en
  pueblos con OSM pobre puede no encontrar nada.
- Sin ratings de usuarios, la calidad se aproxima con un **`specialty_score`**
  heuristico derivado de señales OSM (categoria `coffee_shop`, "especialidad/
  roasters" en el nombre, web y redes propias, notoriedad en Wikidata, riqueza y
  frescura de los datos). El ranking combina ese score con la distancia, y el
  agente curador afina la eleccion segun la peticion (terraza, wifi, accesible...).
  No equivale a las reseñas de Google, pero ya no es "solo por cercania".

Igualar la calidad de Google requeriria una fuente con ratings de usuarios (Google
Places / Foursquare, ambas de pago) o un directorio de especialidad curado. Queda
como trabajo futuro (fase de value-add).

## Estructura

```text
moodbrew/
├── backend/
│   ├── app/
│   │   ├── main.py            # Inicializa FastAPI y registra rutas (/api)
│   │   ├── config/            # Settings via pydantic-settings
│   │   ├── api/               # Routers (health, y futuros endpoints)
│   │   ├── schemas/           # Modelos Pydantic de entrada/salida
│   │   ├── db/                # Base declarativa y sesion async (SQLAlchemy 2.0)
│   │   ├── agents/            # Agentes 1, 2 y 3 (pendiente)
│   │   └── services/          # Clientes LLM y Google Maps (pendiente)
│   ├── tests/
│   ├── Dockerfile
│   └── pyproject.toml
├── docker/
│   ├── docker-compose.yml     # backend + postgres
│   └── docker-compose.dev.yml # override con reload y volumenes
└── Makefile
```

## Puesta en marcha

```bash
cp backend/.env.example backend/.env   # rellena claves y credenciales
make dev                               # levanta backend + postgres con reload
make test                              # corre los tests en el contenedor
```

Comprobacion rapida:

```bash
curl http://localhost:8000/api/health
# {"status":"ok","app_name":"moodbrew","environment":"dev"}
```
