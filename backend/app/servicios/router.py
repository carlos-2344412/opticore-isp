from datetime import date, datetime, timezone
from dateutil.relativedelta import relativedelta
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlmodel import Session, select

from app.auth.security import obtener_payload_token
from app.db.database import engine
from app.models import Cliente, Plan, Servicio

from app.servicios.schemas import (
    ServicioActualizar,
    ServicioCrear,
    ServicioRespuesta,
)


router = APIRouter(
    prefix="/servicios",
    tags=["Servicios"],
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
    response_model=ServicioRespuesta,
    status_code=status.HTTP_201_CREATED,
)
def crear_servicio(
    datos: ServicioCrear,
    payload: dict = Depends(obtener_usuario_token),
):
    empresa_id = UUID(payload["empresa_id"])

    with Session(engine) as session:

        cliente = session.exec(
            select(Cliente).where(
                Cliente.id == datos.cliente_id,
                Cliente.empresa_id == empresa_id,
            )
        ).first()

        if not cliente:
            raise HTTPException(
                status_code=404,
                detail="Cliente no encontrado",
            )

        plan = session.exec(
            select(Plan).where(
                Plan.id == datos.plan_id,
                Plan.empresa_id == empresa_id,
                Plan.estado == True,
            )
        ).first()

        if not plan:
            raise HTTPException(
                status_code=404,
                detail="Plan no encontrado o inactivo",
            )

        if datos.usuario_pppoe:

            existente = session.exec(
                select(Servicio).where(
                    Servicio.usuario_pppoe
                    == datos.usuario_pppoe
                )
            ).first()

            if existente:
                raise HTTPException(
                    status_code=409,
                    detail="El usuario PPPoE ya está registrado",
                )

        # Fecha de instalación
        fecha_instalacion = datos.fecha_instalacion or date.today()

        # El servicio vence un mes después de la instalación
        fecha_vencimiento = fecha_instalacion + relativedelta(months=1)

        servicio = Servicio(
            empresa_id=empresa_id,
            cliente_id=datos.cliente_id,
            plan_id=datos.plan_id,
            tipo=datos.tipo,
            usuario_pppoe=datos.usuario_pppoe,
            estado="activo",
            fecha_instalacion=fecha_instalacion,
            fecha_vencimiento=fecha_vencimiento,
            suspendido=False,
            motivo_suspension=None,
        )

        session.add(servicio)
        session.commit()
        session.refresh(servicio)

        return servicio


@router.get(
    "",
    response_model=list[ServicioRespuesta],
)
def listar_servicios(
    payload: dict = Depends(obtener_usuario_token),
):
    empresa_id = UUID(payload["empresa_id"])

    with Session(engine) as session:

        servicios = session.exec(
            select(Servicio)
            .where(
                Servicio.empresa_id == empresa_id
            )
            .order_by(Servicio.created_at.desc())
        ).all()

        return servicios


@router.get(
    "/{servicio_id}",
    response_model=ServicioRespuesta,
)
def obtener_servicio(
    servicio_id: UUID,
    payload: dict = Depends(obtener_usuario_token),
):
    empresa_id = UUID(payload["empresa_id"])

    with Session(engine) as session:

        servicio = session.exec(
            select(Servicio)
            .where(
                Servicio.id == servicio_id,
                Servicio.empresa_id == empresa_id,
            )
        ).first()

        if not servicio:
            raise HTTPException(
                status_code=404,
                detail="Servicio no encontrado",
            )

        return servicio


@router.put(
    "/{servicio_id}",
    response_model=ServicioRespuesta,
)
def actualizar_servicio(
    servicio_id: UUID,
    datos: ServicioActualizar,
    payload: dict = Depends(obtener_usuario_token),
):
    empresa_id = UUID(payload["empresa_id"])

    with Session(engine) as session:

        servicio = session.exec(
            select(Servicio).where(
                Servicio.id == servicio_id,
                Servicio.empresa_id == empresa_id,
            )
        ).first()

        if not servicio:
            raise HTTPException(
                status_code=404,
                detail="Servicio no encontrado",
            )

        cambios = datos.model_dump(
            exclude_unset=True
        )

        if "plan_id" in cambios:

            plan = session.exec(
                select(Plan).where(
                    Plan.id == cambios["plan_id"],
                    Plan.empresa_id == empresa_id,
                    Plan.estado == True,
                )
            ).first()

            if not plan:
                raise HTTPException(
                    status_code=404,
                    detail="Plan no encontrado o inactivo",
                )

        if "usuario_pppoe" in cambios:

            usuario_pppoe = cambios["usuario_pppoe"]

            if usuario_pppoe:

                existente = session.exec(
                    select(Servicio).where(
                        Servicio.usuario_pppoe
                        == usuario_pppoe,
                        Servicio.id != servicio_id,
                    )
                ).first()

                if existente:
                    raise HTTPException(
                        status_code=409,
                        detail="El usuario PPPoE ya está registrado",
                    )

        for campo, valor in cambios.items():
            setattr(servicio, campo, valor)

        servicio.updated_at = datetime.now(
            timezone.utc
        )

        session.add(servicio)
        session.commit()
        session.refresh(servicio)

        return servicio


@router.delete(
    "/{servicio_id}",
)
def suspender_servicio(
    servicio_id: UUID,
    payload: dict = Depends(obtener_usuario_token),
):
    empresa_id = UUID(payload["empresa_id"])

    with Session(engine) as session:

        servicio = session.exec(
            select(Servicio).where(
                Servicio.id == servicio_id,
                Servicio.empresa_id == empresa_id,
            )
        ).first()

        if not servicio:
            raise HTTPException(
                status_code=404,
                detail="Servicio no encontrado",
            )

        servicio.estado = "suspendido"
        servicio.suspendido = True
        servicio.motivo_suspension = "Suspensión manual"
        servicio.updated_at = datetime.now(
            timezone.utc
        )

        session.add(servicio)
        session.commit()

        return {
            "mensaje": "Servicio suspendido correctamente"
        }