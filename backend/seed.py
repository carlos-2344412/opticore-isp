from sqlmodel import Session, select

from app.core.config import settings
from app.db.database import engine
from app.models import Empresa, Rol, Usuario

from passlib.context import CryptContext


pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
)


def crear_datos_iniciales():
    with Session(engine) as session:

        # -------------------------
        # EMPRESA
        # -------------------------
        empresa = session.exec(
            select(Empresa).where(
                Empresa.nit == "900000000-1"
            )
        ).first()

        if not empresa:
            empresa = Empresa(
                nombre="OPTIRÁPIDO",
                nit="900000000-1",
                telefono="",
                correo="",
                direccion="",
                ciudad="",
                departamento="",
                estado=True,
            )

            session.add(empresa)
            session.commit()
            session.refresh(empresa)

            print("Empresa creada.")
        else:
            print("La empresa ya existe.")

        # -------------------------
        # ROL ADMINISTRADOR
        # -------------------------
        rol = session.exec(
            select(Rol).where(
                Rol.nombre == "Administrador"
            )
        ).first()

        if not rol:
            rol = Rol(
                nombre="Administrador",
                descripcion="Acceso completo al sistema.",
                estado=True,
            )

            session.add(rol)
            session.commit()
            session.refresh(rol)

            print("Rol Administrador creado.")
        else:
            print("El rol Administrador ya existe.")

        # -------------------------
        # USUARIO ADMINISTRADOR
        # -------------------------
        correo_admin = "admin@optirapido.com"

        usuario = session.exec(
            select(Usuario).where(
                Usuario.correo == correo_admin
            )
        ).first()

        if not usuario:

            password_temporal = "OptiCore2026!"

            usuario = Usuario(
                empresa_id=empresa.id,
                rol_id=rol.id,
                nombre="Administrador",
                apellido="Principal",
                correo=correo_admin,
                telefono="",
                password_hash=pwd_context.hash(
                    password_temporal
                ),
                estado=True,
            )

            session.add(usuario)
            session.commit()

            print("Usuario administrador creado.")
            print(f"Correo: {correo_admin}")
            print(f"Contraseña temporal: {password_temporal}")

        else:
            print("El usuario administrador ya existe.")


if __name__ == "__main__":
    crear_datos_iniciales()