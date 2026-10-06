from datetime import datetime, timezone
from uuid import UUID, uuid4

from sqlmodel import Field, SQLModel


class EvidenciaSoporte(SQLModel, table=True):
    __tablename__ = "evidencias_soporte"

    id: UUID = Field(
        default_factory=uuid4,
        primary_key=True,
    )

    solicitud_id: UUID = Field(
        foreign_key="solicitudes_soporte.id",
        index=True,
    )

    empresa_id: UUID = Field(
        foreign_key="empresas.id",
        index=True,
    )

    tecnico_id: UUID = Field(
        index=True,
    )

    archivo_url: str

    tipo: str = Field(
        default="foto",
        max_length=30,
    )

    descripcion: str | None = Field(
        default=None,
        max_length=500,
    )

    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
    )