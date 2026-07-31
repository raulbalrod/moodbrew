import os
import time

import httpx
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

BACKEND_URL = os.environ.get("BACKEND_URL", "http://localhost:8000")
REQUEST_TIMEOUT = float(os.environ.get("REQUEST_TIMEOUT", "90"))

_WAKEUP_STATUS = {502, 503, 504}
_MAX_ATTEMPTS = 3
_RETRY_BACKOFF_S = 3.0

_OPEN_BADGE = {True: "🟢 Abierta ahora", False: "🔴 Cerrada ahora"}

_EXAMPLES = [
    "Café tranquilo con wifi en Ixelles, Bruselas",
    "Un espresso de especialidad cerca de la Giralda, Sevilla",
    "Un flat white abierto ahora en el Born, Barcelona",
]

st.set_page_config(page_title="MoodBrew", page_icon="☕", layout="centered")


def _badges(candidate: dict, shop: dict) -> str:
    parts = [_OPEN_BADGE.get(candidate.get("is_open"), "⚪ Horario desconocido")]
    distance = candidate.get("distance_m")
    if distance is not None:
        parts.append(f"📍 a unos {round(distance)} m")
    if shop.get("is_coffee_shop"):
        parts.append("☕ Especialidad")
    if shop.get("has_wifi"):
        parts.append("📶 Wifi")
    return " · ".join(parts)


def _intent_pills(intent: dict) -> None:
    """Devuelve al usuario lo que el sistema entendió de su petición."""
    if not intent:
        return
    chips = []
    if intent.get("area"):
        chips.append(f"📍 {intent['area']}")
    if intent.get("needs_wifi"):
        chips.append("📶 wifi")
    if intent.get("open_now"):
        chips.append("🟢 abierto ahora")
    if intent.get("radius_m"):
        chips.append(f"📏 radio ~{intent['radius_m']} m")
    if not chips:
        return
    html = "".join(
        f"<span style='display:inline-block;background:#F1E7D8;color:#5B4636;"
        f"border:1px solid #E0D2BC;border-radius:999px;padding:2px 12px;margin:2px 4px 2px 0;"
        f"font-size:0.85rem;'>{c}</span>"
        for c in chips
    )
    st.markdown(
        f"<div style='margin:-4px 0 8px'>"
        f"<span style='color:#8A7A66;font-size:0.8rem'>Entendí que buscas:</span><br>{html}</div>",
        unsafe_allow_html=True,
    )


def _maps_url(shop: dict) -> str:
    lat, lon = shop.get("lat"), shop.get("lon")
    return (
        f"https://www.google.com/maps/dir/?api=1"
        f"&destination={lat},{lon}&travelmode=walking"
    )


def _fetch_recommendations(text: str) -> dict:
    """Llama al backend reintentando si esta despertando del spin-down."""
    last_exc: httpx.HTTPError | None = None
    for attempt in range(_MAX_ATTEMPTS):
        try:
            response = httpx.post(
                f"{BACKEND_URL}/api/recommendations",
                json={"text": text},
                timeout=REQUEST_TIMEOUT,
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as exc:
            if exc.response.status_code not in _WAKEUP_STATUS:
                raise
            last_exc = exc
        except httpx.RequestError as exc:
            last_exc = exc
        if attempt < _MAX_ATTEMPTS - 1:
            time.sleep(_RETRY_BACKOFF_S * (attempt + 1))
    assert last_exc is not None
    raise last_exc


def _render(data: dict) -> None:
    recommendations = data.get("recommendations", [])
    _intent_pills(data.get("intent", {}))

    if not recommendations:
        st.warning(data.get("message") or "No he encontrado cafeterías para esa búsqueda.")
        return

    radius = data.get("search_radius_m")
    resumen = f"☕ {len(recommendations)} recomendaciones"
    if radius:
        resumen += f" · radio de búsqueda ~{radius} m"
    st.success(resumen)

    for i, rec in enumerate(recommendations, 1):
        shop = rec["candidate"]["shop"]
        with st.container(border=True):
            header = f"#### {i}. {shop['name']}"
            if i == 1:
                header += "  ·  ⭐ Mejor opción"
            st.markdown(header)
            st.caption(_badges(rec["candidate"], shop))
            if shop.get("address"):
                st.caption(f"📌 {shop['address']}")
            st.write(rec["reasoning"])
            if shop.get("lat") is not None and shop.get("lon") is not None:
                st.link_button("🧭 Cómo llegar", _maps_url(shop), use_container_width=True)


st.markdown("# ☕ MoodBrew")
st.markdown(
    "Recomendador de **cafeterías de especialidad**. Cuéntame dónde estás y qué te apetece."
)

st.caption("¿No sabes por dónde empezar? Prueba una de estas:")
example_cols = st.columns(len(_EXAMPLES))
for col, example in zip(example_cols, _EXAMPLES):
    if col.button(example, use_container_width=True):
        st.session_state.query_input = example
        st.session_state.run_search = True
        st.rerun()

with st.form("buscar"):
    query = st.text_input(
        "¿Qué buscas?",
        key="query_input",
        placeholder="Indica siempre la ciudad + un punto exacto. Ej.: café con wifi cerca de la Giralda, Sevilla",
        help=(
            "Para acertar necesito **la ciudad** y un **punto lo más concreto posible**: "
            "barrio, monumento, plaza o calle.\n\n"
            "✅ «Ixelles, Bruselas» · «cerca de la Giralda, Sevilla» · «el Born, Barcelona»\n\n"
            "⚠️ Evita nombres sueltos y ambiguos («Centro», «Gràcia»): sin ciudad puedo "
            "geolocalizar mal la búsqueda."
        ),
    )
    submitted = st.form_submit_button(
        "Recomiéndame ☕", type="primary", use_container_width=True
    )

run_search = submitted or st.session_state.pop("run_search", False)

if run_search:
    query = st.session_state.get("query_input", "").strip()
    if not query:
        st.info("Escribe primero qué te apetece y dónde estás.")
    else:
        try:
            with st.spinner(
                "Perfilando tu petición y buscando cafeterías de especialidad… "
                "(la primera búsqueda puede tardar unos segundos si el servicio estaba en reposo)"
            ):
                data = _fetch_recommendations(query)
        except httpx.HTTPStatusError as exc:
            st.error("El servicio ha tenido un problema procesando la búsqueda. Prueba de nuevo.")
            with st.expander("Detalle técnico"):
                st.code(f"{exc.response.status_code} · {exc.response.text[:500]}")
        except httpx.RequestError:
            st.error("No he podido conectar con el servicio de recomendaciones. ¿Está arrancado el backend?")
        else:
            _render(data)

st.divider()
st.caption("Datos de OpenStreetMap vía Geoapify · MoodBrew MVP")
