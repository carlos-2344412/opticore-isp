from datetime import date, datetime, timezone
from uuid import UUID, uuid4

from sqlmodel import Field, SQLModel


class Servicio(SQLModel, table=True):
    __tablename__ = "servicios"

    id: UUID = Field(default_factory=uuid4, primary_key=True)

    empresa_id: UUID = Field(
        foreign_key="empresas.id",
        index=True,
    )

    cliente_id: UUID = Field(
        foreign_key="clientes.id",
        index=True,
    )

    plan_id: UUID = Field(
        foreign_key="planes.id",
        index=True,
    )

    tipo: str = Field(
        default="internet",
        max_length=30,
    )

    usuario_pppoe: str | None = Field(
        default=None,
        max_length=100,
        unique=True,
        index=True,
    )

    estado: str = Field(
        default="pendiente",
        max_length=20,
        index=True,
    )

    fecha_instalacion: date | None = Field(default=None)

    fecha_vencimiento: date | None = Field(default=None)

    suspendido: bool = Field(default=False)

    motivo_suspension: str | None = Field(default=None)

    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
