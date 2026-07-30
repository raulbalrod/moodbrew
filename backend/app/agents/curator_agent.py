from app.schemas.coffee import CoffeeShopCandidate
from app.schemas.recommendation import Recommendation
from app.services.llm_client import chat_json

_MAX_OPTIONS = 6
_YES_VALUES = {"yes", "true", "1"}

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
    "Eres un barista y guia de cafeterias de especialidad. De la lista de candidatas, elige "
    "entre 4 y 6 (segun cuantas encajen mejor con la peticion) y escribe una recomendacion "
    "breve, calida y apetecible que invite a visitarla.\n"
    "PRIORIDAD MAXIMA: las marcadas [ESPECIALIDAD] son cafeterias de cafe de especialidad "
    "(coffee_shop); es el criterio con MAS peso, por encima de la cercania y de cualquier "
    "otro. Elígelas siempre que existan y colócalas PRIMERO en tu seleccion, aunque esten algo "
    "mas lejos que una [generica]. Solo completa con [generica] si faltan opciones de "
    "especialidad. Dentro de cada grupo, prioriza las que encajen con lo que pide el usuario "
    "(p.ej. si pide terraza, wifi o accesible, elige las que lo tengan) y la cercania.\n"
    "Combina dos ingredientes:\n"
    "1) HECHOS: usa UNICAMENTE los datos que se dan de cada opcion (nombre, distancia, si esta "
    "abierta ahora, direccion y los 'extras' listados: wifi, terraza, accesible, web, opciones "
    "veganas). Puedes mencionar esos extras porque son datos objetivos. La distancia es "
    "aproximada y en linea recta desde la ubicacion indicada; exprésala como 'a unos X m' y no "
    "la atribuyas a un monumento o punto exacto.\n"
    "2) TONO: una pincelada GENERICA sobre la experiencia de tomar cafe de especialidad (hacer "
    "una pausa, disfrutar de un buen espresso o filtrado sin prisa, un plan de cafe con calma), "
    "como ambiente general, NUNCA como dato concreto de ese local.\n"
    "Prohibido inventar atributos del local: no afirmes su tueste, origenes, sabor, calidad, "
    "ambiente, especialidad ni fama; no menciones extras que no aparezcan en la opcion; no digas "
    "que pertenece a un barrio salvo que aparezca literal en la direccion; si un dato es "
    "desconocido (p.ej. el horario), dilo.\n"
    "1-2 frases por opcion, en español, tono cercano. Devuelve los indices elegidos."
)


def _open_label(is_open: bool | None) -> str:
    return {True: "si", False: "no"}.get(is_open, "desconocido")


def _is_yes(value: object) -> bool:
    return str(value).lower() in _YES_VALUES


def _extras(c: CoffeeShopCandidate) -> str:
    """Lista compacta de atributos objetivos (OSM) que el curador puede citar."""
    attrs = c.shop.attributes or {}
    extras = []
    if c.shop.has_wifi:
        extras.append("wifi")
    if _is_yes(attrs.get("outdoor_seating")):
        extras.append("terraza")
    if _is_yes(attrs.get("wheelchair")):
        extras.append("accesible")
    if _is_yes(attrs.get("diet_vegan")):
        extras.append("opciones veganas")
    if attrs.get("website"):
        extras.append("web")
    return ", ".join(extras) if extras else "ninguno conocido"


def _format_candidates(candidates: list[CoffeeShopCandidate]) -> str:
    lines = []
    for i, c in enumerate(candidates):
        distance = f"{round(c.distance_m)} m" if c.distance_m is not None else "distancia desconocida"
        category = "ESPECIALIDAD" if c.shop.is_coffee_shop else "generica"
        lines.append(
            f"[{i}] {c.shop.name} [{category}] - {distance} - abierta ahora: {_open_label(c.is_open)} - "
            f"extras: {_extras(c)} - {c.shop.address or 'sin direccion'}"
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
