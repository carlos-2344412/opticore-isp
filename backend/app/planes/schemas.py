from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class PlanCrear(BaseModel):
    nombre: str
    velocidad_bajada: int
    velocidad_subida: int
    precio_mensual: float
    descripcion: str | None = None


class PlanActualizar(BaseModel):
    nombre: str | None = None
    velocidad_bajada: int | None = None
    velocidad_subida: int | None = None
    precio_mensual: float | None = None
    descripcion: str | None = None
    estado: bool | None = None


class PlanRespuesta(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    empresa_id: UUID
    nombre: str
    velocidad_bajada: int
    velocidad_subida: int
    precio_mensual: float
    descripcion: str | None
    estado: bool
    created_at: datetime
    updated_at: datetime