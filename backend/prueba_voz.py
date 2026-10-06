import asyncio
import websockets

async def test():
    uri = "ws://localhost:8001/voz/media-stream"

    async with websockets.connect(uri) as websocket:
        print("WEBSOCKET CONECTADO")
        await websocket.send("HOLA DESDE LA PRUEBA")
        print("MENSAJE ENVIADO")
        await asyncio.sleep(2)

asyncio.run(test())
