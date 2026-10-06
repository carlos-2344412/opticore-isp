from datetime import datetime, timedelta, timezone

from jose import jwt
from passlib.context import CryptContext


SECRET_KEY = "CAMBIAR_EN_PRODUCCION"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60


pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
)


def verificar_password(
    password: str,
    password_hash: str,
) -> bool:
    return pwd_context.verify(password, password_hash)


def crear_access_token(data: dict) -> str:
    payload = data.copy()

    expire = datetime.now(timezone.utc) + timedelta(
        minutes=ACCESS_TOKEN_EXPIRE_MINUTES
    )

    payload["exp"] = expire

    return jwt.encode(
        payload,
        SECRET_KEY,
        algorithm=ALGORITHM,
    )

from jose import JWTError


def obtener_payload_token(token: str) -> dict:
    try:
        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM],
        )

        if not payload.get("sub"):
            raise ValueError("Token sin usuario")

        return payload

    except (JWTError, ValueError):
        raise ValueError("Token inválido")