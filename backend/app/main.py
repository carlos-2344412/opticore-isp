from fastapi import FastAPI

app = FastAPI(
    title="FiberCore API",
    version="1.0.0",
    description="Sistema de Gestión para ISP - OPTIRÁPIDO"
)


@app.get("/")
def root():
    return {
        "mensaje": "Bienvenido a FiberCore",
        "empresa": "OPTIRÁPIDO",
        "version": "1.0.0"
    }