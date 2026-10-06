from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class ServicioCrear(BaseModel):
    cliente_id: UUID
    plan_id: UUID
    tipo: str = "internet"
    usuario_pppoe: str | None = None
    fecha_instalacion: date | None = None
    fecha_vencimiento: date | None = None


class ServicioActualizar(BaseModel):
    plan_id: UUID | None = None
    tipo: str | None = None
    usuario_pppoe: str | None = None
    estado: str | None = None
    fecha_instalacion: date | None = None
    fecha_vencimiento: date | None = None
    suspendido: bool | None = None
    motivo_suspension: str | None = None


class ServicioRespuesta(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    empresa_id: UUID
    cliente_id: UUID
    plan_id: UUID
    tipo: str
    usuario_pppoe: str | None
    estado: str
    fecha_instalacion: date | None
    fecha_vencimiento: date | None
    suspendido: bool
    motivo_suspension: str | None
    created_at: datetime
    updated_at: datetime