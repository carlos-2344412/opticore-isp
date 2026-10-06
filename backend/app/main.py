from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

from sqlmodel import Session

from app.db.database import engine

from app.auth.router import router as auth_router
from app.clientes.router import router as clientes_router
from app.planes.router import router as planes_router
from app.servicios.router import router as servicios_router
from app.pagos.router import router as pagos_router
from app.facturas.router import router as facturas_router
from app.chatbot.router import router as chatbot_router
from app.soporte.router import router as soporte_router
from app.services.router import router as automatizacion_router
from app.webhook.router import router as whatsapp_webhook_router
from app.voz.router import router as voz_router

# Comprobantes de pago
from app.pagos.comprobantes_router import router as comprobantes_router

# Cobranza automática
from app.services.cobranza_automatica import revisar_servicios_vencidos

from apscheduler.schedulers.background import BackgroundScheduler


app = FastAPI(
    title="FiberCore ISP",
    description="Sistema de gestión para ISP",
    version="1.0.0",
)


# ============================================================
# CORS
# ============================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# ARCHIVOS SUBIDOS
# ============================================================

app.mount(
    "/uploads",
    StaticFiles(
        directory="C:/Users/HP/Desktop/fibercore/backend/uploads"
    ),
    name="uploads",
)


# ============================================================
# ROUTERS
# ============================================================

app.include_router(auth_router)

app.include_router(clientes_router)

app.include_router(planes_router)

app.include_router(servicios_router)

# IMPORTANTE:
# Comprobantes ANTES de /pagos/{pago_id}
# para evitar que "comprobantes" sea interpretado
# como un UUID de pago.
app.include_router(comprobantes_router)

app.include_router(pagos_router)

app.include_router(facturas_router)

app.include_router(chatbot_router)

app.include_router(soporte_router)

app.include_router(automatizacion_router)

app.include_router(whatsapp_webhook_router)

app.include_router(voz_router)


# ============================================================
# COBRANZA AUTOMÁTICA
# ============================================================

scheduler = BackgroundScheduler()


def ejecutar_cobranza():
    with Session(engine) as session:
        revisar_servicios_vencidos(session)


scheduler.add_job(
    ejecutar_cobranza,
    "cron",
    hour=0,
    minute=5,
)


# ============================================================
# EVENTOS DE INICIO Y APAGADO
# ============================================================

@app.on_event("startup")
def startup_event():
    if not scheduler.running:
        scheduler.start()


@app.on_event("shutdown")
def shutdown_event():
    if scheduler.running:
        scheduler.shutdown()


# ============================================================
# ROOT
# ============================================================

@app.get("/")
def root():
    return {
        "mensaje": "FiberCore ISP funcionando correctamente",
        "estado": "online",
    }