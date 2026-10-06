from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class ClienteCrear(BaseModel):
    documento: str | None = None
    nombre: str
    apellido: str | None = None
    telefono: str
    correo: str | None = None
    direccion: str
    ciudad: str | None = None
    barrio: str | None = None
    referencia_direccion: str | None = None


class ClienteActualizar(BaseModel):
    documento: str | None = None
    nombre: str | None = None
    apellido: str | None = None
    telefono: str | None = None
    correo: str | None = None
    direccion: str | None = None
    ciudad: str | None = None
    barrio: str | None = None
    referencia_direccion: str | None = None
    estado: str | None = None


class ClienteRespuesta(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    empresa_id: UUID
    documento: str | None
    nombre: str
    apellido: str | None
    telefono: str
    correo: str | None
    direccion: str
    ciudad: str | None
    barrio: str | None
    referencia_direccion: str | None
    estado: str
    created_at: datetime
    updated_at: datetime