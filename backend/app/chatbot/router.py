from uuid import UUID

from fastapi import APIRouter
from sqlmodel import Session

from app.chatbot.schemas import (
    ChatMensajeRequest,
    ChatMensajeResponse,
)
from app.chatbot.service import procesar_mensaje
from app.db.database import engine


router = APIRouter(
    prefix="/chatbot",
    tags=["Chatbot"],
)


@router.post(
    "/mensaje",
    response_model=ChatMensajeResponse,
)
def enviar_mensaje(
    datos: ChatMensajeRequest,
):

    with Session(engine) as session:

        respuesta = procesar_mensaje(
            session=session,
            empresa_id=datos.empresa_id,
            mensaje=datos.mensaje,
            cliente_id=datos.cliente_id,
            telefono=datos.telefono,
        )

        return respuesta