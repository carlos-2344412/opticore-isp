from datetime import date, datetime, timedelta, timezone

from sqlmodel import Session, select

from app.models.servicio import Servicio
from app.models.factura import Factura


DIAS_GRACIA = 2


def revisar_servicios_vencidos(session: Session):
    """
    Revisa los servicios vencidos y suspende automáticamente
    aquellos que superaron los días de gracia y todavía tienen
    una factura pendiente.
    """

    hoy = date.today()

    # Fecha límite para suspender
    fecha_limite = hoy - timedelta(days=DIAS_GRACIA)

    # Buscar servicios activos que ya superaron
    # la fecha de vencimiento + días de gracia
    statement = select(Servicio).where(
        Servicio.estado == "activo",
        Servicio.suspendido == False,
        Servicio.fecha_vencimiento <= fecha_limite,
    )

    servicios = session.exec(statement).all()

    suspendidos = []

    for servicio in servicios:

        # Buscar una factura pendiente asociada al servicio
        statement_factura = select(Factura).where(
            Factura.servicio_id == servicio.id,
            Factura.estado == "pendiente",
        )

        factura = session.exec(statement_factura).first()

        # Si no existe una factura pendiente,
        # no suspendemos el servicio
        if not factura:
            continue

        # Suspender el servicio
        servicio.suspendido = True
        servicio.estado = "suspendido"
        servicio.motivo_suspension = (
            "Suspensión automática por falta de pago"
        )

        servicio.updated_at = datetime.now(timezone.utc)

        session.add(servicio)

        suspendidos.append({
            "servicio_id": str(servicio.id),
            "cliente_id": str(servicio.cliente_id),
            "motivo": servicio.motivo_suspension,
        })

    session.commit()

    return {
        "total_suspendidos": len(suspendidos),
        "servicios": suspendidos,
    }