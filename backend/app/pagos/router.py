from datetime import datetime, timezone
from uuid import UUID

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
)
from fastapi.security import OAuth2PasswordBearer
from sqlmodel import Session, select

from app.auth.security import obtener_payload_token
from app.db.database import engine
from app.models import Cliente, Servicio, Pago, Factura

from app.pagos.schemas import (
    PagoActualizar,
    PagoCrear,
    PagoRespuesta,
)


router = APIRouter(
    prefix="/pagos",
    tags=["Pagos"],
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


# ==========================================
# CREAR PAGO
# ==========================================

@router.post(
    "",
    response_model=PagoRespuesta,
    status_code=status.HTTP_201_CREATED,
)
def crear_pago(
    datos: PagoCrear,
    payload: dict = Depends(obtener_usuario_token),
):

    empresa_id = UUID(payload["empresa_id"])

    with Session(engine) as session:

        # =====================================
        # VERIFICAR CLIENTE
        # =====================================

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

        # =====================================
        # VERIFICAR SERVICIO
        # =====================================

        servicio = session.exec(
            select(Servicio).where(
                Servicio.id == datos.servicio_id,
                Servicio.empresa_id == empresa_id,
                Servicio.cliente_id == datos.cliente_id,
            )
        ).first()

        if not servicio:
            raise HTTPException(
                status_code=404,
                detail="Servicio no encontrado para este cliente",
            )

        # =====================================
        # BUSCAR FACTURA
        # =====================================

        factura = None

        # Primero buscar directamente por factura_id
        if datos.factura_id:

            factura = session.exec(
                select(Factura).where(
                    Factura.id == datos.factura_id,
                    Factura.empresa_id == empresa_id,
                )
            ).first()

        # Si no se envió factura_id, buscar por referencia
        elif datos.referencia:

            factura = session.exec(
                select(Factura).where(
                    Factura.empresa_id == empresa_id,
                    Factura.referencia_pago == datos.referencia,
                )
            ).first()

        # =====================================
        # VALIDAR FACTURA
        # =====================================

        if factura:

            # Verificar cliente
            if factura.cliente_id != datos.cliente_id:
                raise HTTPException(
                    status_code=400,
                    detail=(
                        "La factura pertenece a otro cliente"
                    ),
                )

            # Verificar servicio
            if (
                factura.servicio_id
                and factura.servicio_id != datos.servicio_id
            ):
                raise HTTPException(
                    status_code=400,
                    detail=(
                        "La factura pertenece a otro servicio"
                    ),
                )

            # Verificar si ya está pagada
            if factura.estado == "pagada":
                raise HTTPException(
                    status_code=400,
                    detail="Esta factura ya fue pagada",
                )

            # Verificar monto
            if datos.monto < factura.total:
                raise HTTPException(
                    status_code=400,
                    detail=(
                        f"El monto pagado (${datos.monto}) "
                        f"es menor al valor de la factura "
                        f"(${factura.total})"
                    ),
                )

        # =====================================
        # CREAR EL PAGO
        # =====================================

        pago = Pago(
            empresa_id=empresa_id,
            cliente_id=datos.cliente_id,
            servicio_id=datos.servicio_id,

            factura_id=(
                factura.id
                if factura
                else datos.factura_id
            ),

            monto=datos.monto,

            fecha_pago=(
                datos.fecha_pago
                or datetime.now(timezone.utc)
            ),

            metodo_pago=datos.metodo_pago,
            referencia=datos.referencia,
            estado=datos.estado,
            observaciones=datos.observaciones,
        )

        # Guardar el pago
        session.add(pago)

        # =====================================
        # ACTUALIZAR FACTURA AUTOMÁTICAMENTE
        # =====================================

        if factura:

            factura.estado = "pagada"

            factura.updated_at = datetime.now(
                timezone.utc
            )

            session.add(factura)

        # =====================================
        # REACTIVAR SERVICIO AUTOMÁTICAMENTE
        # =====================================

        if servicio.suspendido:

            servicio.suspendido = False
            servicio.motivo_suspension = None
            servicio.estado = "activo"

            servicio.updated_at = datetime.now(
                timezone.utc
            )

            session.add(servicio)
        # Guardar todos los cambios
        session.commit()

        # Actualizar datos del pago
        session.refresh(pago)

        return pago


# ==========================================
# LISTAR PAGOS
# ==========================================

@router.get(
    "",
    response_model=list[PagoRespuesta],
)
def listar_pagos(
    payload: dict = Depends(obtener_usuario_token),
):

    empresa_id = UUID(payload["empresa_id"])

    with Session(engine) as session:

        pagos = session.exec(
            select(Pago)
            .where(
                Pago.empresa_id == empresa_id
            )
            .order_by(
                Pago.fecha_pago.desc()
            )
        ).all()

        return pagos


# ==========================================
# OBTENER UN PAGO
# ==========================================

@router.get(
    "/{pago_id}",
    response_model=PagoRespuesta,
)
def obtener_pago(
    pago_id: UUID,
    payload: dict = Depends(obtener_usuario_token),
):

    empresa_id = UUID(payload["empresa_id"])

    with Session(engine) as session:

        pago = session.exec(
            select(Pago).where(
                Pago.id == pago_id,
                Pago.empresa_id == empresa_id,
            )
        ).first()

        if not pago:
            raise HTTPException(
                status_code=404,
                detail="Pago no encontrado",
            )

        return pago


# ==========================================
# ACTUALIZAR PAGO
# ==========================================

@router.put(
    "/{pago_id}",
    response_model=PagoRespuesta,
)
def actualizar_pago(
    pago_id: UUID,
    datos: PagoActualizar,
    payload: dict = Depends(obtener_usuario_token),
):

    empresa_id = UUID(payload["empresa_id"])

    with Session(engine) as session:

        pago = session.exec(
            select(Pago).where(
                Pago.id == pago_id,
                Pago.empresa_id == empresa_id,
            )
        ).first()

        if not pago:
            raise HTTPException(
                status_code=404,
                detail="Pago no encontrado",
            )

        cambios = datos.model_dump(
            exclude_unset=True
        )

        for campo, valor in cambios.items():

            setattr(
                pago,
                campo,
                valor,
            )

        pago.updated_at = datetime.now(
            timezone.utc
        )

        session.add(pago)
        session.commit()
        session.refresh(pago)

        return pago


# ==========================================
# ANULAR PAGO
# ==========================================

@router.delete(
    "/{pago_id}",
)
def anular_pago(
    pago_id: UUID,
    payload: dict = Depends(obtener_usuario_token),
):

    empresa_id = UUID(payload["empresa_id"])

    with Session(engine) as session:

        # Buscar el pago
        pago = session.exec(
            select(Pago).where(
                Pago.id == pago_id,
                Pago.empresa_id == empresa_id,
            )
        ).first()

        if not pago:
            raise HTTPException(
                status_code=404,
                detail="Pago no encontrado",
            )

        # Evitar anular dos veces el mismo pago
        if pago.estado == "anulado":
            raise HTTPException(
                status_code=400,
                detail="Este pago ya fue anulado",
            )

        # =====================================
        # BUSCAR LA FACTURA
        # =====================================

        factura = None

        # Primero buscar directamente mediante factura_id
        if pago.factura_id:

            factura = session.exec(
                select(Factura).where(
                    Factura.id == pago.factura_id,
                    Factura.empresa_id == empresa_id,
                )
            ).first()

        # Si no existe factura_id, buscar mediante referencia
        elif pago.referencia:

            factura = session.exec(
                select(Factura).where(
                    Factura.empresa_id == empresa_id,
                    Factura.referencia_pago == pago.referencia,
                )
            ).first()

        # =====================================
        # ANULAR EL PAGO
        # =====================================

        pago.estado = "anulado"

        pago.updated_at = datetime.now(
            timezone.utc
        )

        session.add(pago)

        # Si encontramos la factura, volverla a pendiente
        if factura:

            factura.estado = "pendiente"

            factura.updated_at = datetime.now(
                timezone.utc
            )

            session.add(factura)

        # Guardar todos los cambios
        session.commit()

        return {
            "mensaje": "Pago anulado correctamente",

            "factura_actualizada": (
                factura.numero
                if factura
                else None
            ),
        }