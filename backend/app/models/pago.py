from datetime import datetime, timezone
from uuid import UUID, uuid4

from sqlmodel import Field, SQLModel


class Pago(SQLModel, table=True):
    __tablename__ = "pagos"

    id: UUID = Field(
        default_factory=uuid4,
        primary_key=True,
    )

    empresa_id: UUID = Field(
        foreign_key="empresas.id",
        index=True,
    )

    cliente_id: UUID = Field(
        foreign_key="clientes.id",
        index=True,
    )

    servicio_id: UUID = Field(
        foreign_key="servicios.id",
        index=True,
    )

    factura_id: UUID | None = Field(
        default=None,
        foreign_key="facturas.id",
        index=True,
    )

    monto: float = Field(
        gt=0
    )

    fecha_pago: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    metodo_pago: str = Field(
        max_length=30
    )

    referencia: str | None = Field(
        default=None,
        max_length=100,
        index=True,
    )

    estado: str = Field(
        default="pagado",
        max_length=20,
        index=True,
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