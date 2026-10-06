from datetime import datetime, timezone
from uuid import UUID, uuid4

from sqlmodel import Field, SQLModel


class Usuario(SQLModel, table=True):
    __tablename__ = "usuarios"

    id: UUID = Field(default_factory=uuid4, primary_key=True)

    empresa_id: UUID = Field(
        foreign_key="empresas.id",
        index=True,
    )

    rol_id: UUID = Field(
        foreign_key="roles.id",
        index=True,
    )

    nombre: str = Field(max_length=100)

    apellido: str | None = Field(
        default=None,
        max_length=100,
    )

    correo: str = Field(
        max_length=150,
        unique=True,
        index=True,
    )

    telefono: str | None = Field(
        default=None,
        max_length=20,
    )

    password_hash: str

    estado: bool = Field(default=True)

    ultimo_acceso: datetime | None = Field(default=None)

    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )