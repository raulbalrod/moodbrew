import os

import httpx
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

BACKEND_URL = os.environ.get("BACKEND_URL", "http://localhost:8000")
REQUEST_TIMEOUT = float(os.environ.get("REQUEST_TIMEOUT", "60"))

_OPEN_BADGE = {True: "🟢 Abierta ahora", False: "🔴 Cerrada ahora"}

st.set_page_config(page_title="MoodBrew", page_icon="☕", layout="centered")


def _badges(candidate: dict, shop: dict) -> str:
    parts = [_OPEN_BADGE.get(candidate.get("is_open"), "⚪ Horario desconocido")]
    distance = candidate.get("distance_m")
    if distance is not None:
        parts.append(f"📍 a unos {round(distance)} m")
    if shop.get("has_wifi"):
        parts.append("📶 Wifi")
    return " · ".join(parts)


def _fetch_recommendations(text: str) -> dict:
    response = httpx.post(
        f"{BACKEND_URL}/api/recommendations",
        json={"text": text},
        timeout=REQUEST_TIMEOUT,
    )
    response.raise_for_status()
    return response.json()


def _render(data: dict) -> None:
    recommendations = data.get("recommendations", [])
    if not recommendations:
        st.warning(data.get("message") or "No he encontrado cafeterías para esa búsqueda.")
        return

    radius = data.get("search_radius_m")
    resumen = f"{len(recommendations)} recomendaciones"
    if radius:
        resumen += f" · radio de búsqueda ~{radius} m"
    st.success(resumen)

    for rec in recommendations:
        shop = rec["candidate"]["shop"]
        with st.container(border=True):
            st.markdown(f"#### {shop['name']}")
            st.caption(_badges(rec["candidate"], shop))
            if shop.get("address"):
                st.caption(f"📌 {shop['address']}")
            st.write(rec["reasoning"])


st.markdown("# ☕ MoodBrew")
st.markdown(
    "Recomendador de **cafeterías de especialidad**. Cuéntame dónde estás y qué te apetece."
)

with st.form("buscar"):
    query = st.text_input(
        "¿Qué buscas?",
        placeholder="p.ej. estoy en la Giralda de Sevilla, un café tranquilo con wifi",
    )
    submitted = st.form_submit_button("Recomiéndame ☕", type="primary", use_container_width=True)

if submitted:
    if not query.strip():
        st.info("Escribe primero qué te apetece y dónde estás.")
    else:
        try:
            with st.spinner("Buscando cafeterías de especialidad…"):
                data = _fetch_recommendations(query)
        except Exception as exc:
            st.error(f"No se pudo conectar con el servicio ({BACKEND_URL}). Detalle: {exc}")
        else:
            _render(data)

st.divider()
st.caption("Datos de OpenStreetMap vía Geoapify · MoodBrew MVP")
