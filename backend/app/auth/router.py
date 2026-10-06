from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlmodel import Session, select

from app.auth.security import (
    crear_access_token,
    obtener_payload_token,
    verificar_password,
)
from app.db.database import engine
from app.models import Usuario


router = APIRouter(
    prefix="/auth",
    tags=["Autenticación"],
)

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="auth/login"
)


@router.post("/login")
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
):
    with Session(engine) as session:

        usuario = session.exec(
            select(Usuario).where(
                Usuario.correo == form_data.username
            )
        ).first()

        if not usuario:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Correo o contraseña incorrectos",
            )

        if not usuario.estado:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Usuario desactivado",
            )

        if not verificar_password(
            form_data.password,
            usuario.password_hash,
        ):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Correo o contraseña incorrectos",
            )

        token = crear_access_token(
            {
                "sub": str(usuario.id),
                "empresa_id": str(usuario.empresa_id),
                "rol_id": str(usuario.rol_id),
            }
        )

        return {
            "access_token": token,
            "token_type": "bearer",
        }


@router.get("/me")
def obtener_usuario_actual(
    token: str = Depends(oauth2_scheme),
):
    try:
        payload = obtener_payload_token(token)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido o expirado",
        )

    usuario_id = payload["sub"]

    with Session(engine) as session:
        usuario = session.get(
            Usuario,
            usuario_id,
        )

        if not usuario:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Usuario no encontrado",
            )

        if not usuario.estado:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Usuario desactivado",
            )

        return {
            "id": str(usuario.id),
            "nombre": usuario.nombre,
            "apellido": usuario.apellido,
            "correo": usuario.correo,
            "empresa_id": str(usuario.empresa_id),
            "rol_id": str(usuario.rol_id),
            "estado": usuario.estado,
        }