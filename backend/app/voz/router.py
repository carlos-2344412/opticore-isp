from fastapi import APIRouter, WebSocket
from fastapi.responses import PlainTextResponse


router = APIRouter(
    prefix="/voz",
    tags=["Bot de Voz"],
)


@router.post("/llamada")
async def iniciar_llamada():
    twiml = """<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Connect>
        <Stream url="wss://save-arrive-singing-owns.trycloudflare.com/voz/media-stream" />
    </Connect>
</Response>"""

    return PlainTextResponse(
        twiml,
        media_type="application/xml",
    )


@router.websocket("/media-stream")
async def media_stream(websocket: WebSocket):
    await websocket.accept()

    print("========== TWILIO MEDIA STREAM CONECTADO ==========")

    try:
        while True:
            mensaje = await websocket.receive_text()

            print("TWILIO:")
            print(mensaje)

    except Exception as e:
        print("MEDIA STREAM FINALIZADO:", e)

    finally:
        print("========== TWILIO MEDIA STREAM DESCONECTADO ==========")