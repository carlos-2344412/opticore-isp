from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select

from app.auth.security import obtener_payload_token
from app.db.database import engine
from app.models import Cliente

from fastapi.security import OAuth2PasswordBearer

from app.clientes.schemas import (
    ClienteActualizar,
    ClienteCrear,
    ClienteRespuesta,
)


router = APIRouter(
    prefix="/clientes",
    tags=["Clientes"],
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
    response_model=ClienteRespuesta,
    status_code=status.HTTP_201_CREATED,
)
def crear_cliente(
    datos: ClienteCrear,
    payload: dict = Depends(obtener_usuario_token),
):
    empresa_id = UUID(payload["empresa_id"])

    with Session(engine) as session:

        cliente = Cliente(
            empresa_id=empresa_id,
            documento=datos.documento,
            nombre=datos.nombre,
            apellido=datos.apellido,
            telefono=datos.telefono,
            correo=datos.correo,
            direccion=datos.direccion,
            ciudad=datos.ciudad,
            barrio=datos.barrio,
            referencia_direccion=datos.referencia_direccion,
            estado="activo",
        )

        session.add(cliente)
        session.commit()
        session.refresh(cliente)

        return cliente


@router.get(
    "",
    response_model=list[ClienteRespuesta],
)
def listar_clientes(
    payload: dict = Depends(obtener_usuario_token),
):
    empresa_id = UUID(payload["empresa_id"])

    with Session(engine) as session:

        clientes = session.exec(
            select(Cliente)
            .where(
                Cliente.empresa_id == empresa_id
            )
            .order_by(Cliente.nombre)
        ).all()

        return clientes


@router.get(
    "/{cliente_id}",
    response_model=ClienteRespuesta,
)
def obtener_cliente(
    cliente_id: UUID,
    payload: dict = Depends(obtener_usuario_token),
):
    empresa_id = UUID(payload["empresa_id"])

    with Session(engine) as session:

        cliente = session.exec(
            select(Cliente)
            .where(
                Cliente.id == cliente_id,
                Cliente.empresa_id == empresa_id,
            )
        ).first()

        if not cliente:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Cliente no encontrado",
            )

        return cliente


@router.put(
    "/{cliente_id}",
    response_model=ClienteRespuesta,
)
def actualizar_cliente(
    cliente_id: UUID,
    datos: ClienteActualizar,
    payload: dict = Depends(obtener_usuario_token),
):
    empresa_id = UUID(payload["empresa_id"])

    with Session(engine) as session:

        cliente = session.exec(
            select(Cliente)
            .where(
                Cliente.id == cliente_id,
                Cliente.empresa_id == empresa_id,
            )
        ).first()

        if not cliente:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Cliente no encontrado",
            )

        cambios = datos.model_dump(
            exclude_unset=True
        )

        for campo, valor in cambios.items():
            setattr(cliente, campo, valor)

        cliente.updated_at = datetime.now(
            timezone.utc
        )

        session.add(cliente)
        session.commit()
        session.refresh(cliente)

        return cliente


@router.delete(
    "/{cliente_id}",
)
def desactivar_cliente(
    cliente_id: UUID,
    payload: dict = Depends(obtener_usuario_token),
):
    empresa_id = UUID(payload["empresa_id"])

    with Session(engine) as session:

        cliente = session.exec(
            select(Cliente)
            .where(
                Cliente.id == cliente_id,
                Cliente.empresa_id == empresa_id,
            )
        ).first()

        if not cliente:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Cliente no encontrado",
            )

        cliente.estado = "inactivo"
        cliente.updated_at = datetime.now(
            timezone.utc
        )

        session.add(cliente)
        session.commit()

        return {
            "mensaje": "Cliente desactivado correctamente"
        }