from datetime import datetime, timezone
from uuid import UUID
from pathlib import Path
from uuid import uuid4

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
    UploadFile,
    File,
)

from fastapi.security import OAuth2PasswordBearer

from sqlmodel import Session, select

from app.auth.security import obtener_payload_token
from app.db.database import engine
from app.models import (
    Cliente,
    Plan,
    Servicio,
    SolicitudSoporte,
    EvidenciaSoporte,
)

from app.soporte.schemas import (
    SolicitudSoporteCreate,
    SolicitudSoporteUpdate,
    SolicitudSoporteResponse,
)


router = APIRouter(
    prefix="/soporte",
    tags=["Soporte"],
)

# ==========================================
# CARPETA DE EVIDENCIAS
# ==========================================

UPLOADS_DIR = Path(
    "C:/Users/HP/Desktop/fibercore/backend/uploads"
)

UPLOADS_DIR.mkdir(
    parents=True,
    exist_ok=True,
)

# ==========================================
# AUTENTICACIÓN
# ==========================================

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
# CREAR SOLICITUD DE SOPORTE
# ==========================================

@router.post(
    "",
    response_model=SolicitudSoporteResponse,
    status_code=status.HTTP_201_CREATED,
)
def crear_solicitud_soporte(
    datos: SolicitudSoporteCreate,
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

        if datos.servicio_id:

            servicio = session.exec(
                select(Servicio).where(
                    Servicio.id == datos.servicio_id,
                    Servicio.cliente_id == datos.cliente_id,
                    Servicio.empresa_id == empresa_id,
                )
            ).first()

            if not servicio:
                raise HTTPException(
                    status_code=404,
                    detail="Servicio no encontrado para este cliente",
                )

        # =====================================
        # CREAR SOLICITUD
        # =====================================

        solicitud = SolicitudSoporte(

            empresa_id=empresa_id,

            cliente_id=datos.cliente_id,

            servicio_id=datos.servicio_id,

            descripcion=datos.descripcion,

            prioridad=datos.prioridad,

            origen=datos.origen,

            estado="pendiente",
        )

        session.add(solicitud)

        session.commit()

        session.refresh(solicitud)

        return solicitud


# ==========================================
# LISTAR TODAS LAS SOLICITUDES
# ==========================================

@router.get(
    "",
    response_model=list[SolicitudSoporteResponse],
)
def listar_solicitudes_soporte(
    payload: dict = Depends(obtener_usuario_token),
):

    empresa_id = UUID(payload["empresa_id"])

    with Session(engine) as session:

        solicitudes = session.exec(

            select(SolicitudSoporte)
            .where(
                SolicitudSoporte.empresa_id == empresa_id
            )
            .order_by(
                SolicitudSoporte.created_at.desc()
            )

        ).all()

        return solicitudes

# ==========================================
# LISTAR TRABAJOS DEL TÉCNICO
# ==========================================
@router.get(
    "/mis-trabajos",
    response_model=list[SolicitudSoporteResponse],
)
def listar_mis_trabajos(
    payload: dict = Depends(obtener_usuario_token),
):

    empresa_id = UUID(payload["empresa_id"])
    tecnico_id = UUID(payload["sub"])

    with Session(engine) as session:

        solicitudes = session.exec(
            select(SolicitudSoporte)
            .where(
                SolicitudSoporte.empresa_id == empresa_id,
                SolicitudSoporte.tecnico_id == tecnico_id,
            )
            .order_by(
                SolicitudSoporte.created_at.desc()
            )
        ).all()

        resultados = []

        for solicitud in solicitudes:

            cliente = session.exec(
                select(Cliente).where(
                    Cliente.id == solicitud.cliente_id,
                    Cliente.empresa_id == empresa_id,
                )
            ).first()

            servicio = None
            plan = None

            if solicitud.servicio_id:
                servicio = session.exec(
                    select(Servicio).where(
                       Servicio.id == solicitud.servicio_id,
                        Servicio.empresa_id == empresa_id,
                    )
                ).first()

            if servicio:
                plan = session.exec(
                    select(Plan).where(
                        Plan.id == servicio.plan_id,
                        Plan.empresa_id == empresa_id,
                    )
                ).first()

            resultados.append(
                SolicitudSoporteResponse(
                    id=solicitud.id,
                    empresa_id=solicitud.empresa_id,
                    cliente_id=solicitud.cliente_id,
                    servicio_id=solicitud.servicio_id,
                    descripcion=solicitud.descripcion,
                    estado=solicitud.estado,
                    prioridad=solicitud.prioridad,
                    origen=solicitud.origen,
                    tecnico_id=solicitud.tecnico_id,

                    cliente_nombre=(
                        f"{cliente.nombre} {cliente.apellido or ''}".strip()
                        if cliente
                        else None
                    ),

                    cliente_telefono=(
                        cliente.telefono
                        if cliente
                        else None
                    ),

                    cliente_direccion=(
                        cliente.direccion
                        if cliente
                        else None
                    ),

                    cliente_ciudad=(
                        cliente.ciudad
                        if cliente
                        else None
                    ),

                    cliente_barrio=(
                        cliente.barrio
                        if cliente
                        else None
                    ),

                    cliente_referencia=(
                        cliente.referencia_direccion
                        if cliente
                        else None
                    ),

                    created_at=solicitud.created_at,
                    updated_at=solicitud.updated_at,
                )
            )

        return resultados
# ==========================================
# OBTENER SOLICITUD ESPECÍFICA
# ==========================================

@router.get(
    "/{solicitud_id}",
    response_model=SolicitudSoporteResponse,
)
def obtener_solicitud_soporte(
    solicitud_id: UUID,
    payload: dict = Depends(obtener_usuario_token),
):

    empresa_id = UUID(payload["empresa_id"])

    with Session(engine) as session:

        solicitud = session.exec(

            select(SolicitudSoporte).where(
                SolicitudSoporte.id == solicitud_id,
                SolicitudSoporte.empresa_id == empresa_id,
            )

        ).first()

        if not solicitud:

            raise HTTPException(
                status_code=404,
                detail="Solicitud de soporte no encontrada",
            )

        return solicitud


# ==========================================
# ACTUALIZAR SOLICITUD
# ==========================================

@router.put(
    "/{solicitud_id}",
    response_model=SolicitudSoporteResponse,
)
def actualizar_solicitud_soporte(
    solicitud_id: UUID,
    datos: SolicitudSoporteUpdate,
    payload: dict = Depends(obtener_usuario_token),
):

    empresa_id = UUID(payload["empresa_id"])

    with Session(engine) as session:

        solicitud = session.exec(
            select(SolicitudSoporte).where(
                SolicitudSoporte.id == solicitud_id,
                SolicitudSoporte.empresa_id == empresa_id,
            )
        ).first()

        if not solicitud:
            raise HTTPException(
                status_code=404,
                detail="Solicitud de soporte no encontrada",
            )

        # ==========================================
        # SEGURIDAD PARA TÉCNICOS
        # ==========================================

        rol_id = payload.get("rol_id")
        usuario_id = UUID(payload["sub"])

        ROL_TECNICO = UUID(
            "e8b67fd6-6f1a-4d3e-a013-8599170cf7c5"
        )

        if rol_id == str(ROL_TECNICO):

            if solicitud.tecnico_id != usuario_id:
                raise HTTPException(
                    status_code=403,
                    detail="No tienes permiso para modificar este trabajo",
                )

        # ==========================================
        # APLICAR CAMBIOS
        # ==========================================

        cambios = datos.model_dump(
            exclude_unset=True
        )

        for campo, valor in cambios.items():
            setattr(
                solicitud,
                campo,
                valor,
            )

        solicitud.updated_at = datetime.now(
            timezone.utc
        )

        session.add(solicitud)

        session.commit()

        session.refresh(solicitud)

        # ==========================================
        # OBTENER CLIENTE
        # ==========================================

        cliente = session.exec(
            select(Cliente).where(
                Cliente.id == solicitud.cliente_id,
                Cliente.empresa_id == empresa_id,
            )
        ).first()

        # ==========================================
        # OBTENER SERVICIO
        # ==========================================

        servicio = None
        plan = None

        if solicitud.servicio_id:

            servicio = session.exec(
                select(Servicio).where(
                    Servicio.id == solicitud.servicio_id,
                    Servicio.empresa_id == empresa_id,
                )
            ).first()

        # ==========================================
        # OBTENER PLAN
        # ==========================================

        if servicio:

            plan = session.exec(
                select(Plan).where(
                    Plan.id == servicio.plan_id,
                    Plan.empresa_id == empresa_id,
                )
            ).first()

        # ==========================================
        # DEVOLVER RESPUESTA COMPLETA
        # ==========================================

        return SolicitudSoporteResponse(

            id=solicitud.id,

            empresa_id=solicitud.empresa_id,

            cliente_id=solicitud.cliente_id,

            servicio_id=solicitud.servicio_id,

            descripcion=solicitud.descripcion,

            estado=solicitud.estado,

            prioridad=solicitud.prioridad,

            origen=solicitud.origen,

            tecnico_id=solicitud.tecnico_id,

            # Información del servicio
            servicio_tipo=(
                servicio.tipo if servicio else None
            ),

            servicio_usuario_pppoe=(
                servicio.usuario_pppoe
                if servicio
                else None
            ),

            servicio_estado=(
                servicio.estado
                if servicio
                else None
            ),

            servicio_suspendido=(
                servicio.suspendido
                if servicio
                else None
            ),

            # Información del plan
            plan_nombre=(
                plan.nombre
                if plan
                else None
            ),

            plan_velocidad_bajada=(
                plan.velocidad_bajada
                if plan
                else None
            ),

            plan_velocidad_subida=(
                plan.velocidad_subida
                if plan
                else None
            ),

            plan_precio_mensual=(
                plan.precio_mensual
                if plan
                else None
            ),

            # Información del cliente
            cliente_nombre=(
                f"{cliente.nombre} {cliente.apellido or ''}".strip()
                if cliente
                else None
            ),

            cliente_telefono=(
                cliente.telefono
                if cliente
                else None
            ),

            cliente_direccion=(
                cliente.direccion
                if cliente
                else None
            ),

            cliente_ciudad=(
                cliente.ciudad
                if cliente
                else None
            ),

            cliente_barrio=(
                cliente.barrio
                if cliente
                else None
            ),

            cliente_referencia=(
                cliente.referencia_direccion
                if cliente
                else None
            ),

            created_at=solicitud.created_at,

            updated_at=solicitud.updated_at,
        )


# ==========================================
# SUBIR EVIDENCIA FOTOGRÁFICA
# ==========================================

@router.post(
    "/{solicitud_id}/evidencias",
)
async def subir_evidencia(
    solicitud_id: UUID,
    archivo: UploadFile = File(...),
    payload: dict = Depends(obtener_usuario_token),
):

    empresa_id = UUID(payload["empresa_id"])
    tecnico_id = UUID(payload["sub"])

    with Session(engine) as session:

        # ==========================================
        # BUSCAR SOLICITUD
        # ==========================================

        solicitud = session.exec(
            select(SolicitudSoporte).where(
                SolicitudSoporte.id == solicitud_id,
                SolicitudSoporte.empresa_id == empresa_id,
            )
        ).first()

        if not solicitud:
            raise HTTPException(
                status_code=404,
                detail="Solicitud de soporte no encontrada",
            )

        # ==========================================
        # VERIFICAR TÉCNICO
        # ==========================================

        if solicitud.tecnico_id != tecnico_id:
            raise HTTPException(
                status_code=403,
                detail="No tienes permiso para subir evidencia de este trabajo",
            )

        # ==========================================
        # VERIFICAR TIPO DE ARCHIVO
        # ==========================================

        tipos_permitidos = {
            "image/jpeg",
            "image/png",
            "image/webp",
        }

        if archivo.content_type not in tipos_permitidos:
            raise HTTPException(
                status_code=400,
                detail="Solo se permiten imágenes JPG, PNG o WEBP",
            )

        # ==========================================
        # VERIFICAR EXTENSIÓN
        # ==========================================

        extension = Path(
            archivo.filename or ""
        ).suffix.lower()

        if extension not in {
            ".jpg",
            ".jpeg",
            ".png",
            ".webp",
        }:
            raise HTTPException(
                status_code=400,
                detail="Extensión de imagen no permitida",
            )

        # ==========================================
        # GENERAR NOMBRE ÚNICO
        # ==========================================

        nombre_archivo = (
            f"{solicitud_id}_"
            f"{uuid4()}"
            f"{extension}"
        )

        ruta_archivo = UPLOADS_DIR / nombre_archivo

        # ==========================================
        # GUARDAR ARCHIVO
        # ==========================================

        contenido = await archivo.read()

        with open(
            ruta_archivo,
            "wb",
        ) as archivo_destino:

            archivo_destino.write(
                contenido
            )

        # ==========================================
        # GUARDAR REGISTRO EN BASE DE DATOS
        # ==========================================

        evidencia = EvidenciaSoporte(
            solicitud_id=solicitud.id,
            empresa_id=empresa_id,
            tecnico_id=tecnico_id,
            archivo_url=f"/uploads/{nombre_archivo}",
            tipo="foto",
        )

        session.add(evidencia)

        session.commit()

        session.refresh(evidencia)

        return {
            "mensaje": "Evidencia subida correctamente",
            "id": str(evidencia.id),
            "archivo_url": evidencia.archivo_url,
        }


# ==========================================
# LISTAR EVIDENCIAS DE UN TRABAJO
# ==========================================

@router.get(
    "/{solicitud_id}/evidencias",
)
def listar_evidencias(
    solicitud_id: UUID,
    payload: dict = Depends(obtener_usuario_token),
):

    empresa_id = UUID(payload["empresa_id"])
    usuario_id = UUID(payload["sub"])

    with Session(engine) as session:

        # ==========================================
        # BUSCAR SOLICITUD
        # ==========================================

        solicitud = session.exec(
            select(SolicitudSoporte).where(
                SolicitudSoporte.id == solicitud_id,
                SolicitudSoporte.empresa_id == empresa_id,
            )
        ).first()

        if not solicitud:
            raise HTTPException(
                status_code=404,
                detail="Solicitud de soporte no encontrada",
            )

        # ==========================================
        # VERIFICAR ACCESO DEL TÉCNICO
        # ==========================================

        rol_id = payload.get("rol_id")

        ROL_TECNICO = UUID(
            "e8b67fd6-6f1a-4d3e-a013-8599170cf7c5"
        )

        if rol_id == str(ROL_TECNICO):

            if solicitud.tecnico_id != usuario_id:
                raise HTTPException(
                    status_code=403,
                    detail="No tienes permiso para ver estas evidencias",
                )

        # ==========================================
        # BUSCAR EVIDENCIAS
        # ==========================================

        evidencias = session.exec(
            select(EvidenciaSoporte)
            .where(
                EvidenciaSoporte.solicitud_id == solicitud_id,
                EvidenciaSoporte.empresa_id == empresa_id,
            )
            .order_by(
                EvidenciaSoporte.created_at.desc()
            )
        ).all()

        return [
            {
                "id": str(evidencia.id),
                "solicitud_id": str(
                    evidencia.solicitud_id
                ),
                "tecnico_id": str(
                    evidencia.tecnico_id
                ),
                "archivo_url": evidencia.archivo_url,
                "tipo": evidencia.tipo,
                "descripcion": evidencia.descripcion,
                "created_at": evidencia.created_at,
            }
            for evidencia in evidencias
        ]