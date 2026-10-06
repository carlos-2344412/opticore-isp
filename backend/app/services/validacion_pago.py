from datetime import datetime, timedelta


def validar_comprobante(
    monto_detectado: float | None,
    monto_factura: float,
    banco_detectado: str | None,
    destinatario_detectado: str | None,
    fecha_detectada: datetime | None,
    fecha_emision: datetime,
) -> dict:

    errores = []
    validaciones = []

    # ========================================================
    # 1. MONTO
    # ========================================================

    if monto_detectado is None:

        errores.append(
            "No se pudo detectar el monto del comprobante"
        )

    elif monto_detectado < monto_factura:

        errores.append(
            f"El monto detectado ({monto_detectado}) "
            f"es menor al valor de la factura "
            f"({monto_factura})"
        )

    else:

        validaciones.append(
            "Monto correcto"
        )

    # ========================================================
    # 2. BANCO / CANAL
    # ========================================================

    if not banco_detectado:

        errores.append(
            "No se pudo detectar el banco o canal de pago"
        )

    else:

        banco = banco_detectado.strip().lower()

        canales_permitidos = {
            "bancolombia",
            "nequi",
        }

        if banco not in canales_permitidos:

            errores.append(
                f"Banco o canal no autorizado: "
                f"{banco_detectado}"
            )

        else:

            validaciones.append(
                f"Canal de pago correcto: "
                f"{banco_detectado}"
            )

    # ========================================================
    # 3. DESTINATARIO
    # ========================================================

    if not destinatario_detectado:

        errores.append(
            "No se pudo detectar el destinatario"
        )

    else:

        destinatario = (
            destinatario_detectado
            .strip()
            .upper()
        )

        # Nombre completo de la empresa
        if destinatario == "OPTIRAPIDO.NET SAS":

            validaciones.append(
                "Destinatario correcto"
            )

        # Nequi puede ocultar parte del nombre:
        #
        # OPT******** NET
        #
        # En este caso reconocemos que el OCR encontró
        # el fragmento visible del nombre.
        elif (
            "OPT" in destinatario
            and "NET" in destinatario
        ):

            validaciones.append(
                "Destinatario parcialmente identificado "
                "en comprobante"
            )

        else:

            errores.append(
                "Destinatario diferente al esperado: "
                f"{destinatario_detectado}"
            )

    # ========================================================
    # 4. FECHA
    # ========================================================

    if not fecha_detectada:

        errores.append(
            "No se pudo detectar la fecha del comprobante"
        )

    else:

        fecha_emision_naive = (
            fecha_emision.replace(
                tzinfo=None
            )
        )

        fecha_minima = (
            fecha_emision_naive
            - timedelta(days=7)
        )

        fecha_maxima = datetime.now()

        if fecha_detectada < fecha_minima:

            errores.append(
                "La fecha del comprobante es demasiado "
                "anterior a la factura"
            )

        elif fecha_detectada > fecha_maxima:

            errores.append(
                "La fecha del comprobante es futura"
            )

        else:

            validaciones.append(
                "Fecha válida"
            )

    # ========================================================
    # RESULTADO
    # ========================================================

    estado = (
        "validado"
        if not errores
        else "rechazado"
    )

    return {
        "estado": estado,
        "validaciones": validaciones,
        "errores": errores,
    }