from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class PagoCrear(BaseModel):
    cliente_id: UUID
    servicio_id: UUID

    monto: float = Field(
        gt=0
    )

    fecha_pago: datetime | None = None

    metodo_pago: str

    referencia: str | None = None

    estado: str = "pagado"

    observaciones: str | None = None
   
    factura_id: UUID | None = None

class PagoActualizar(BaseModel):
    monto: float | None = Field(
        default=None,
        gt=0
    )

    fecha_pago: datetime | None = None

    metodo_pago: str | None = None

    referencia: str | None = None

    estado: str | None = None

    observaciones: str | None = None


class PagoRespuesta(BaseModel):
    id: UUID
    empresa_id: UUID
    cliente_id: UUID
    servicio_id: UUID
    monto: float
    fecha_pago: datetime
    metodo_pago: str
    referencia: str | None
    estado: str
    observaciones: str | None
    created_at: datetime
    updated_at: datetime
    factura_id: UUID | None = None