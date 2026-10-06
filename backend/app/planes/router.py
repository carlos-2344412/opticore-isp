from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlmodel import Session, select

from app.auth.security import obtener_payload_token
from app.db.database import engine
from app.models import Plan

from app.planes.schemas import (
    PlanActualizar,
    PlanCrear,
    PlanRespuesta,
)


router = APIRouter(
    prefix="/planes",
    tags=["Planes"],
)


oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/auth/login"
)


def obtener_usuario_token(
    token: str = Depends(oauth2_scheme),
):
    try:
        return obtener_payload_token(token)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido o expirado",
        )


@router.post(
    "",
    response_model=PlanRespuesta,
    status_code=status.HTTP_201_CREATED,
)
def crear_plan(
    datos: PlanCrear,
    payload: dict = Depends(obtener_usuario_token),
):
    empresa_id = UUID(payload["empresa_id"])

    if datos.velocidad_bajada <= 0:
        raise HTTPException(
            status_code=400,
            detail="La velocidad de bajada debe ser mayor que 0",
        )

    if datos.velocidad_subida <= 0:
        raise HTTPException(
            status_code=400,
            detail="La velocidad de subida debe ser mayor que 0",
        )

    if datos.precio_mensual < 0:
        raise HTTPException(
            status_code=400,
            detail="El precio no puede ser negativo",
        )

    with Session(engine) as session:

        plan = Plan(
            empresa_id=empresa_id,
            nombre=datos.nombre,
            velocidad_bajada=datos.velocidad_bajada,
            velocidad_subida=datos.velocidad_subida,
            precio_mensual=datos.precio_mensual,
            descripcion=datos.descripcion,
            estado=True,
        )

        session.add(plan)
        session.commit()
        session.refresh(plan)

        return plan


@router.get(
    "",
    response_model=list[PlanRespuesta],
)
def listar_planes(
    payload: dict = Depends(obtener_usuario_token),
):
    empresa_id = UUID(payload["empresa_id"])

    with Session(engine) as session:

        planes = session.exec(
            select(Plan)
            .where(
                Plan.empresa_id == empresa_id
            )
            .order_by(Plan.nombre)
        ).all()

        return planes


@router.get(
    "/{plan_id}",
    response_model=PlanRespuesta,
)
def obtener_plan(
    plan_id: UUID,
    payload: dict = Depends(obtener_usuario_token),
):
    empresa_id = UUID(payload["empresa_id"])

    with Session(engine) as session:

        plan = session.exec(
            select(Plan)
            .where(
                Plan.id == plan_id,
                Plan.empresa_id == empresa_id,
            )
        ).first()

        if not plan:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Plan no encontrado",
            )

        return plan


@router.put(
    "/{plan_id}",
    response_model=PlanRespuesta,
)
def actualizar_plan(
    plan_id: UUID,
    datos: PlanActualizar,
    payload: dict = Depends(obtener_usuario_token),
):
    empresa_id = UUID(payload["empresa_id"])

    with Session(engine) as session:

        plan = session.exec(
            select(Plan)
            .where(
                Plan.id == plan_id,
                Plan.empresa_id == empresa_id,
            )
        ).first()

        if not plan:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Plan no encontrado",
            )

        cambios = datos.model_dump(
            exclude_unset=True
        )

        if (
            "velocidad_bajada" in cambios
            and cambios["velocidad_bajada"] <= 0
        ):
            raise HTTPException(
                status_code=400,
                detail="La velocidad de bajada debe ser mayor que 0",
            )

        if (
            "velocidad_subida" in cambios
            and cambios["velocidad_subida"] <= 0
        ):
            raise HTTPException(
                status_code=400,
                detail="La velocidad de subida debe ser mayor que 0",
            )

        if (
            "precio_mensual" in cambios
            and cambios["precio_mensual"] < 0
        ):
            raise HTTPException(
                status_code=400,
                detail="El precio no puede ser negativo",
            )

        for campo, valor in cambios.items():
            setattr(plan, campo, valor)

        plan.updated_at = datetime.now(timezone.utc)

        session.add(plan)
        session.commit()
        session.refresh(plan)

        return plan


@router.delete(
    "/{plan_id}",
)
def desactivar_plan(
    plan_id: UUID,
    payload: dict = Depends(obtener_usuario_token),
):
    empresa_id = UUID(payload["empresa_id"])

    with Session(engine) as session:

        plan = session.exec(
            select(Plan)
            .where(
                Plan.id == plan_id,
                Plan.empresa_id == empresa_id,
            )
        ).first()

        if not plan:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Plan no encontrado",
            )

        plan.estado = False
        plan.updated_at = datetime.now(timezone.utc)

        session.add(plan)
        session.commit()

        return {
            "mensaje": "Plan desactivado correctamente"
        }