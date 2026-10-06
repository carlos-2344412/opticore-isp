from datetime import datetime, timezone
from uuid import UUID, uuid4

from sqlmodel import Field, SQLModel


class Factura(SQLModel, table=True):
    __tablename__ = "facturas"

    id: UUID = Field(
        default_factory=uuid4,
        primary_key=True
    )

    empresa_id: UUID = Field(
        foreign_key="empresas.id",
        index=True
    )

    cliente_id: UUID = Field(
        foreign_key="clientes.id",
        index=True
    )

    servicio_id: UUID | None = Field(
        default=None,
        foreign_key="servicios.id",
        index=True
    )

    numero: str = Field(
        max_length=50,
        unique=True,
        index=True
    )

    referencia_pago: str | None = Field(
        default=None,
        max_length=50,
        unique=True,
        index=True
    )
    concepto: str = Field(
        default="Servicio de Internet",
        max_length=200
    )

    subtotal: float = Field(default=0)

    descuento: float = Field(default=0)

    total: float = Field(default=0)

    fecha_emision: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    fecha_vencimiento: datetime | None = Field(
        default=None
    )

    estado: str = Field(
        default="pendiente",
        max_length=20,
        index=True
    )

    observaciones: str | None = Field(
        default=None
    )

    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )