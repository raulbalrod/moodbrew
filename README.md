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

## Arquitectura

Dos servicios: **frontend Next.js @ Vercel** · **API FastAPI @ Render** · **DB Postgres
@ Neon**. El navegador consume la API por HTTPS (`NEXT_PUBLIC_API_BASE_URL`).

```text
moodbrew/
├── backend/                   # API FastAPI (pipeline multiagente)
│   ├── app/
│   │   ├── main.py            # FastAPI + CORS + rate limit; crea el schema en el lifespan
│   │   ├── config/            # Settings via pydantic-settings
│   │   ├── api/               # Routers (/api/health, /api/recommendations)
│   │   ├── schemas/           # Modelos Pydantic de entrada/salida
│   │   ├── db/                # Base declarativa y sesion async (SQLAlchemy 2.0)
│   │   ├── agents/            # intent → search → curator
│   │   └── services/          # Clientes LLM (Cerebras) y mapas (Geoapify)
│   └── tests/
├── frontend/                  # Next.js 16 + React 19 + Tailwind v4 + shadcn/ui (pnpm)
├── docker/
│   ├── docker-compose.yml     # API + postgres
│   └── docker-compose.dev.yml # override con reload y volumenes
├── Dockerfile                 # imagen de la API (uvicorn)
└── Makefile
```

## Puesta en marcha

Backend (Docker):

```bash
cp backend/.env.example backend/.env   # rellena claves y credenciales
make dev                               # API FastAPI en :8000 con reload (+ postgres)
make test                              # corre los tests en el contenedor
curl http://localhost:8000/api/health  # {"status":"ok",...}
```

Frontend (pnpm, fuera de Docker):

```bash
cd frontend
cp .env.example .env.local             # NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
pnpm install
pnpm dev                               # http://localhost:3000
```
