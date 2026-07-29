# MoodBrew

Recomendador de cafeterias de especialidad basado en un pipeline multiagente
secuencial (intencion → busqueda/validacion → curacion).

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
