# ---------- base ----------
FROM python:3.13-slim AS base
WORKDIR /app
COPY pyproject.toml .
COPY app.py .

# ---------- dev ----------
FROM base AS dev
RUN pip install --no-cache-dir -e .
CMD ["streamlit", "run", "app.py", "--server.address=0.0.0.0", "--server.port=8501", "--server.headless=true"]

# ---------- prod ----------
FROM base AS prod
RUN pip install --no-cache-dir .
EXPOSE 8501
CMD ["streamlit", "run", "app.py", "--server.address=0.0.0.0", "--server.port=8501", "--server.headless=true"]
