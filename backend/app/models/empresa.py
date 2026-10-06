from datetime import datetime, timezone
from uuid import UUID, uuid4

from sqlmodel import Field, SQLModel


class Empresa(SQLModel, table=True):
    __tablename__ = "empresas"

    id: UUID = Field(default_factory=uuid4, primary_key=True)

    nombre: str = Field(max_length=150, index=True)

    nit: str | None = Field(
        default=None,
        max_length=30,
        unique=True,
        index=True,
    )

    telefono: str | None = Field(
        default=None,
        max_length=20,
    )

    correo: str | None = Field(
        default=None,
        max_length=150,
    )

    direccion: str | None = Field(default=None)

    ciudad: str | None = Field(
        default=None,
        max_length=100,
    )

    departamento: str | None = Field(
        default=None,
        max_length=100,
    )

    logo: str | None = Field(default=None)

    estado: bool = Field(default=True)

    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )