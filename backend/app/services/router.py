from fastapi import APIRouter
from sqlmodel import Session

from app.db.database import engine
from app.services.cobranza_automatica import revisar_servicios_vencidos


router = APIRouter(
    prefix="/automatizacion",
    tags=["Automatización"],
)


@router.post("/revisar-cobranza")
def ejecutar_revision_cobranza():
    """
    Ejecuta manualmente la revisión de servicios vencidos.
    """

    with Session(engine) as session:

        resultado = revisar_servicios_vencidos(session)

        return resultado