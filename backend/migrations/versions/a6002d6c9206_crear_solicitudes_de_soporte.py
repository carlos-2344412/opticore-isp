"""crear solicitudes de soporte

Revision ID: a6002d6c9206
Revises: 1c4d043c9d75
Create Date: 2026-09-02
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "a6002d6c9206"
down_revision: Union[str, Sequence[str], None] = "1c4d043c9d75"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "solicitudes_soporte",

        sa.Column(
            "id",
            sa.Uuid(),
            nullable=False,
        ),

        sa.Column(
            "empresa_id",
            sa.Uuid(),
            nullable=False,
        ),

        sa.Column(
            "cliente_id",
            sa.Uuid(),
            nullable=False,
        ),

        sa.Column(
            "servicio_id",
            sa.Uuid(),
            nullable=True,
        ),

        sa.Column(
            "descripcion",
            sa.String(),
            nullable=False,
        ),

        sa.Column(
            "estado",
            sa.String(length=30),
            nullable=False,
            server_default="pendiente",
        ),

        sa.Column(
            "prioridad",
            sa.String(length=20),
            nullable=False,
            server_default="normal",
        ),

        sa.Column(
            "origen",
            sa.String(length=30),
            nullable=False,
            server_default="whatsapp",
        ),

        sa.Column(
            "tecnico_id",
            sa.Uuid(),
            nullable=True,
        ),

        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
        ),

        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
        ),

        sa.ForeignKeyConstraint(
            ["empresa_id"],
            ["empresas.id"],
        ),

        sa.ForeignKeyConstraint(
            ["cliente_id"],
            ["clientes.id"],
        ),

        sa.ForeignKeyConstraint(
            ["servicio_id"],
            ["servicios.id"],
        ),

        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index(
        "ix_solicitudes_soporte_empresa_id",
        "solicitudes_soporte",
        ["empresa_id"],
        unique=False,
    )

    op.create_index(
        "ix_solicitudes_soporte_cliente_id",
        "solicitudes_soporte",
        ["cliente_id"],
        unique=False,
    )

    op.create_index(
        "ix_solicitudes_soporte_servicio_id",
        "solicitudes_soporte",
        ["servicio_id"],
        unique=False,
    )

    op.create_index(
        "ix_solicitudes_soporte_estado",
        "solicitudes_soporte",
        ["estado"],
        unique=False,
    )

    op.create_index(
        "ix_solicitudes_soporte_prioridad",
        "solicitudes_soporte",
        ["prioridad"],
        unique=False,
    )

    op.create_index(
        "ix_solicitudes_soporte_tecnico_id",
        "solicitudes_soporte",
        ["tecnico_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_solicitudes_soporte_tecnico_id",
        table_name="solicitudes_soporte",
    )

    op.drop_index(
        "ix_solicitudes_soporte_prioridad",
        table_name="solicitudes_soporte",
    )

    op.drop_index(
        "ix_solicitudes_soporte_estado",
        table_name="solicitudes_soporte",
    )

    op.drop_index(
        "ix_solicitudes_soporte_servicio_id",
        table_name="solicitudes_soporte",
    )

    op.drop_index(
        "ix_solicitudes_soporte_cliente_id",
        table_name="solicitudes_soporte",
    )

    op.drop_index(
        "ix_solicitudes_soporte_empresa_id",
        table_name="solicitudes_soporte",
    )

    op.drop_table("solicitudes_soporte")