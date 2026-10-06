from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


# ==========================================
# CREAR SOLICITUD DE SOPORTE
# ==========================================

class SolicitudSoporteCreate(BaseModel):
    cliente_id: UUID

    servicio_id: UUID | None = None

    descripcion: str = Field(
        min_length=5,
        max_length=2000,
    )

    prioridad: str = "normal"

    origen: str = "whatsapp"


# ==========================================
# ACTUALIZAR SOLICITUD
# ==========================================

class SolicitudSoporteUpdate(BaseModel):
    estado: str | None = None


# ==========================================
# RESPUESTA DE SOLICITUD
# ==========================================

class SolicitudSoporteResponse(BaseModel):
    id: UUID

    empresa_id: UUID

    cliente_id: UUID

    servicio_id: UUID | None

    descripcion: str

    estado: str

    prioridad: str

    origen: str

    tecnico_id: UUID | None

    # ==========================================
    # INFORMACIÓN DEL SERVICIO
    # ==========================================

    servicio_tipo: str | None = None

    servicio_usuario_pppoe: str | None = None

    servicio_estado: str | None = None

    servicio_suspendido: bool | None = None

    # ==========================================
    # INFORMACIÓN DEL PLAN
    # ==========================================

    plan_nombre: str | None = None

    plan_velocidad_bajada: int | None = None

    plan_velocidad_subida: int | None = None

    plan_precio_mensual: float | None = None

    # ==========================================
    # INFORMACIÓN DEL CLIENTE
    # ==========================================

    cliente_nombre: str | None = None

    cliente_telefono: str | None = None

    cliente_direccion: str | None = None

    cliente_ciudad: str | None = None

    cliente_barrio: str | None = None

    cliente_referencia: str | None = None

    # ==========================================
    # FECHAS
    # ==========================================

    created_at: datetime

    updated_at: datetime

    model_config = {
        "from_attributes": True
    }