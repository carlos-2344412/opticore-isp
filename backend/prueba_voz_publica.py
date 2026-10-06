import asyncio
import websockets

async def test():
    uri = "wss://hobby-deposit-str-exercise.trycloudflare.com/voz/media-stream"

    async with websockets.connect(uri) as websocket:
        print("WEBSOCKET PUBLICO CONECTADO")
        await websocket.send("PRUEBA DESDE CLOUDFLARE")
        print("MENSAJE ENVIADO")
        await asyncio.sleep(2)

asyncio.run(test())
