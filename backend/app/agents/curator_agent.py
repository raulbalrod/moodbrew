from app.schemas.coffee import CoffeeShopCandidate
from app.schemas.recommendation import Recommendation
from app.services.llm_client import chat_json

_MAX_OPTIONS = 3

_CURATION_SCHEMA = {
    "type": "object",
    "properties": {
        "selections": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "index": {"type": "integer"},
                    "reasoning": {"type": "string"},
                },
                "required": ["index", "reasoning"],
                "additionalProperties": False,
            },
        }
    },
    "required": ["selections"],
    "additionalProperties": False,
}

_SYSTEM_PROMPT = (
    "Eres un especialista en cafe de especialidad. De la lista de cafeterias candidatas, "
    "elige entre 2 y 3 y explica por que encajan con la peticion del usuario. "
    "Razona UNICAMENTE con los datos proporcionados (distancia, si esta abierta, wifi, "
    "direccion): no inventes tueste, sabor, ambiente ni ningun atributo que no aparezca. "
    "Tono cercano de especialista, 1-2 frases por opcion. Devuelve los indices elegidos."
)


def _open_label(is_open: bool | None) -> str:
    return {True: "si", False: "no"}.get(is_open, "desconocido")


def _format_candidates(candidates: list[CoffeeShopCandidate]) -> str:
    lines = []
    for i, c in enumerate(candidates):
        distance = f"{round(c.distance_m)} m" if c.distance_m is not None else "distancia desconocida"
        lines.append(
            f"[{i}] {c.shop.name} - {distance} - abierta ahora: {_open_label(c.is_open)} - "
            f"wifi: {'si' if c.shop.has_wifi else 'no'} - {c.shop.address or 'sin direccion'}"
        )
    return "\n".join(lines)


def _fallback(candidates: list[CoffeeShopCandidate]) -> list[Recommendation]:
    """Si el LLM falla: devuelve los primeros candidatos con un razonamiento factual."""
    recs = []
    for c in candidates[:_MAX_OPTIONS]:
        distance = f"a {round(c.distance_m)} m" if c.distance_m is not None else "cerca"
        recs.append(Recommendation(candidate=c, reasoning=f"{c.shop.name}, {distance} de tu ubicacion."))
    return recs


async def curate(query: str, candidates: list[CoffeeShopCandidate]) -> list[Recommendation]:
    """Agente curador: elige 2-3 candidatos y los razona con tono de especialista."""
    if not candidates:
        return []

    messages = [
        {"role": "system", "content": _SYSTEM_PROMPT},
        {
            "role": "user",
            "content": f"Peticion del usuario: {query}\n\nCandidatas:\n{_format_candidates(candidates)}",
        },
    ]
    try:
        data = await chat_json(messages, _CURATION_SCHEMA, "curation")
    except Exception:
        return _fallback(candidates)

    recommendations = []
    for selection in data.get("selections", [])[:_MAX_OPTIONS]:
        index = selection.get("index")
        if isinstance(index, int) and 0 <= index < len(candidates):
            recommendations.append(
                Recommendation(candidate=candidates[index], reasoning=selection["reasoning"])
            )
    return recommendations or _fallback(candidates)
