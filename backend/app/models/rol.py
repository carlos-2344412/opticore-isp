from datetime import datetime, timezone
from uuid import UUID, uuid4

from sqlmodel import Field, SQLModel


class Rol(SQLModel, table=True):
    __tablename__ = "roles"

    id: UUID = Field(default_factory=uuid4, primary_key=True)

    nombre: str = Field(
        max_length=50,
        unique=True,
        index=True,
    )

    descripcion: str | None = Field(
        default=None,
        max_length=255,
    )

    estado: bool = Field(default=True)

    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )