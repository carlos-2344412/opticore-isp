from datetime import datetime, timezone
from uuid import UUID, uuid4

from sqlmodel import Field, SQLModel


class Cliente(SQLModel, table=True):
    __tablename__ = "clientes"

    id: UUID = Field(default_factory=uuid4, primary_key=True)

    empresa_id: UUID = Field(
        foreign_key="empresas.id",
        index=True,
    )

    documento: str | None = Field(
        default=None,
        max_length=30,
        index=True,
    )

    nombre: str = Field(max_length=100)

    apellido: str | None = Field(
        default=None,
        max_length=100,
    )

    telefono: str = Field(max_length=20)

    correo: str | None = Field(
        default=None,
        max_length=150,
    )

    direccion: str

    ciudad: str | None = Field(
        default=None,
        max_length=100,
    )

    barrio: str | None = Field(
        default=None,
        max_length=100,
    )

    referencia_direccion: str | None = Field(default=None)

    estado: str = Field(
        default="activo",
        max_length=20,
        index=True,
    )

    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
