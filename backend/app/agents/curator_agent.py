from app.schemas.coffee import CoffeeShopCandidate
from app.schemas.recommendation import CurationResult, Recommendation
from app.services.llm_client import chat_json

_CURATED_MAX = 3
_NEARBY_MAX = 6
_YES_VALUES = {"yes", "true", "1"}

_SELECTIONS = {
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

_CURATION_SCHEMA = {
    "type": "object",
    "properties": {"curated": _SELECTIONS, "nearby": _SELECTIONS},
    "required": ["curated", "nearby"],
    "additionalProperties": False,
}

_SYSTEM_PROMPT = (
    "Eres un barista y guia de cafeterias de especialidad. De la lista de candidatas, produce DOS "
    "grupos SIN repetir ninguna entre ellos:\n"
    "- 'curated': entre 1 y 3, las MEJORES para la peticion; son las que se muestran destacadas.\n"
    "- 'nearby': hasta 6 ADICIONALES como 'tambien te pueden gustar, cerca de tu ubicacion'.\n"
    "Para cada opcion escribe una recomendacion breve, calida y apetecible que invite a visitarla.\n"
    "PRIORIDAD MAXIMA: las marcadas [ESPECIALIDAD] son cafeterias de cafe de especialidad "
    "(coffee_shop); es el criterio con MAS peso, por encima de la cercania y de cualquier otro. "
    "Elígelas siempre que existan y colócalas PRIMERO, sobre todo en 'curated', aunque esten algo "
    "mas lejos que una [generica]. Solo completa con [generica] si faltan opciones de especialidad. "
    "Dentro de cada grupo, prioriza las que encajen con lo que pide el usuario (p.ej. terraza, wifi "
    "o accesible) y la cercania.\n"
    "Combina dos ingredientes:\n"
    "1) HECHOS: usa UNICAMENTE los datos que se dan de cada opcion (nombre, distancia, si esta "
    "abierta ahora, direccion y los 'extras' listados: wifi, terraza, accesible, web, opciones "
    "veganas). Puedes mencionar esos extras porque son datos objetivos. La distancia es aproximada "
    "y en linea recta desde la ubicacion indicada; exprésala como 'a unos X m' y no la atribuyas a "
    "un monumento o punto exacto.\n"
    "2) TONO: una pincelada GENERICA sobre la experiencia de tomar cafe de especialidad (hacer una "
    "pausa, disfrutar de un buen espresso o filtrado sin prisa, un plan de cafe con calma), como "
    "ambiente general, NUNCA como dato concreto de ese local.\n"
    "Prohibido inventar atributos del local: no afirmes su tueste, origenes, sabor, calidad, "
    "ambiente, especialidad ni fama; no menciones extras que no aparezcan en la opcion; no digas "
    "que pertenece a un barrio salvo que aparezca literal en la direccion; si un dato es desconocido "
    "(p.ej. el horario), dilo.\n"
    "1-2 frases por opcion, en español, tono cercano. Devuelve los indices elegidos en cada grupo."
)


def _open_label(is_open: bool | None) -> str:
    return {True: "si", False: "no"}.get(is_open, "desconocido")


def _is_yes(value: object) -> bool:
    return str(value).lower() in _YES_VALUES


def _extras(c: CoffeeShopCandidate) -> str:
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


def _factual_rec(c: CoffeeShopCandidate) -> Recommendation:
    distance = f"a {round(c.distance_m)} m" if c.distance_m is not None else "cerca"
    return Recommendation(candidate=c, reasoning=f"{c.shop.name}, {distance} de tu ubicacion.")


def _fallback(candidates: list[CoffeeShopCandidate]) -> CurationResult:
    """Si el LLM falla: reparte los candidatos ya rankeados en ambos grupos, sin razonar."""
    recs = [_factual_rec(c) for c in candidates[: _CURATED_MAX + _NEARBY_MAX]]
    return CurationResult(curated=recs[:_CURATED_MAX], nearby=recs[_CURATED_MAX:])


def _pick(
    selections: list[dict],
    candidates: list[CoffeeShopCandidate],
    limit: int,
    exclude: set[int],
) -> tuple[list[Recommendation], set[int]]:
    recs: list[Recommendation] = []
    used: set[int] = set()
    for selection in selections:
        if len(recs) >= limit:
            break
        index = selection.get("index")
        if isinstance(index, int) and 0 <= index < len(candidates) and index not in exclude | used:
            used.add(index)
            recs.append(Recommendation(candidate=candidates[index], reasoning=selection["reasoning"]))
    return recs, used


async def curate(query: str, candidates: list[CoffeeShopCandidate]) -> CurationResult:
    """Agente curador: destacadas + secundarias, razonadas de especialista, en una sola llamada."""
    if not candidates:
        return CurationResult(curated=[], nearby=[])

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

    curated, used = _pick(data.get("curated", []), candidates, _CURATED_MAX, set())
    nearby, _ = _pick(data.get("nearby", []), candidates, _NEARBY_MAX, used)

    if not curated and not nearby:
        return _fallback(candidates)
    return CurationResult(curated=curated, nearby=nearby)
