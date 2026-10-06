from datetime import datetime, timezone
from pathlib import Path
from uuid import UUID, uuid4


from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    UploadFile,
)

from fastapi.security import OAuth2PasswordBearer

from sqlmodel import Session, select

from app.auth.security import obtener_payload_token
from app.db.database import engine

from app.models import (
    Cliente,
    ComprobantePago,
    Factura,
)

from app.services.validador_comprobante import extraer_datos_comprobante

from app.pagos.schemas import PagoCrear
from app.pagos.router import crear_pago
from app.services.validacion_pago import validar_comprobante

router = APIRouter(
    prefix="/pagos/comprobantes",
    tags=["Comprobantes de Pago"],
)


oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/auth/login"
)


UPLOADS_DIR = Path(
    "C:/Users/HP/Desktop/fibercore/backend/uploads"
)

UPLOADS_DIR.mkdir(
    parents=True,
    exist_ok=True,
)


# ============================================================
# AUTENTICACIÓN
# ============================================================

def obtener_usuario_token(
    token: str = Depends(oauth2_scheme),
):
    try:
        return obtener_payload_token(token)

    except ValueError:
        raise HTTPException(
            status_code=401,
            detail="Token inválido o expirado",
        )


# ============================================================
# RECIBIR COMPROBANTE CON REFERENCIA OPTICORE
# ============================================================

@router.post("")
async def recibir_comprobante(
    referencia: str = Form(...),
    archivo: UploadFile = File(...),
    payload: dict = Depends(obtener_usuario_token),
):
    empresa_id = UUID(payload["empresa_id"])

    referencia = referencia.strip()

    if not referencia:
        raise HTTPException(
            status_code=400,
            detail="La referencia de pago es obligatoria",
        )

    with Session(engine) as session:

        # ====================================================
        # BUSCAR FACTURA POR REFERENCIA OPTICORE
        # ====================================================

        factura = session.exec(
            select(Factura).where(
                Factura.empresa_id == empresa_id,
                Factura.referencia_pago == referencia,
            )
        ).first()

        if not factura:
            raise HTTPException(
                status_code=404,
                detail=(
                    f"No existe una factura con la referencia "
                    f"{referencia}"
                ),
            )

        # ====================================================
        # VERIFICAR ESTADO DE LA FACTURA
        # ====================================================

        if factura.estado == "pagada":
            raise HTTPException(
                status_code=400,
                detail="Esta factura ya está pagada",
            )

        # ====================================================
        # VERIFICAR CLIENTE
        # ====================================================

        cliente = session.exec(
            select(Cliente).where(
                Cliente.id == factura.cliente_id,
                Cliente.empresa_id == empresa_id,
            )
        ).first()

        if not cliente:
            raise HTTPException(
                status_code=404,
                detail="Cliente de la factura no encontrado",
            )

        # ====================================================
        # VERIFICAR ARCHIVO
        # ====================================================

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

        # ====================================================
        # GENERAR NOMBRE ÚNICO
        # ====================================================

        nombre_archivo = (
            f"comprobante_"
            f"{factura.id}_"
            f"{uuid4()}"
            f"{extension}"
        )

        ruta_archivo = UPLOADS_DIR / nombre_archivo

        # ====================================================
        # GUARDAR ARCHIVO
        # ====================================================

        contenido = await archivo.read()

        if not contenido:
            raise HTTPException(
                status_code=400,
                detail="El archivo está vacío",
            )

        with open(
            ruta_archivo,
            "wb",
        ) as archivo_destino:
            archivo_destino.write(
                contenido
            )

        # ====================================================
        # EXTRAER DATOS DEL COMPROBANTE CON OCR
        # ====================================================

        try:
            datos_ocr = extraer_datos_comprobante(
                str(ruta_archivo)
            )

        except Exception as error:
            raise HTTPException(
                status_code=500,
                detail=f"No se pudo analizar el comprobante: {error}",
            )

        # ====================================================
        # CREAR COMPROBANTE
        # ====================================================

        comprobante = ComprobantePago(
            empresa_id=empresa_id,
            cliente_id=cliente.id,
            factura_id=factura.id,
            pago_id=None,
            archivo_url=f"/uploads/{nombre_archivo}",
            nombre_archivo=archivo.filename,
            estado_validacion="en_revision",
            monto_detectado=datos_ocr["monto_detectado"],
            fecha_detectada=datos_ocr["fecha_detectada"],
            banco_detectado=datos_ocr["banco_detectado"],
            destinatario_detectado=datos_ocr["destinatario_detectado"],
            referencia_detectada=datos_ocr["referencia_detectada"],
            observaciones=(
                f"Referencia OptiCore recibida: {referencia}"
            ),
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )

        session.add(comprobante)
        session.commit()
        session.refresh(comprobante)

        return {
            "mensaje": "Comprobante recibido correctamente",
            "comprobante_id": str(comprobante.id),
            "factura_id": str(factura.id),
            "numero_factura": factura.numero,
            "referencia_opticore": referencia,
            "cliente_id": str(cliente.id),
            "monto_factura": factura.total,
            "estado_validacion": comprobante.estado_validacion,
            "archivo_url": comprobante.archivo_url,
        }


# ============================================================
# LISTAR COMPROBANTES
# ============================================================

@router.get("")
def listar_comprobantes(
    payload: dict = Depends(obtener_usuario_token),
):
    empresa_id = UUID(payload["empresa_id"])

    with Session(engine) as session:

        comprobantes = session.exec(
            select(ComprobantePago)
            .where(
                ComprobantePago.empresa_id == empresa_id
            )
            .order_by(
                ComprobantePago.created_at.desc()
            )
        ).all()

        return [
            {
                "id": str(comprobante.id),

                "cliente_id": str(
                    comprobante.cliente_id
                ),

                "factura_id": (
                    str(comprobante.factura_id)
                    if comprobante.factura_id
                    else None
                ),

                "pago_id": (
                    str(comprobante.pago_id)
                    if comprobante.pago_id
                    else None
                ),

                "archivo_url": comprobante.archivo_url,

                "nombre_archivo": (
                    comprobante.nombre_archivo
                ),

                "estado_validacion": (
                    comprobante.estado_validacion
                ),

                "monto_detectado": (
                    comprobante.monto_detectado
                ),

                "fecha_detectada": (
                    comprobante.fecha_detectada
                ),

                "banco_detectado": (
                    comprobante.banco_detectado
                ),

                "destinatario_detectado": (
                    comprobante.destinatario_detectado
                ),

                "referencia_detectada": (
                    comprobante.referencia_detectada
                ),

                "observaciones": (
                    comprobante.observaciones
                ),

                "created_at": (
                    comprobante.created_at
                ),

                "updated_at": (
                    comprobante.updated_at
                ),
            }

            for comprobante in comprobantes
        ]


# ============================================================
# REPROCESAR COMPROBANTE CON OCR
# ============================================================

@router.post("/{comprobante_id}/reprocesar")
def reprocesar_comprobante(
    comprobante_id: UUID,
    payload: dict = Depends(obtener_usuario_token),
):
    empresa_id = UUID(payload["empresa_id"])

    with Session(engine) as session:

        # ====================================================
        # BUSCAR COMPROBANTE
        # ====================================================

        comprobante = session.exec(
            select(ComprobantePago).where(
                ComprobantePago.id == comprobante_id,
                ComprobantePago.empresa_id == empresa_id,
            )
        ).first()

        if not comprobante:
            raise HTTPException(
                status_code=404,
                detail="Comprobante no encontrado",
            )

        # ====================================================
        # OBTENER ARCHIVO FÍSICO
        # ====================================================

        if not comprobante.archivo_url:
            raise HTTPException(
                status_code=400,
                detail="El comprobante no tiene archivo asociado",
            )

        nombre_archivo = Path(
            comprobante.archivo_url
        ).name

        ruta_archivo = UPLOADS_DIR / nombre_archivo

        if not ruta_archivo.exists():
            raise HTTPException(
                status_code=404,
                detail=(
                    f"No se encontró el archivo del comprobante: "
                    f"{nombre_archivo}"
                ),
            )

        # ====================================================
        # EJECUTAR OCR NUEVAMENTE
        # ====================================================

        try:
            datos_ocr = extraer_datos_comprobante(
                str(ruta_archivo)
            )

        except Exception as error:
            raise HTTPException(
                status_code=500,
                detail=(
                    f"No se pudo reprocesar el comprobante: "
                    f"{error}"
                ),
            )

        # ====================================================
        # ACTUALIZAR DATOS EXTRAÍDOS
        # ====================================================

        comprobante.monto_detectado = (
            datos_ocr["monto_detectado"]
        )

        comprobante.fecha_detectada = (
            datos_ocr["fecha_detectada"]
        )

        comprobante.banco_detectado = (
            datos_ocr["banco_detectado"]
        )

        comprobante.destinatario_detectado = (
            datos_ocr["destinatario_detectado"]
        )

        comprobante.referencia_detectada = (
            datos_ocr["referencia_detectada"]
        )

        comprobante.updated_at = (
            datetime.now(timezone.utc)
        )

        # ====================================================
        # IMPORTANTE:
        # NO CAMBIAMOS EL ESTADO
        # ====================================================

        session.add(comprobante)
        session.commit()
        session.refresh(comprobante)

        return {
            "mensaje": "Comprobante reprocesado correctamente",

            "comprobante_id": str(
                comprobante.id
            ),

            "estado_validacion": (
                comprobante.estado_validacion
            ),

            "monto_detectado": (
                comprobante.monto_detectado
            ),

            "fecha_detectada": (
                comprobante.fecha_detectada
            ),

            "banco_detectado": (
                comprobante.banco_detectado
            ),

            "destinatario_detectado": (
                comprobante.destinatario_detectado
            ),

            "referencia_detectada": (
                comprobante.referencia_detectada
            ),
        }

# ============================================================
# VALIDAR Y APLICAR COMPROBANTE
# ============================================================

@router.post("/{comprobante_id}/validar")
def validar_y_aplicar_comprobante(
    comprobante_id: UUID,
    payload: dict = Depends(obtener_usuario_token),
):
    empresa_id = UUID(payload["empresa_id"])

    with Session(engine) as session:

        # ====================================================
        # BUSCAR COMPROBANTE
        # ====================================================

        comprobante = session.exec(
            select(ComprobantePago).where(
                ComprobantePago.id == comprobante_id,
                ComprobantePago.empresa_id == empresa_id,
            )
        ).first()

        if not comprobante:
            raise HTTPException(
                status_code=404,
                detail="Comprobante no encontrado",
            )

        # ====================================================
        # EVITAR PROCESAR DOS VECES
        # ====================================================

        if comprobante.pago_id:
            raise HTTPException(
                status_code=400,
                detail="Este comprobante ya tiene un pago aplicado",
            )

        # ====================================================
        # BUSCAR FACTURA
        # ====================================================

        if not comprobante.factura_id:
            raise HTTPException(
                status_code=400,
                detail="El comprobante no tiene factura asociada",
            )

        factura = session.exec(
            select(Factura).where(
                Factura.id == comprobante.factura_id,
                Factura.empresa_id == empresa_id,
            )
        ).first()

        if not factura:
            raise HTTPException(
                status_code=404,
                detail="Factura asociada no encontrada",
            )

        # ====================================================
        # VERIFICAR QUE LA FACTURA NO ESTÉ PAGADA
        # ====================================================

        if factura.estado == "pagada":
            raise HTTPException(
                status_code=400,
                detail="La factura ya está pagada",
            )

        # ====================================================
        # OBTENER SERVICIO
        # ====================================================

        if not factura.servicio_id:
            raise HTTPException(
                status_code=400,
                detail="La factura no tiene servicio asociado",
            )

        # ====================================================
        # EJECUTAR VALIDACIÓN
        # ====================================================

        resultado = validar_comprobante(
            monto_detectado=comprobante.monto_detectado,
            monto_factura=factura.total,
            banco_detectado=comprobante.banco_detectado,
            destinatario_detectado=comprobante.destinatario_detectado,
            fecha_detectada=comprobante.fecha_detectada,
            fecha_emision=factura.fecha_emision,
        )

        # ====================================================
        # GUARDAR RESULTADO DE VALIDACIÓN
        # ====================================================

        if resultado["estado"] != "validado":

            comprobante.estado_validacion = "rechazado"

            comprobante.observaciones = (
                f"{comprobante.observaciones or ''}\n"
                f"Validación rechazada: "
                f"{'; '.join(resultado['errores'])}"
            ).strip()

            comprobante.updated_at = datetime.now(
                timezone.utc
            )

            session.add(comprobante)
            session.commit()
            session.refresh(comprobante)

            return {
                "mensaje": "Comprobante rechazado",
                "comprobante_id": str(comprobante.id),
                "estado_validacion": comprobante.estado_validacion,
                "validaciones": resultado["validaciones"],
                "errores": resultado["errores"],
            }

        # ====================================================
        # CREAR PAGO USANDO LA LÓGICA EXISTENTE
        # ====================================================

        datos_pago = PagoCrear(
            cliente_id=comprobante.cliente_id,
            servicio_id=factura.servicio_id,
            factura_id=factura.id,
            monto=comprobante.monto_detectado,
            fecha_pago=comprobante.fecha_detectada,
            metodo_pago="transferencia",
            referencia=factura.referencia_pago,
            estado="pagado",
            observaciones=(
                f"Pago validado automáticamente desde comprobante "
                f"{comprobante.id}. "
                f"Referencia bancaria: "
                f"{comprobante.referencia_detectada or 'No detectada'}"
            ),
        )

        # ====================================================
        # REUTILIZAR CREAR_PAGO EXISTENTE
        # ====================================================

        pago = crear_pago(
            datos=datos_pago,
            payload=payload,
        )

        # ====================================================
        # RELACIONAR COMPROBANTE CON EL PAGO
        # ====================================================

        comprobante.pago_id = pago.id
        comprobante.estado_validacion = "validado"

        comprobante.observaciones = (
            f"{comprobante.observaciones or ''}\n"
            f"Pago aplicado correctamente. "
            f"ID del pago: {pago.id}"
        ).strip()

        comprobante.updated_at = datetime.now(
            timezone.utc
        )

        session.add(comprobante)
        session.commit()
        session.refresh(comprobante)

        return {
            "mensaje": "Comprobante validado y pago aplicado correctamente",
            "comprobante_id": str(comprobante.id),
            "pago_id": str(pago.id),
            "factura_id": str(factura.id),
            "numero_factura": factura.numero,
            "referencia_opticore": factura.referencia_pago,
            "monto": comprobante.monto_detectado,
            "estado_validacion": comprobante.estado_validacion,
            "estado_factura": "pagada",
            "validaciones": resultado["validaciones"],
            "errores": resultado["errores"],
        }