from datetime import datetime, timezone
from uuid import UUID, uuid4

from sqlmodel import Field, SQLModel


class SolicitudSoporte(SQLModel, table=True):
    __tablename__ = "solicitudes_soporte"

    # Identificador único de la solicitud
    id: UUID = Field(
        default_factory=uuid4,
        primary_key=True,
    )

    # Empresa propietaria de la solicitud
    empresa_id: UUID = Field(
        foreign_key="empresas.id",
        index=True,
    )

    # Cliente que reporta el problema
    cliente_id: UUID = Field(
        foreign_key="clientes.id",
        index=True,
    )

    # Servicio que presenta el problema
    servicio_id: UUID | None = Field(
        default=None,
        foreign_key="servicios.id",
        index=True,
    )

    # Descripción proporcionada por el cliente
    descripcion: str

    # Estado de la solicitud
    # pendiente → creada, esperando asignación
    # asignada → técnico asignado
    # en_proceso → técnico trabajando
    # resuelta → problema solucionado
    # cancelada → solicitud cancelada
    estado: str = Field(
        default="pendiente",
        max_length=30,
        index=True,
    )

    # Prioridad del reporte
    # baja, normal, alta, urgente
    prioridad: str = Field(
        default="normal",
        max_length=20,
        index=True,
    )

    # Origen de la solicitud
    # whatsapp, web, telefono, empresa
    origen: str = Field(
        default="whatsapp",
        max_length=30,
    )

    # Aquí posteriormente asignaremos el técnico
    tecnico_id: UUID | None = Field(
        default=None,
        index=True,
    )

    # Fechas de control
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )