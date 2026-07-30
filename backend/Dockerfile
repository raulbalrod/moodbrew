# ---------- base ----------
FROM python:3.13-slim AS base
WORKDIR /code
COPY pyproject.toml .

# ---------- dev ----------
FROM base AS dev
RUN pip install --no-cache-dir -e ".[dev]"
COPY . .
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

# ---------- prod ----------
FROM base AS prod
RUN pip install --no-cache-dir .
COPY app ./app
COPY scripts ./scripts
EXPOSE 8000
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
