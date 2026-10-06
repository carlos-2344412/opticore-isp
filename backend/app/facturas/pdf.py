from io import BytesIO

from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)


def formato_pesos(valor):
    """Convierte un número a formato de pesos colombianos."""
    if valor is None:
        valor = 0

    return f"${valor:,.0f}".replace(",", ".")


def generar_factura_pdf(
    factura,
    cliente,
    empresa,
    servicio=None,
):
    """
    Genera una factura en PDF y devuelve los datos
    como un archivo en memoria.
    """

    buffer = BytesIO()

    documento = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=40,
        leftMargin=40,
        topMargin=40,
        bottomMargin=40,
    )

    elementos = []

    estilos = getSampleStyleSheet()

    # =========================
    # ESTILOS PERSONALIZADOS
    # =========================

    titulo = ParagraphStyle(
        "TituloFactura",
        parent=estilos["Heading1"],
        fontSize=22,
        leading=26,
        spaceAfter=10,
        alignment=0,
    )

    subtitulo = ParagraphStyle(
        "SubtituloFactura",
        parent=estilos["Normal"],
        fontSize=10,
        leading=14,
    )

    titulo_seccion = ParagraphStyle(
        "TituloSeccion",
        parent=estilos["Heading3"],
        fontSize=12,
        leading=16,
        spaceBefore=10,
        spaceAfter=6,
    )

    normal = ParagraphStyle(
        "NormalFactura",
        parent=estilos["Normal"],
        fontSize=9,
        leading=13,
    )

    # =========================
    # ENCABEZADO
    # =========================

    empresa_nombre = empresa.nombre or "OPTIRÁPIDO"

    datos_empresa = [
        Paragraph(
            f"<b>{empresa_nombre}</b>",
            titulo,
        ),
        Paragraph(
            f"NIT: {empresa.nit or 'No registrado'}",
            subtitulo,
        ),
        Paragraph(
            f"Teléfono: {empresa.telefono or 'No registrado'}",
            subtitulo,
        ),
        Paragraph(
            f"Correo: {empresa.correo or 'No registrado'}",
            subtitulo,
        ),
    ]

    datos_factura = [
        Paragraph(
            "<b>FACTURA DE SERVICIO</b>",
            titulo_seccion,
        ),
        Paragraph(
            f"<b>Número:</b> {factura.numero}",
            normal,
        ),
        Paragraph(
            f"<b>Referencia de pago:</b> "
            f"{factura.referencia_pago or 'No asignada'}",
            normal,
        ),
        Paragraph(
            f"<b>Estado:</b> {factura.estado}",
            normal,
        ),
    ]

    tabla_encabezado = Table(
        [
            [
                datos_empresa,
                datos_factura,
            ]
        ],
        colWidths=[260, 250],
    )

    tabla_encabezado.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("BOX", (0, 0), (-1, -1), 0.8, colors.black),
                ("INNERGRID", (0, 0), (-1, -1), 0.4, colors.grey),
                ("LEFTPADDING", (0, 0), (-1, -1), 12),
                ("RIGHTPADDING", (0, 0), (-1, -1), 12),
                ("TOPPADDING", (0, 0), (-1, -1), 12),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 12),
            ]
        )
    )

    elementos.append(tabla_encabezado)
    elementos.append(Spacer(1, 20))

    # =========================
    # DATOS DEL CLIENTE
    # =========================

    elementos.append(
        Paragraph(
            "DATOS DEL CLIENTE",
            titulo_seccion,
        )
    )

    nombre_cliente = (
        f"{cliente.nombre or ''} "
        f"{cliente.apellido or ''}"
    ).strip()

    datos_cliente = [
        [
            Paragraph(
                "<b>Cliente</b>",
                normal,
            ),
            Paragraph(
                nombre_cliente,
                normal,
            ),
        ],
        [
            Paragraph(
                "<b>Documento</b>",
                normal,
            ),
            Paragraph(
                str(cliente.documento or "No registrado"),
                normal,
            ),
        ],
        [
            Paragraph(
                "<b>Teléfono</b>",
                normal,
            ),
            Paragraph(
                str(cliente.telefono or "No registrado"),
                normal,
            ),
        ],
        [
            Paragraph(
                "<b>Correo</b>",
                normal,
            ),
            Paragraph(
                str(cliente.correo or "No registrado"),
                normal,
            ),
        ],
        [
            Paragraph(
                "<b>Dirección</b>",
                normal,
            ),
            Paragraph(
                str(cliente.direccion or "No registrada"),
                normal,
            ),
        ],
        [
            Paragraph(
                "<b>Ciudad</b>",
                normal,
            ),
            Paragraph(
                str(cliente.ciudad or "No registrada"),
                normal,
            ),
        ],
    ]

    tabla_cliente = Table(
        datos_cliente,
        colWidths=[120, 390],
    )

    tabla_cliente.setStyle(
        TableStyle(
            [
                ("BOX", (0, 0), (-1, -1), 0.6, colors.black),
                ("INNERGRID", (0, 0), (-1, -1), 0.3, colors.grey),
                ("BACKGROUND", (0, 0), (0, -1), colors.lightgrey),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )

    elementos.append(tabla_cliente)
    elementos.append(Spacer(1, 20))

    # =========================
    # INFORMACIÓN DEL SERVICIO
    # =========================

    elementos.append(
        Paragraph(
            "DETALLE DEL SERVICIO",
            titulo_seccion,
        )
    )

    descripcion_servicio = factura.concepto

    if servicio:
        descripcion_servicio = (
            f"{factura.concepto}<br/>"
            f"Servicio asociado: {servicio.tipo}"
        )

    datos_servicio = [
        [
            Paragraph("<b>Descripción</b>", normal),
            Paragraph("<b>Valor</b>", normal),
        ],
        [
            Paragraph(
                descripcion_servicio,
                normal,
            ),
            Paragraph(
                formato_pesos(factura.subtotal),
                normal,
            ),
        ],
    ]

    tabla_servicio = Table(
        datos_servicio,
        colWidths=[380, 130],
    )

    tabla_servicio.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("ALIGN", (1, 0), (1, -1), "RIGHT"),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                ("TOPPADDING", (0, 0), (-1, -1), 8),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
            ]
        )
    )

    elementos.append(tabla_servicio)
    elementos.append(Spacer(1, 15))

    # =========================
    # TOTALES
    # =========================

    datos_totales = [
        [
            Paragraph("<b>Subtotal</b>", normal),
            Paragraph(
                formato_pesos(factura.subtotal),
                normal,
            ),
        ],
        [
            Paragraph("<b>Descuento</b>", normal),
            Paragraph(
                formato_pesos(factura.descuento),
                normal,
            ),
        ],
        [
            Paragraph("<b>TOTAL A PAGAR</b>", normal),
            Paragraph(
                f"<b>{formato_pesos(factura.total)}</b>",
                normal,
            ),
        ],
    ]

    tabla_totales = Table(
        datos_totales,
        colWidths=[160, 140],
        hAlign="RIGHT",
    )

    tabla_totales.setStyle(
        TableStyle(
            [
                ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
                ("BACKGROUND", (0, 2), (-1, 2), colors.lightgrey),
                ("ALIGN", (1, 0), (1, -1), "RIGHT"),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                ("TOPPADDING", (0, 0), (-1, -1), 8),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
            ]
        )
    )

    elementos.append(tabla_totales)
    elementos.append(Spacer(1, 20))

    # =========================
    # FECHAS
    # =========================

    fecha_emision = (
        factura.fecha_emision.strftime("%d/%m/%Y")
        if factura.fecha_emision
        else "No registrada"
    )

    fecha_vencimiento = (
        factura.fecha_vencimiento.strftime("%d/%m/%Y")
        if factura.fecha_vencimiento
        else "No registrada"
    )

    elementos.append(
        Paragraph(
            f"<b>Fecha de emisión:</b> {fecha_emision}",
            normal,
        )
    )

    elementos.append(
        Paragraph(
            f"<b>Fecha de vencimiento:</b> "
            f"{fecha_vencimiento}",
            normal,
        )
    )

    elementos.append(Spacer(1, 15))

    # =========================
    # REFERENCIA DE PAGO
    # =========================

    elementos.append(
        Paragraph(
            "INFORMACIÓN DE PAGO",
            titulo_seccion,
        )
    )

    elementos.append(
        Paragraph(
            "Para realizar el pago, utiliza la siguiente "
            "referencia:",
            normal,
        )
    )

    elementos.append(Spacer(1, 8))

    referencia = factura.referencia_pago or "No asignada"

    referencia_style = ParagraphStyle(
        "ReferenciaPago",
        parent=estilos["Heading2"],
        fontSize=16,
        leading=20,
        alignment=1,
    )

    elementos.append(
        Paragraph(
            f"<b>{referencia}</b>",
            referencia_style,
        )
    )

    elementos.append(Spacer(1, 20))

    # =========================
    # OBSERVACIONES
    # =========================

    if factura.observaciones:

        elementos.append(
            Paragraph(
                "OBSERVACIONES",
                titulo_seccion,
            )
        )

        elementos.append(
            Paragraph(
                str(factura.observaciones),
                normal,
            )
        )

        elementos.append(Spacer(1, 15))

    # =========================
    # PIE DE PÁGINA
    # =========================

    elementos.append(
        Paragraph(
            "Gracias por utilizar los servicios de "
            f"{empresa_nombre}.",
            normal,
        )
    )

    elementos.append(
        Paragraph(
            "Este documento fue generado automáticamente "
            "por el sistema OptiCore ISP.",
            normal,
        )
    )

    documento.build(elementos)

    buffer.seek(0)

    return buffer