from pydantic import BaseModel, Field


class IntentProfile(BaseModel):
    """Perfil estructurado que extrae el Agente 1 del texto libre del usuario.

    Solo campos extraibles/objetivos para el MVP: el agente rellena unicamente
    lo que el usuario expresa, sin inventar.
    """

    area: str | None = Field(
        default=None, description="Zona, barrio o ciudad indicada por el usuario."
    )
    needs_wifi: bool = Field(default=False, description="Prefiere wifi.")
    open_now: bool = Field(default=False, description="Debe estar abierto ahora.")
    radius_m: int = Field(
        default=1500, ge=100, le=10000, description="Radio de busqueda en metros."
    )
