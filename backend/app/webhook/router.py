from fastapi import APIRouter, Request
from fastapi.responses import PlainTextResponse
from sqlmodel import Session

from app.chatbot.service import procesar_mensaje
from app.db.database import engine

from app.webhook.whatsapp import (
    enviar_mensaje_whatsapp,
    descargar_imagen_whatsapp,
)

import os
from datetime import datetime


router = APIRouter(
    prefix="/webhook/whatsapp",
    tags=["WhatsApp Webhook"],
)


VERIFY_TOKEN = "fibercore_whatsapp_2026"


@router.post("/voz")
async def recibir_llamada_voz():
    return PlainTextResponse(
        """<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say language="es-CO" voice="Polly.Mia">
        Hola, bienvenido a OPTIRÁPIDO. Esta es una prueba del asistente virtual.
    </Say>
</Response>""",
        media_type="application/xml",
    )


@router.get("")
async def verificar_webhook(request: Request):
    params = request.query_params

    mode = params.get("hub.mode")
    token = params.get("hub.verify_token")
    challenge = params.get("hub.challenge")

    if mode == "subscribe" and token == VERIFY_TOKEN:
        return PlainTextResponse(challenge or "")

    return PlainTextResponse(
        "Token de verificación incorrecto",
        status_code=403,
    )


@router.post("")
async def recibir_webhook(request: Request):
    data = await request.json()

    try:
        value = data["entry"][0]["changes"][0]["value"]
        messages = value.get("messages", [])

        if not messages:
            return {"status": "EVENT_RECEIVED"}

        mensaje = messages[0]

        tipo_mensaje = mensaje.get("type")

        # ==========================================
        # MENSAJE DE TEXTO
        # ==========================================

        if tipo_mensaje == "text":

            numero = mensaje["from"]
            texto = mensaje["text"]["body"]

            print("\n========== MENSAJE WHATSAPP ==========")
            print("Número:", numero)
            print("Mensaje:", texto)
            print("======================================")

            with Session(engine) as session:
                respuesta = procesar_mensaje(
                    session=session,
                    empresa_id="29241149-5806-4f7d-bf31-13041f187799",
                    telefono=numero,
                    mensaje=texto,
                )

            print("Respuesta del chatbot:", respuesta)

            await enviar_mensaje_whatsapp(
                numero_destino=numero,
                mensaje=respuesta["respuesta"],
            )

            return {
                "status": "TEXT_PROCESSED"
            }

        # ==========================================
        # IMAGEN / COMPROBANTE
        # ==========================================

        if tipo_mensaje == "image":

            numero = mensaje["from"]

            imagen = mensaje["image"]

            media_id = imagen.get("id")

            caption = imagen.get("caption", "")

            print("\n========== COMPROBANTE WHATSAPP ==========")
            print("Número:", numero)
            print("Media ID:", media_id)
            print("Referencia enviada:", caption)
            print("==========================================")

            if not media_id:
                print(
                    "ERROR: WhatsApp no envió media_id."
                )

                await enviar_mensaje_whatsapp(
                    numero_destino=numero,
                    mensaje=(
                        "No pude identificar el comprobante "
                        "recibido. Por favor envía nuevamente "
                        "la imagen."
                    ),
                )

                return {
                    "status": "IMAGE_ERROR"
                }

            # ==========================================
            # CREAR NOMBRE DEL ARCHIVO
            # ==========================================

            carpeta_uploads = (
                r"C:\Users\HP\Desktop\fibercore"
                r"\backend\uploads\whatsapp"
            )

            os.makedirs(
                carpeta_uploads,
                exist_ok=True,
            )

            fecha = datetime.now().strftime(
                "%Y%m%d_%H%M%S"
            )

            nombre_archivo = (
                f"whatsapp_{numero}_{fecha}_{media_id}.jpg"
            )

            ruta_archivo = os.path.join(
                carpeta_uploads,
                nombre_archivo,
            )

            # ==========================================
            # DESCARGAR IMAGEN DESDE WHATSAPP
            # ==========================================

            await descargar_imagen_whatsapp(
                media_id=media_id,
                ruta_destino=ruta_archivo,
            )

            print(
                "COMPROBANTE GUARDADO CORRECTAMENTE:"
            )
            print(ruta_archivo)

            # ==========================================
            # RESPONDER AL CLIENTE
            # ==========================================

            await enviar_mensaje_whatsapp(
                numero_destino=numero,
                mensaje=(
                    "Comprobante recibido correctamente. "
                    "Estamos procesando la imagen."
                ),
            )

            return {
                "status": "IMAGE_DOWNLOADED",
                "media_id": media_id,
                "referencia": caption,
                "archivo": ruta_archivo,
            }

        # ==========================================
        # OTROS TIPOS DE MENSAJE
        # ==========================================

        print(
            "Tipo de mensaje no soportado:",
            tipo_mensaje,
        )

        return {
            "status": "EVENT_RECEIVED"
        }

    except Exception as e:

        print(
            "ERROR PROCESANDO WHATSAPP:",
            e,
        )

        return {
            "status": "EVENT_RECEIVED"
        }