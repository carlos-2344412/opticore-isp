import os

import httpx
from dotenv import load_dotenv


load_dotenv()


WHATSAPP_ACCESS_TOKEN = os.getenv("WHATSAPP_ACCESS_TOKEN")
WHATSAPP_PHONE_NUMBER_ID = os.getenv("WHATSAPP_PHONE_NUMBER_ID")


async def enviar_mensaje_whatsapp(
    numero_destino: str,
    mensaje: str,
):
    url = (
        f"https://graph.facebook.com/v23.0/"
        f"{WHATSAPP_PHONE_NUMBER_ID}/messages"
    )

    headers = {
        "Authorization": f"Bearer {WHATSAPP_ACCESS_TOKEN}",
        "Content-Type": "application/json",
    }

    payload = {
        "messaging_product": "whatsapp",
        "to": numero_destino,
        "type": "text",
        "text": {
            "body": mensaje,
        },
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(
            url,
            headers=headers,
            json=payload,
        )

    print("WHATSAPP API STATUS:", response.status_code)
    print("WHATSAPP API RESPONSE:", response.text)

    response.raise_for_status()

    return response.json()


async def descargar_imagen_whatsapp(
    media_id: str,
    ruta_destino: str,
):
    """
    Descarga una imagen recibida por WhatsApp
    y la guarda en el servidor.
    """

    if not media_id:
        raise ValueError("No se recibió el media_id de WhatsApp.")

    # ==========================================
    # PASO 1
    # Obtener la URL temporal de la imagen
    # ==========================================

    media_url = (
        f"https://graph.facebook.com/v23.0/"
        f"{media_id}"
    )

    headers = {
        "Authorization": f"Bearer {WHATSAPP_ACCESS_TOKEN}",
    }

    async with httpx.AsyncClient() as client:

        response = await client.get(
            media_url,
            headers=headers,
        )

        print(
            "WHATSAPP MEDIA INFO STATUS:",
            response.status_code,
        )

        print(
            "WHATSAPP MEDIA INFO RESPONSE:",
            response.text,
        )

        response.raise_for_status()

        media_data = response.json()

    url_imagen = media_data.get("url")

    if not url_imagen:
        raise ValueError(
            "WhatsApp no devolvió la URL de la imagen."
        )

    # ==========================================
    # PASO 2
    # Descargar la imagen
    # ==========================================

    async with httpx.AsyncClient() as client:

        response = await client.get(
            url_imagen,
            headers=headers,
        )

        print(
            "WHATSAPP IMAGE DOWNLOAD STATUS:",
            response.status_code,
        )

        response.raise_for_status()

        contenido = response.content

    # ==========================================
    # PASO 3
    # Crear carpeta si no existe
    # ==========================================

    carpeta = os.path.dirname(ruta_destino)

    if carpeta:
        os.makedirs(
            carpeta,
            exist_ok=True,
        )

    # ==========================================
    # PASO 4
    # Guardar imagen
    # ==========================================

    with open(
        ruta_destino,
        "wb",
    ) as archivo:

        archivo.write(contenido)

    print(
        "IMAGEN WHATSAPP GUARDADA:",
        ruta_destino,
    )

    return ruta_destino