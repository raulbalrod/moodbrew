from app.schemas.intent import IntentProfile
from app.services.llm_client import chat_json

_INTENT_SCHEMA = {
    "type": "object",
    "properties": {
        "area": {"type": ["string", "null"]},
        "needs_wifi": {"type": "boolean"},
        "open_now": {"type": "boolean"},
    },
    "required": ["area", "needs_wifi", "open_now"],
    "additionalProperties": False,
}

_SYSTEM_PROMPT = (
    "Eres un extractor de intencion para un recomendador de cafeterias de especialidad. "
    "Devuelve UNICAMENTE los campos del schema, basandote solo en lo que el usuario dice. "
    "No inventes: si un dato no aparece, usa null para `area` y false para `needs_wifi` "
    "y `open_now`. `area` es la ubicacion MAS ESPECIFICA que menciona el usuario: incluye "
    "el punto de referencia, monumento, plaza o calle junto con la ciudad si aparece "
    "(p.ej. 'Giralda, Sevilla' o 'Plaza Mayor, Madrid'), no la reduzcas solo a la ciudad."
)


async def parse_intent(text: str) -> IntentProfile:
    """Agente de intencion: texto libre -> IntentProfile validado.

    Degradado elegante: si el LLM falla, devuelve un perfil vacio en vez de romper.
    """
    messages = [
        {"role": "system", "content": _SYSTEM_PROMPT},
        {"role": "user", "content": text},
    ]
    try:
        data = await chat_json(messages, _INTENT_SCHEMA, "intent_profile")
    except Exception:
        return IntentProfile()
    return IntentProfile.model_validate(data)
