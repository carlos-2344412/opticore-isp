from datetime import datetime, timezone
from uuid import UUID, uuid4

from sqlmodel import Field, SQLModel


class ComprobantePago(SQLModel, table=True):
    __tablename__ = "comprobantes_pago"

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

    factura_id: UUID | None = Field(
        default=None,
        foreign_key="facturas.id",
        index=True,
    )

    pago_id: UUID | None = Field(
        default=None,
        foreign_key="pagos.id",
        index=True,
    )

    archivo_url: str = Field(
        max_length=500,
    )

    nombre_archivo: str | None = Field(
        default=None,
        max_length=255,
    )

    estado_validacion: str = Field(
        default="en_revision",
        max_length=30,
        index=True,
    )

    monto_detectado: float | None = Field(
        default=None,
    )

    fecha_detectada: datetime | None = Field(
        default=None,
    )

    banco_detectado: str | None = Field(
        default=None,
        max_length=100,
    )

    destinatario_detectado: str | None = Field(
        default=None,
        max_length=200,
    )

    referencia_detectada: str | None = Field(
        default=None,
        max_length=100,
    )

    observaciones: str | None = Field(
        default=None,
    )

    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
    )

    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
    )