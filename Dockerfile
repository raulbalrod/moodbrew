# ---------- base ----------
FROM python:3.13-slim AS base
WORKDIR /srv
COPY backend/pyproject.toml ./backend/pyproject.toml
COPY backend/app ./backend/app
COPY backend/scripts ./backend/scripts

# ---------- dev ----------
FROM base AS dev
RUN pip install --no-cache-dir -e "./backend[dev]" streamlit==1.60.0 python-dotenv==1.2.2
COPY frontend/streamlit_app.py ./streamlit_app.py
COPY frontend/.streamlit ./.streamlit
CMD ["sh", "-c", "streamlit run streamlit_app.py --server.address=0.0.0.0 --server.port=${PORT:-8501} --server.headless=true --server.runOnSave=true"]

# ---------- prod ----------
FROM base AS prod
RUN pip install --no-cache-dir ./backend streamlit==1.60.0 python-dotenv==1.2.2
COPY frontend/streamlit_app.py ./streamlit_app.py
COPY frontend/.streamlit ./.streamlit
EXPOSE 8501
CMD ["sh", "-c", "streamlit run streamlit_app.py --server.address=0.0.0.0 --server.port=${PORT:-8501} --server.headless=true"]
