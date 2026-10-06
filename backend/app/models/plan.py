from datetime import datetime, timezone
from uuid import UUID, uuid4

from sqlmodel import Field, SQLModel


class Plan(SQLModel, table=True):
    __tablename__ = "planes"

    id: UUID = Field(default_factory=uuid4, primary_key=True)

    empresa_id: UUID = Field(
        foreign_key="empresas.id",
        index=True,
    )

    nombre: str = Field(max_length=100)

    velocidad_bajada: int

    velocidad_subida: int

    precio_mensual: float

    descripcion: str | None = Field(default=None)

    estado: bool = Field(default=True)

    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
