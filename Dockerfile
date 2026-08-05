# ---------- base ----------
FROM python:3.13-slim AS base
WORKDIR /srv
COPY backend/pyproject.toml ./backend/pyproject.toml
COPY backend/app ./backend/app
COPY backend/scripts ./backend/scripts

# ---------- dev ----------
FROM base AS dev
RUN pip install --no-cache-dir -e "./backend[dev]"
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000} --reload --reload-dir /srv/backend"]

# ---------- prod ----------
FROM base AS prod
RUN pip install --no-cache-dir ./backend
EXPOSE 8000
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
