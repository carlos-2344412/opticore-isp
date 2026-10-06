from datetime import datetime, timezone
from uuid import UUID, uuid4

from sqlmodel import Field, SQLModel


class ConversacionChatbot(SQLModel, table=True):

    __tablename__ = "conversaciones_chatbot"

    id: UUID = Field(
        default_factory=uuid4,
        primary_key=True
    )

    empresa_id: UUID = Field(
        foreign_key="empresas.id",
        index=True
    )

    cliente_id: UUID | None = Field(
        default=None,
        foreign_key="clientes.id",
        index=True
    )

    telefono: str | None = Field(
        default=None,
        max_length=30,
        index=True
    )

    esperando_documento: bool = Field(
        default=False
    )

    esperando_descripcion_soporte: bool = Field(
        default=False
    )
   
    esperando_datos_contratacion: bool = Field(
        default=False
    )

    paso_contratacion: str | None = Field(
        default=None,
        max_length=50
    )

    nombre_contratacion: str | None = Field(
        default=None,
        max_length=150
    )

    documento_contratacion: str | None = Field(
        default=None,
        max_length=30
    )

    direccion_contratacion: str | None = Field(
        default=None,
        max_length=255
    )

    plan_contratacion: UUID | None = Field(
        default=None
    )

    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )