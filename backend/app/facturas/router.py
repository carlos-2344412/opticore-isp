from datetime import datetime, timezone
from uuid import UUID, uuid4
from io import BytesIO
from zipfile import ZipFile, ZIP_DEFLATED
import os
from html import escape

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
)

from fastapi.responses import StreamingResponse

from sqlmodel import Session, select

from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from reportlab.graphics.shapes import Drawing
from reportlab.graphics.barcode import qr
from reportlab.graphics import renderPDF

from app.db.database import get_session

from app.models.factura import Factura
from app.models.cliente import Cliente
from app.models.servicio import Servicio
from app.models.empresa import Empresa


router = APIRouter(
    prefix="/facturas",
    tags=["Facturación"],
)


# =========================================================
# COLORES CORPORATIVOS
# =========================================================

AZUL_OSCURO = colors.HexColor("#071C3D")
AZUL = colors.HexColor("#123A75")
AZUL_CLARO = colors.HexColor("#EAF1FB")

ROJO = colors.HexColor("#E51B23")
ROJO_CLARO = colors.HexColor("#FCE9EA")

GRIS_FONDO = colors.HexColor("#F5F7FA")
GRIS_BORDE = colors.HexColor("#D9E0EA")
GRIS_TEXTO = colors.HexColor("#687386")

BLANCO = colors.white
NEGRO = colors.HexColor("#1C2533")

VERDE = colors.HexColor("#21884A")
VERDE_CLARO = colors.HexColor("#E4F4E9")

AMARILLO = colors.HexColor("#C98500")
AMARILLO_CLARO = colors.HexColor("#FFF4D6")

ROJO_ESTADO = colors.HexColor("#C62828")


# =========================================================
# FUNCIONES AUXILIARES
# =========================================================

def obtener_valor(objeto, atributo, defecto=""):
    """
    Obtiene un atributo de forma segura.
    """

    valor = getattr(
        objeto,
        atributo,
        defecto,
    )

    if valor is None:
        return defecto

    return str(valor)


def formatear_fecha(fecha):
    """
    Convierte una fecha al formato colombiano.
    """

    if not fecha:
        return "No definida"

    try:
        return fecha.strftime("%d/%m/%Y")
    except Exception:
        return str(fecha)


def formatear_dinero(valor):
    """
    Formatea valores monetarios en pesos colombianos.
    """

    try:
        numero = float(valor or 0)

        return f"${numero:,.0f}".replace(
            ",",
            ".",
        )

    except Exception:
        return "$0"


def obtener_nombre_cliente(cliente):
    """
    Obtiene el nombre completo del cliente.
    """

    nombre = obtener_valor(
        cliente,
        "nombre",
        "",
    )

    apellido = obtener_valor(
        cliente,
        "apellido",
        "",
    )

    nombre_completo = (
        f"{nombre} {apellido}"
    ).strip()

    return nombre_completo or "Cliente"


def obtener_ruta_logo():
    """
    Busca automáticamente el logo de la empresa
    en varias ubicaciones posibles.

    Si no encuentra una imagen, la factura seguirá
    funcionando y mostrará el nombre de la empresa.
    """

    base_dir = os.path.abspath(
        os.path.dirname(__file__)
    )

    rutas_posibles = [
        # Ubicación recomendada: backend/app/assets/logo.png
        os.path.join(base_dir, "..", "assets", "logo.png"),
        os.path.join(base_dir, "..", "assets", "optirapido.png"),
        os.path.join(base_dir, "..", "assets", "logo_optirapido.png"),
        os.path.join(base_dir, "..", "assets", "logo.jpg"),
        os.path.join(base_dir, "..", "assets", "logo.jpeg"),

        # Otras ubicaciones comunes del proyecto
        os.path.join(base_dir, "..", "..", "assets", "logo.png"),
        os.path.join(base_dir, "..", "..", "assets", "optirapido.png"),
        os.path.join(base_dir, "..", "..", "frontend", "src", "assets", "logo.png"),
        os.path.join(base_dir, "..", "..", "frontend", "src", "assets", "optirapido.png"),
        os.path.join(base_dir, "..", "..", "frontend", "public", "logo.png"),
        os.path.join(base_dir, "..", "..", "frontend", "public", "optirapido.png"),
    ]

    for ruta in rutas_posibles:

        ruta = os.path.abspath(ruta)

        if os.path.exists(ruta):
            return ruta

    return None


def dibujar_tarjeta(
    pdf,
    x,
    y,
    ancho,
    alto,
    color_fondo=BLANCO,
    radio=12,
    borde=GRIS_BORDE,
):
    """
    Dibuja una tarjeta con bordes redondeados.
    """

    pdf.setFillColor(
        color_fondo
    )

    pdf.setStrokeColor(
        borde
    )

    pdf.setLineWidth(0.8)

    pdf.roundRect(
        x,
        y,
        ancho,
        alto,
        radio,
        stroke=1,
        fill=1,
    )


def dibujar_titulo_seccion(
    pdf,
    x,
    y,
    titulo,
):
    """
    Dibuja los títulos de las secciones.
    """

    pdf.setFillColor(
        AZUL_OSCURO
    )

    pdf.circle(
        x + 10,
        y - 9,
        12,
        stroke=0,
        fill=1,
    )

    pdf.setFillColor(
        BLANCO
    )

    pdf.setFont(
        "Helvetica-Bold",
        12,
    )

    pdf.drawCentredString(
        x + 10,
        y - 13,
        "i",
    )

    pdf.setFillColor(
        AZUL_OSCURO
    )

    pdf.setFont(
        "Helvetica-Bold",
        13,
    )

    pdf.drawString(
        x + 30,
        y - 14,
        titulo.upper(),
    )


def dibujar_fila_dato(
    pdf,
    x,
    y,
    ancho,
    etiqueta,
    valor,
    color_valor=NEGRO,
    linea=True,
):
    """
    Dibuja una fila de información.
    """

    pdf.setFillColor(
        GRIS_TEXTO
    )

    pdf.setFont(
        "Helvetica-Bold",
        8,
    )

    pdf.drawString(
        x,
        y,
        etiqueta.upper(),
    )

    pdf.setFillColor(
        color_valor
    )

    pdf.setFont(
        "Helvetica-Bold",
        9,
    )

    texto = str(valor)

    ancho_texto = pdf.stringWidth(
        texto,
        "Helvetica-Bold",
        9,
    )

    if ancho_texto > ancho * 0.52:

        texto = texto[:35] + "..."

    pdf.drawRightString(
        x + ancho,
        y,
        texto,
    )

    if linea:

        pdf.setStrokeColor(
            GRIS_BORDE
        )

        pdf.setLineWidth(0.5)

        pdf.line(
            x,
            y - 8,
            x + ancho,
            y - 8,
        )


# =========================================================
# LISTAR FACTURAS
# =========================================================

@router.get("")
def listar_facturas(
    session: Session = Depends(
        get_session
    ),
):
    facturas = session.exec(
        select(Factura)
    ).all()

    return facturas


# =========================================================
# CREAR FACTURA
# =========================================================

@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
)
def crear_factura(
    datos: Factura,
    session: Session = Depends(
        get_session
    ),
):

    cliente = session.exec(
        select(Cliente).where(
            Cliente.id == datos.cliente_id,
            Cliente.empresa_id
            == datos.empresa_id,
        )
    ).first()

    if not cliente:

        raise HTTPException(
            status_code=404,
            detail="Cliente no encontrado",
        )

    if datos.servicio_id:

        servicio = session.exec(
            select(Servicio).where(
                Servicio.id
                == datos.servicio_id,

                Servicio.empresa_id
                == datos.empresa_id,

                Servicio.cliente_id
                == datos.cliente_id,
            )
        ).first()

        if not servicio:

            raise HTTPException(
                status_code=404,
                detail=(
                    "Servicio no encontrado "
                    "para este cliente"
                ),
            )

    # Generar ID

    datos.id = uuid4()

    # Año actual

    anio = datetime.now().year

    # Buscar última factura

    ultima_factura = session.exec(
        select(Factura)
        .order_by(
            Factura.created_at.desc()
        )
    ).first()

    # Consecutivo

    if (
        ultima_factura
        and ultima_factura.numero
    ):

        try:

            ultimo_numero = int(
                ultima_factura.numero
                .split("-")[-1]
            )

            consecutivo = (
                ultimo_numero + 1
            )

        except (
            ValueError,
            IndexError,
        ):

            consecutivo = 1

    else:

        consecutivo = 1

    # Número de factura

    datos.numero = (
        f"FAC-{anio}-"
        f"{consecutivo:06d}"
    )

    # Referencia de pago

    datos.referencia_pago = (
        f"OPT-{anio}-"
        f"{consecutivo:06d}"
    )

    # Guardar

    session.add(datos)

    session.commit()

    session.refresh(datos)

    return datos


# =========================================================
# GENERAR PDF PROFESIONAL
# =========================================================

def _texto_ajustado(pdf, texto, fuente, tamano, ancho_maximo):
    """Recorta texto sin permitir que invada otras columnas."""
    texto = str(texto or "")
    if pdf.stringWidth(texto, fuente, tamano) <= ancho_maximo:
        return texto

    sufijo = "..."
    while texto and pdf.stringWidth(texto + sufijo, fuente, tamano) > ancho_maximo:
        texto = texto[:-1]

    return (texto.rstrip() + sufijo) if texto else sufijo


def _lineas_ajustadas(pdf, texto, fuente, tamano, ancho_maximo, max_lineas=4):
    """Divide un texto en líneas usando el ancho real disponible."""
    palabras = str(texto or "").split()
    if not palabras:
        return []

    lineas = []
    actual = ""

    for palabra in palabras:
        prueba = (actual + " " + palabra).strip()

        if actual and pdf.stringWidth(prueba, fuente, tamano) > ancho_maximo:
            lineas.append(actual)
            actual = palabra

            if len(lineas) >= max_lineas:
                break
        else:
            actual = prueba

    if actual and len(lineas) < max_lineas:
        lineas.append(actual)

    if len(lineas) == max_lineas and len(palabras) > 0:
        ultima = lineas[-1]
        if not ultima.endswith("..."):
            while ultima and pdf.stringWidth(ultima + "...", fuente, tamano) > ancho_maximo:
                ultima = ultima[:-1]
            lineas[-1] = ultima.rstrip() + "..."

    return lineas


def _icono_circulo(pdf, x, y, letra, color=AZUL_OSCURO, radio=12):
    """Icono simple y consistente, sin depender de fuentes externas."""
    pdf.setFillColor(color)
    pdf.circle(x, y, radio, stroke=0, fill=1)

    pdf.setFillColor(BLANCO)
    pdf.setFont("Helvetica-Bold", 9)
    pdf.drawCentredString(x, y - 3, letra)


def _fila_factura_profesional(
    pdf,
    x,
    y,
    ancho,
    etiqueta,
    valor,
    icono,
    color_valor=NEGRO,
    color_icono=AZUL_OSCURO,
    linea=True,
):
    """Fila alineada para el bloque de información de la factura."""
    _icono_circulo(pdf, x + 17, y + 1, icono, color_icono, 11)

    pdf.setFillColor(GRIS_TEXTO)
    pdf.setFont("Helvetica-Bold", 7.2)
    pdf.drawString(x + 42, y - 2, etiqueta.upper())

    pdf.setFillColor(color_valor)
    pdf.setFont("Helvetica-Bold", 9.5)
    valor_visible = _texto_ajustado(
        pdf,
        valor,
        "Helvetica-Bold",
        9.5,
        ancho * 0.42,
    )
    pdf.drawRightString(x + ancho - 16, y - 2, valor_visible)

    if linea:
        pdf.setStrokeColor(GRIS_BORDE)
        pdf.setLineWidth(0.45)
        pdf.line(x + 38, y - 18, x + ancho - 16, y - 18)


def _dibujar_servicio_grafico(pdf, x, y, ancho, alto):
    """Panel corporativo decorativo para que la factura no se vea vacía."""
    pdf.setFillColor(AZUL_OSCURO)
    pdf.roundRect(x, y, ancho, alto, 13, stroke=0, fill=1)

    # Título
    pdf.setFillColor(BLANCO)
    pdf.setFont("Helvetica-Bold", 10.5)
    pdf.drawString(x + 18, y + alto - 28, "INTERNET QUE TE")
    pdf.setFillColor(ROJO)
    pdf.drawString(x + 18 + 104, y + alto - 28, "CONECTA,")

    pdf.setFillColor(BLANCO)
    pdf.drawString(x + 18, y + alto - 44, "SERVICIO QUE TE")
    pdf.setFillColor(colors.HexColor("#5E9DF6"))
    pdf.drawString(x + 18 + 112, y + alto - 44, "RESPALDA.")

    # Casa
    casa_x = x + ancho - 76
    casa_y = y + 16

    pdf.setStrokeColor(colors.HexColor("#A7C4F4"))
    pdf.setLineWidth(1.6)
    pdf.line(casa_x - 24, casa_y + 27, casa_x, casa_y + 50)
    pdf.line(casa_x, casa_y + 50, casa_x + 24, casa_y + 27)
    pdf.line(casa_x - 18, casa_y + 27, casa_x - 18, casa_y)
    pdf.line(casa_x - 18, casa_y, casa_x + 18, casa_y)
    pdf.line(casa_x + 18, casa_y, casa_x + 18, casa_y + 27)

    # Señal WiFi
    pdf.arc(casa_x - 15, casa_y + 12, casa_x + 15, casa_y + 40, 25, 130)
    pdf.arc(casa_x - 10, casa_y + 15, casa_x + 10, casa_y + 33, 25, 130)
    pdf.circle(casa_x, casa_y + 20, 1.7, stroke=0, fill=1)

    # Beneficios
    beneficios = [
        ("V", "VELOCIDAD", "ESTABLE"),
        ("S", "SOPORTE", "CONFIABLE"),
        ("A", "ATENCIÓN", "CERCANA"),
    ]

    ancho_beneficio = (ancho * 0.62) / 3

    for indice, (letra, linea1, linea2) in enumerate(beneficios):
        bx = x + 18 + indice * ancho_beneficio
        _icono_circulo(
            pdf,
            bx + ancho_beneficio / 2,
            y + 28,
            letra,
            colors.HexColor("#15345F"),
            9,
        )

        pdf.setFillColor(colors.HexColor("#C8D7EC"))
        pdf.setFont("Helvetica-Bold", 6.2)
        pdf.drawCentredString(
            bx + ancho_beneficio / 2,
            y + 11,
            linea1,
        )
        pdf.drawCentredString(
            bx + ancho_beneficio / 2,
            y + 3,
            linea2,
        )


@router.get(
    "/{factura_id}/pdf"
)
def generar_factura_pdf(
    factura_id: UUID,
    session: Session = Depends(
        get_session
    ),
):
    # =====================================
    # BUSCAR DATOS
    # =====================================

    factura = session.get(Factura, factura_id)

    if not factura:
        raise HTTPException(
            status_code=404,
            detail="Factura no encontrada",
        )

    empresa = session.get(Empresa, factura.empresa_id)

    if not empresa:
        raise HTTPException(
            status_code=404,
            detail="Empresa no encontrada",
        )

    cliente = session.get(Cliente, factura.cliente_id)

    if not cliente:
        raise HTTPException(
            status_code=404,
            detail="Cliente no encontrado",
        )

    servicio = None

    if factura.servicio_id:
        servicio = session.get(
            Servicio,
            factura.servicio_id,
        )

    # =====================================
    # DATOS PREPARADOS
    # =====================================

    nombre_empresa = obtener_valor(
        empresa,
        "nombre",
        "OPTIRÁPIDO",
    )

    nombre_cliente = obtener_nombre_cliente(cliente)

    documento_cliente = obtener_valor(
        cliente,
        "documento",
        "No registrado",
    )

    telefono_cliente = obtener_valor(
        cliente,
        "telefono",
        "No registrado",
    )

    correo_cliente = obtener_valor(
        cliente,
        "correo",
        "No registrado",
    )

    nit = obtener_valor(empresa, "nit", "")
    direccion = obtener_valor(empresa, "direccion", "")
    ciudad = obtener_valor(empresa, "ciudad", "")
    telefono_empresa = obtener_valor(empresa, "telefono", "")
    correo_empresa = obtener_valor(empresa, "correo", "")

    fecha_emision = formatear_fecha(
        factura.fecha_emision
    )

    fecha_vencimiento = formatear_fecha(
        factura.fecha_vencimiento
    )

    referencia = (
        factura.referencia_pago
        or "NO ASIGNADA"
    )

    estado = (
        factura.estado
        or "pendiente"
    ).upper()

    concepto = (
        factura.concepto
        or "Servicio de Internet"
    )

    if servicio:
        tipo_servicio = obtener_valor(
            servicio,
            "tipo",
            "",
        )

        if tipo_servicio:
            concepto = tipo_servicio

    # Colores del estado
    color_estado = AMARILLO
    fondo_estado = AMARILLO_CLARO

    if estado == "PAGADA":
        color_estado = VERDE
        fondo_estado = VERDE_CLARO

    elif estado == "ANULADA":
        color_estado = ROJO_ESTADO
        fondo_estado = ROJO_CLARO

    # =====================================
    # PREPARAR PDF
    # =====================================

    buffer = BytesIO()

    pdf = canvas.Canvas(
        buffer,
        pagesize=letter,
        pageCompression=1,
    )

    ANCHO, ALTO = letter

    margen = 24
    contenido_ancho = ANCHO - (margen * 2)

    # Fondo limpio
    pdf.setFillColor(colors.HexColor("#F7F8FB"))
    pdf.rect(
        0,
        0,
        ANCHO,
        ALTO,
        stroke=0,
        fill=1,
    )

    # =====================================
    # ENCABEZADO
    # =====================================

    alto_header = 188
    ancho_izquierda = 274

    # Panel azul corporativo
    pdf.setFillColor(AZUL_OSCURO)
    pdf.rect(
        0,
        ALTO - alto_header,
        ancho_izquierda,
        alto_header,
        stroke=0,
        fill=1,
    )

    # Detalles decorativos
    pdf.setStrokeColor(colors.HexColor("#102D57"))
    pdf.setLineWidth(0.45)

    for i in range(9):
        yy = ALTO - 15 - i * 14
        pdf.line(
            12,
            yy,
            ancho_izquierda - 28,
            yy - 22,
        )

    # Franja roja lateral
    pdf.setFillColor(ROJO)
    pdf.rect(
        ancho_izquierda - 5,
        ALTO - alto_header,
        5,
        alto_header,
        stroke=0,
        fill=1,
    )

    # Logo
    ruta_logo = obtener_ruta_logo()
    logo_dibujado = False

    if ruta_logo:
        try:
            imagen = ImageReader(ruta_logo)
            pdf.drawImage(
                imagen,
                22,
                ALTO - 120,
                width=230,
                height=92,
                preserveAspectRatio=True,
                anchor="c",
                mask="auto",
            )
            logo_dibujado = True
        except Exception:
            logo_dibujado = False

    if not logo_dibujado:
        pdf.setFillColor(BLANCO)
        pdf.setFont("Helvetica-Bold", 26)
        pdf.drawString(
            26,
            ALTO - 70,
            nombre_empresa.upper(),
        )

    # Eslogan
    pdf.setFillColor(colors.HexColor("#E0E7F1"))
    pdf.setFont("Helvetica", 10)
    pdf.drawString(
        42,
        ALTO - 145,
        "Conectamos tu mundo,",
    )

    pdf.setFillColor(ROJO)
    pdf.setFont("Helvetica-Bold", 10)
    pdf.drawString(
        42,
        ALTO - 160,
        "impulsamos tu vida.",
    )

    # =====================================
    # TÍTULO Y DATOS DE FACTURA
    # =====================================

    x_info = ancho_izquierda + 24
    ancho_info = ANCHO - x_info - margen

    pdf.setFillColor(AZUL_OSCURO)
    pdf.setFont("Helvetica-Bold", 19)
    pdf.drawString(
        x_info,
        ALTO - 46,
        "FACTURA DE SERVICIO",
    )

    pdf.setStrokeColor(ROJO)
    pdf.setLineWidth(1)
    pdf.line(
        x_info,
        ALTO - 57,
        ANCHO - margen,
        ALTO - 57,
    )

    alto_info = 158
    y_info = ALTO - 228

    dibujar_tarjeta(
        pdf,
        x_info,
        y_info,
        ancho_info,
        alto_info,
        color_fondo=BLANCO,
        radio=12,
    )

    filas = [
        (
            "NÚMERO DE FACTURA",
            factura.numero or "Sin número",
            "F",
            NEGRO,
            AZUL_OSCURO,
        ),
        (
            "REFERENCIA DE PAGO",
            referencia,
            "R",
            NEGRO,
            AZUL_OSCURO,
        ),
        (
            "FECHA DE EMISIÓN",
            fecha_emision,
            "E",
            NEGRO,
            AZUL_OSCURO,
        ),
        (
            "FECHA DE VENCIMIENTO",
            fecha_vencimiento,
            "V",
            ROJO,
            ROJO,
        ),
    ]

    y_fila = y_info + alto_info - 28

    for etiqueta, valor, icono, color_valor, color_icono in filas:
        _fila_factura_profesional(
            pdf,
            x_info + 8,
            y_fila,
            ancho_info - 16,
            etiqueta,
            valor,
            icono,
            color_valor,
            color_icono,
            True,
        )
        y_fila -= 31

    # Estado
    _icono_circulo(
        pdf,
        x_info + 25,
        y_info + 17,
        "✓",
        AZUL_OSCURO,
        11,
    )

    pdf.setFillColor(GRIS_TEXTO)
    pdf.setFont("Helvetica-Bold", 7.2)
    pdf.drawString(
        x_info + 50,
        y_info + 14,
        "ESTADO",
    )

    ancho_badge = 92
    pdf.setFillColor(fondo_estado)
    pdf.roundRect(
        x_info + ancho_info - ancho_badge - 16,
        y_info + 5,
        ancho_badge,
        24,
        12,
        stroke=0,
        fill=1,
    )

    pdf.setFillColor(color_estado)
    pdf.setFont("Helvetica-Bold", 8)
    pdf.drawCentredString(
        x_info + ancho_info - ancho_badge / 2 - 16,
        y_info + 14,
        estado,
    )

    # =====================================
    # DATOS DEL CLIENTE
    # =====================================

    y_seccion_cliente = ALTO - 226
    dibujar_titulo_seccion(
        pdf,
        margen + 8,
        y_seccion_cliente,
        "Datos del cliente",
    )

    x_cliente = margen
    y_cliente = 418
    ancho_cliente = ancho_izquierda - margen - 12
    alto_cliente = 150

    dibujar_tarjeta(
        pdf,
        x_cliente,
        y_cliente,
        ancho_cliente,
        alto_cliente,
        color_fondo=BLANCO,
        radio=12,
    )

    datos_cliente = [
        ("N", "NOMBRE", nombre_cliente),
        ("D", "DOCUMENTO", documento_cliente),
        ("T", "TELÉFONO", telefono_cliente),
        ("C", "CORREO", correo_cliente),
    ]

    y_dato = y_cliente + alto_cliente - 28

    for indice, (icono, etiqueta, valor) in enumerate(datos_cliente):
        _icono_circulo(
            pdf,
            x_cliente + 20,
            y_dato - 1,
            icono,
            AZUL_OSCURO,
            10,
        )

        pdf.setFillColor(GRIS_TEXTO)
        pdf.setFont("Helvetica-Bold", 7.3)
        pdf.drawString(
            x_cliente + 42,
            y_dato - 4,
            etiqueta,
        )

        pdf.setFillColor(NEGRO)
        pdf.setFont("Helvetica", 8.5)

        valor_visible = _texto_ajustado(
            pdf,
            valor,
            "Helvetica",
            8.5,
            ancho_cliente - 126,
        )

        pdf.drawRightString(
            x_cliente + ancho_cliente - 14,
            y_dato - 4,
            valor_visible,
        )

        if indice < len(datos_cliente) - 1:
            pdf.setStrokeColor(GRIS_BORDE)
            pdf.setLineWidth(0.45)
            pdf.line(
                x_cliente + 40,
                y_dato - 20,
                x_cliente + ancho_cliente - 14,
                y_dato - 20,
            )

        y_dato -= 31

    # =====================================
    # PANEL DEL SERVICIO
    # =====================================

    x_servicio = x_info
    y_servicio = y_cliente
    ancho_servicio = ancho_info
    alto_servicio = 104

    _dibujar_servicio_grafico(
        pdf,
        x_servicio,
        y_servicio,
        ancho_servicio,
        alto_servicio,
    )

    # =====================================
    # DETALLE DEL SERVICIO
    # =====================================

    y_titulo_detalle = 378

    dibujar_titulo_seccion(
        pdf,
        margen + 8,
        y_titulo_detalle,
        "Detalle del servicio",
    )

    x_tabla = margen
    y_tabla = 288
    ancho_tabla = contenido_ancho
    alto_cabecera = 30
    alto_fila = 58

    # Contenedor completo
    dibujar_tarjeta(
        pdf,
        x_tabla,
        y_tabla,
        ancho_tabla,
        alto_cabecera + alto_fila,
        color_fondo=BLANCO,
        radio=10,
    )

    # Cabecera
    pdf.setFillColor(AZUL_OSCURO)
    pdf.roundRect(
        x_tabla,
        y_tabla + alto_fila,
        ancho_tabla,
        alto_cabecera,
        10,
        stroke=0,
        fill=1,
    )

    # Evitar esquinas inferiores visualmente redondeadas en cabecera
    pdf.rect(
        x_tabla,
        y_tabla + alto_fila,
        ancho_tabla,
        10,
        stroke=0,
        fill=1,
    )

    x1 = x_tabla
    x2 = x_tabla + ancho_tabla * 0.46
    x3 = x_tabla + ancho_tabla * 0.68
    x4 = x_tabla + ancho_tabla * 0.84
    x5 = x_tabla + ancho_tabla

    columnas = [
        ("CONCEPTO", x1, x2),
        ("SUBTOTAL", x2, x3),
        ("DESCUENTO", x3, x4),
        ("TOTAL", x4, x5),
    ]

    pdf.setFillColor(BLANCO)
    pdf.setFont("Helvetica-Bold", 7.5)

    for encabezado, inicio, fin in columnas:
        pdf.drawCentredString(
            (inicio + fin) / 2,
            y_tabla + alto_fila + 11,
            encabezado,
        )

    # Separadores
    pdf.setStrokeColor(GRIS_BORDE)
    pdf.setLineWidth(0.45)

    for xx in [x2, x3, x4]:
        pdf.line(
            xx,
            y_tabla,
            xx,
            y_tabla + alto_fila,
        )

    # Icono de servicio
    _icono_circulo(
        pdf,
        x1 + 26,
        y_tabla + 29,
        "I",
        AZUL_CLARO,
        15,
    )

    pdf.setFillColor(AZUL_OSCURO)
    pdf.setFont("Helvetica-Bold", 7)

    pdf.setFillColor(NEGRO)
    pdf.setFont("Helvetica", 9)

    concepto_visible = _texto_ajustado(
        pdf,
        concepto,
        "Helvetica",
        9,
        x2 - x1 - 68,
    )

    pdf.drawString(
        x1 + 50,
        y_tabla + 25,
        concepto_visible,
    )

    valores = [
        (
            formatear_dinero(factura.subtotal),
            (x2 + x3) / 2,
            NEGRO,
        ),
        (
            formatear_dinero(factura.descuento),
            (x3 + x4) / 2,
            NEGRO,
        ),
        (
            formatear_dinero(factura.total),
            (x4 + x5) / 2,
            ROJO,
        ),
    ]

    pdf.setFont("Helvetica-Bold", 9)

    for texto, xx, color in valores:
        pdf.setFillColor(color)
        pdf.drawCentredString(
            xx,
            y_tabla + 25,
            texto,
        )

    # =====================================
    # TOTAL A PAGAR
    # =====================================

    ancho_total = 268
    alto_total = 36
    x_total = ANCHO - margen - ancho_total
    y_total = 244

    dibujar_tarjeta(
        pdf,
        x_total,
        y_total,
        ancho_total,
        alto_total,
        color_fondo=BLANCO,
        radio=8,
    )

    pdf.setFillColor(AZUL_OSCURO)
    pdf.setFont("Helvetica-Bold", 10)
    pdf.drawString(
        x_total + 18,
        y_total + 12,
        "TOTAL A PAGAR",
    )

    ancho_valor = 108
    pdf.setFillColor(ROJO)
    pdf.roundRect(
        x_total + ancho_total - ancho_valor,
        y_total,
        ancho_valor,
        alto_total,
        6,
        stroke=0,
        fill=1,
    )

    pdf.setFillColor(BLANCO)
    pdf.setFont("Helvetica-Bold", 13)
    pdf.drawCentredString(
        x_total + ancho_total - ancho_valor / 2,
        y_total + 11,
        formatear_dinero(factura.total),
    )

    # =====================================
    # PAGO Y OBSERVACIONES
    # =====================================

    y_inferior = 82
    alto_inferior = 145
    ancho_pago = contenido_ancho * 0.49
    x_pago = margen

    dibujar_tarjeta(
        pdf,
        x_pago,
        y_inferior,
        ancho_pago,
        alto_inferior,
        color_fondo=BLANCO,
        radio=12,
    )

    dibujar_titulo_seccion(
        pdf,
        x_pago + 10,
        y_inferior + alto_inferior - 18,
        "Información para el pago",
    )

    pdf.setFillColor(NEGRO)
    pdf.setFont("Helvetica", 7.5)
    pdf.drawString(
        x_pago + 18,
        y_inferior + 95,
        "Para realizar el pago de esta factura utilice",
    )
    pdf.drawString(
        x_pago + 18,
        y_inferior + 83,
        "la siguiente referencia única:",
    )

    # Referencia
    ancho_referencia = ancho_pago - 98

    pdf.setFillColor(ROJO)
    pdf.roundRect(
        x_pago + 18,
        y_inferior + 45,
        ancho_referencia,
        30,
        7,
        stroke=0,
        fill=1,
    )

    pdf.setFillColor(BLANCO)
    pdf.setFont("Helvetica-Bold", 10)
    pdf.drawCentredString(
        x_pago + 18 + ancho_referencia / 2,
        y_inferior + 55,
        _texto_ajustado(
            pdf,
            referencia,
            "Helvetica-Bold",
            10,
            ancho_referencia - 16,
        ),
    )

    # QR
    try:
        qr_widget = qr.QrCodeWidget(referencia)
        bounds = qr_widget.getBounds()

        qr_ancho = bounds[2] - bounds[0]
        qr_alto = bounds[3] - bounds[1]
        tamano_qr = 54

        dibujo_qr = Drawing(
            tamano_qr,
            tamano_qr,
            transform=[
                tamano_qr / qr_ancho,
                0,
                0,
                tamano_qr / qr_alto,
                0,
                0,
            ],
        )

        dibujo_qr.add(qr_widget)

        renderPDF.draw(
            dibujo_qr,
            pdf,
            x_pago + ancho_pago - 70,
            y_inferior + 18,
        )

    except Exception:
        pass

    pdf.setFillColor(GRIS_TEXTO)
    pdf.setFont("Helvetica", 7)
    pdf.drawString(
        x_pago + 18,
        y_inferior + 25,
        "Escanea el código QR o utiliza la referencia para pagar.",
    )

    pdf.setFont("Helvetica-Bold", 7.5)
    pdf.setFillColor(AZUL_OSCURO)
    pdf.drawString(
        x_pago + 18,
        y_inferior + 10,
        "Bancolombia   •   Daviplata   •   Nequi",
    )

    # Observaciones
    x_obs = x_pago + ancho_pago + 12
    ancho_obs = ANCHO - margen - x_obs

    dibujar_tarjeta(
        pdf,
        x_obs,
        y_inferior,
        ancho_obs,
        alto_inferior,
        color_fondo=BLANCO,
        radio=12,
    )

    dibujar_titulo_seccion(
        pdf,
        x_obs + 10,
        y_inferior + alto_inferior - 18,
        "Observaciones",
    )

    observaciones = (
        factura.observaciones
        or "No hay observaciones adicionales."
    )

    pdf.setFillColor(NEGRO)
    pdf.setFont("Helvetica", 8.5)

    lineas = _lineas_ajustadas(
        pdf,
        observaciones,
        "Helvetica",
        8.5,
        ancho_obs - 34,
        5,
    )

    y_texto = y_inferior + alto_inferior - 55

    for linea in lineas:
        pdf.drawString(
            x_obs + 18,
            y_texto,
            linea,
        )
        y_texto -= 13

    # Marca decorativa inferior
    pdf.setStrokeColor(colors.HexColor("#D6DFEB"))
    pdf.setLineWidth(2.5)
    pdf.arc(
        x_obs + ancho_obs - 90,
        y_inferior + 18,
        x_obs + ancho_obs - 20,
        y_inferior + 88,
        20,
        120,
    )

    # =====================================
    # PIE DE PÁGINA
    # =====================================

    y_pie = 28

    pdf.setStrokeColor(AZUL)
    pdf.setLineWidth(1.6)
    pdf.line(
        margen,
        y_pie + 38,
        ANCHO - margen,
        y_pie + 38,
    )

    pdf.setStrokeColor(ROJO)
    pdf.setLineWidth(1.6)
    pdf.line(
        ANCHO - 120,
        y_pie + 38,
        ANCHO - margen,
        y_pie + 38,
    )

    # Empresa
    pdf.setFillColor(AZUL_OSCURO)
    pdf.setFont("Helvetica-Bold", 7.5)
    pdf.drawString(
        margen,
        y_pie + 20,
        nombre_empresa,
    )

    pdf.setFillColor(GRIS_TEXTO)
    pdf.setFont("Helvetica", 6.5)

    if nit:
        pdf.drawString(
            margen,
            y_pie + 8,
            f"NIT: {nit}",
        )

    ubicacion = " - ".join(
        [dato for dato in [direccion, ciudad] if dato]
    )

    if ubicacion:
        pdf.drawString(
            margen,
            y_pie - 4,
            _texto_ajustado(
                pdf,
                ubicacion,
                "Helvetica",
                6.5,
                150,
            ),
        )

    # Contacto
    x_contacto = ANCHO * 0.34

    pdf.setFillColor(AZUL_OSCURO)
    pdf.setFont("Helvetica", 6.8)

    if telefono_empresa:
        pdf.drawString(
            x_contacto,
            y_pie + 20,
            f"Tel: {telefono_empresa}",
        )

    if correo_empresa:
        pdf.drawString(
            x_contacto,
            y_pie + 8,
            correo_empresa,
        )

    # Mensaje final
    pdf.setFillColor(AZUL_OSCURO)
    pdf.setFont("Helvetica-Bold", 7.2)
    pdf.drawRightString(
        ANCHO - margen,
        y_pie + 20,
        "¡Gracias por confiar en nosotros!",
    )

    pdf.setFillColor(ROJO)
    pdf.setFont("Helvetica", 6.8)
    pdf.drawRightString(
        ANCHO - margen,
        y_pie + 8,
        "Estamos para mantenerte siempre conectado.",
    )

    # =====================================
    # FINALIZAR
    # =====================================

    pdf.showPage()
    pdf.save()

    buffer.seek(0)

    nombre_archivo = (
        f"{factura.numero}.pdf"
    )

    return StreamingResponse(
        buffer,
        media_type="application/pdf",
        headers={
            "Content-Disposition":
            f'inline; filename="{nombre_archivo}"'
        },
    )


# =========================================================
# DESCARGAR FACTURAS DEL MES EN ZIP
# =========================================================

@router.get(
    "/descargar-mes/zip"
)
async def descargar_facturas_mes(
    mes: int,
    anio: int,
    estado: str = "todas",
    session: Session = Depends(
        get_session
    ),
):
    """
    Genera un archivo ZIP con las facturas del mes seleccionado.

    Estado permitido:
    - todas
    - pendiente
    - pagada
    """

    if mes < 1 or mes > 12:
        raise HTTPException(
            status_code=400,
            detail="El mes debe estar entre 1 y 12",
        )

    if anio < 2000 or anio > 2100:
        raise HTTPException(
            status_code=400,
            detail="El año seleccionado no es válido",
        )

    estado = (estado or "todas").strip().lower()

    estados_permitidos = {
        "todas",
        "pendiente",
        "pagada",
    }

    if estado not in estados_permitidos:
        raise HTTPException(
            status_code=400,
            detail="Estado no válido",
        )

    facturas = session.exec(
        select(Factura)
        .order_by(Factura.numero)
    ).all()

    facturas_filtradas = []

    for factura in facturas:
        fecha = factura.fecha_emision

        if not fecha:
            continue

        if (
            fecha.month != mes
            or fecha.year != anio
        ):
            continue

        estado_factura = (
            factura.estado
            or ""
        ).strip().lower()

        if (
            estado != "todas"
            and estado_factura != estado
        ):
            continue

        facturas_filtradas.append(factura)

    if not facturas_filtradas:
        nombres_mes = [
            "",
            "enero",
            "febrero",
            "marzo",
            "abril",
            "mayo",
            "junio",
            "julio",
            "agosto",
            "septiembre",
            "octubre",
            "noviembre",
            "diciembre",
        ]

        raise HTTPException(
            status_code=404,
            detail=(
                f"No se encontraron facturas "
                f"{estado if estado != 'todas' else ''} "
                f"para {nombres_mes[mes]} de {anio}"
            ).strip(),
        )

    buffer_zip = BytesIO()

    with ZipFile(
        buffer_zip,
        mode="w",
        compression=ZIP_DEFLATED,
    ) as archivo_zip:

        for factura in facturas_filtradas:

            # Reutilizamos exactamente el mismo generador
            # profesional que se usa para la descarga individual.
            respuesta_pdf = generar_factura_pdf(
                factura.id,
                session,
            )

            contenido_pdf = b""

            async for fragmento in respuesta_pdf.body_iterator:
                contenido_pdf += fragmento

            nombre_pdf = (
                f"{factura.numero or factura.id}.pdf"
            )

            archivo_zip.writestr(
                nombre_pdf,
                contenido_pdf,
            )

    buffer_zip.seek(0)

    sufijo = {
        "todas": "TODAS",
        "pendiente": "PENDIENTES",
        "pagada": "PAGADAS",
    }[estado]

    nombre_archivo = (
        f"FACTURAS_{anio}_{mes:02d}_{sufijo}.zip"
    )

    return StreamingResponse(
        buffer_zip,
        media_type="application/zip",
        headers={
            "Content-Disposition":
            f'attachment; filename="{nombre_archivo}"'
        },
    )


# =========================================================
# OBTENER FACTURA
# =========================================================

@router.get(
    "/{factura_id}"
)
def obtener_factura(
    factura_id: UUID,
    session: Session = Depends(
        get_session
    ),
):

    factura = session.get(
        Factura,
        factura_id,
    )

    if not factura:

        raise HTTPException(
            status_code=404,
            detail="Factura no encontrada",
        )

    return factura


# =========================================================
# ACTUALIZAR FACTURA
# =========================================================

@router.put(
    "/{factura_id}"
)
def actualizar_factura(
    factura_id: UUID,
    datos: Factura,
    session: Session = Depends(
        get_session
    ),
):

    factura = session.get(
        Factura,
        factura_id,
    )

    if not factura:

        raise HTTPException(
            status_code=404,
            detail="Factura no encontrada",
        )

    factura.cliente_id = (
        datos.cliente_id
    )

    factura.servicio_id = (
        datos.servicio_id
    )

    factura.concepto = (
        datos.concepto
    )

    factura.subtotal = (
        datos.subtotal
    )

    factura.descuento = (
        datos.descuento
    )

    factura.total = (
        datos.total
    )

    factura.fecha_vencimiento = (
        datos.fecha_vencimiento
    )

    factura.estado = (
        datos.estado
    )

    factura.observaciones = (
        datos.observaciones
    )

    factura.updated_at = (
        datetime.now(
            timezone.utc
        )
    )

    session.add(
        factura
    )

    session.commit()

    session.refresh(
        factura
    )

    return factura


# =========================================================
# ANULAR FACTURA
# =========================================================

@router.delete(
    "/{factura_id}"
)
def anular_factura(
    factura_id: UUID,
    session: Session = Depends(
        get_session
    ),
):

    factura = session.get(
        Factura,
        factura_id,
    )

    if not factura:

        raise HTTPException(
            status_code=404,
            detail="Factura no encontrada",
        )

    factura.estado = "anulada"

    factura.updated_at = (
        datetime.now(
            timezone.utc
        )
    )

    session.add(
        factura
    )

    session.commit()

    session.refresh(
        factura
    )

    return factura