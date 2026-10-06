from uuid import UUID

from pydantic import BaseModel, Field


class ChatMensajeRequest(BaseModel):
    empresa_id: UUID

    mensaje: str = Field(
        min_length=1,
        max_length=2000,
    )

    # Se utilizará para identificar la conversación,
    # especialmente cuando conectemos WhatsApp.
    telefono: str | None = None

    # Opcional: útil para pruebas internas.
    cliente_id: UUID | None = None


class ChatMensajeResponse(BaseModel):
    respuesta: str
    intencion: str
    requiere_tecnico: bool = False
    datos: dict = {}