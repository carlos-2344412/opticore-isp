import re
import subprocess
from datetime import datetime
from pathlib import Path


TESSERACT_PATH = r"C:\Program Files\Tesseract-OCR\tesseract.exe"


# ============================================================
# OCR
# ============================================================

def extraer_texto_ocr(ruta_imagen: str) -> str:
    ruta = Path(ruta_imagen)

    if not ruta.exists():
        raise FileNotFoundError(
            f"No existe el comprobante: {ruta}"
        )

    resultado = subprocess.run(
        [
            TESSERACT_PATH,
            str(ruta),
            "stdout",
            "-l",
            "spa",
        ],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )

    if resultado.returncode != 0:
        raise RuntimeError(
            f"Tesseract devolvió un error: {resultado.stderr}"
        )

    return resultado.stdout


# ============================================================
# CONVERTIR MONTO COLOMBIANO
# ============================================================

def convertir_monto(valor: str) -> float | None:
    valor = valor.strip()

    # Eliminar símbolos
    valor = valor.replace("$", "")
    valor = valor.replace(" ", "")

    # Formato colombiano:
    # 49.000,00
    # 80.000,00
    #
    # Se convierte a:
    # 49000.00
    if "." in valor and "," in valor:
        valor = valor.replace(".", "")
        valor = valor.replace(",", ".")

    # Formato:
    # 49000,00
    elif "," in valor:
        valor = valor.replace(",", ".")

    # Formato:
    # 49000
    else:
        valor = valor.replace(".", "")

    try:
        return float(valor)

    except ValueError:
        return None


# ============================================================
# EXTRAER FECHA EN ESPAÑOL
# ============================================================

def extraer_fecha(
    texto: str,
) -> datetime | None:

    meses = {
        "enero": 1,
        "febrero": 2,
        "marzo": 3,
        "abril": 4,
        "mayo": 5,
        "junio": 6,
        "julio": 7,
        "agosto": 8,
        "septiembre": 9,
        "setiembre": 9,
        "octubre": 10,
        "noviembre": 11,
        "diciembre": 12,
    }

    # ========================================================
    # FORMATO NEQUI
    #
    # 22 de septiembre de 2026 a las 02:43 p. m.
    # ========================================================

    patron_nequi = re.search(
        r"(\d{1,2})\s+de\s+"
        r"([A-Za-záéíóúÁÉÍÓÚ]+)\s+de\s+"
        r"(\d{4})"
        r"\s+(?:a\s+las|a)\s+"
        r"(\d{1,2}):(\d{2})\s*"
        r"([ap])\.?\s*m\.?",
        texto,
        re.IGNORECASE,
    )

    if patron_nequi:

        dia = int(patron_nequi.group(1))
        nombre_mes = patron_nequi.group(2).lower()
        anio = int(patron_nequi.group(3))

        hora = int(patron_nequi.group(4))
        minuto = int(patron_nequi.group(5))

        am_pm = patron_nequi.group(6).lower()

        mes = meses.get(nombre_mes)

        if mes:

            if am_pm == "p" and hora != 12:
                hora += 12

            if am_pm == "a" and hora == 12:
                hora = 0

            return datetime(
                anio,
                mes,
                dia,
                hora,
                minuto,
            )

    # ========================================================
    # FORMATO BANCOLOMBIA
    #
    # 05 de septiembre de 2026 - 02:18 p. m.
    # ========================================================

    patron_bancolombia = re.search(
        r"(\d{1,2})\s+de\s+"
        r"([A-Za-záéíóúÁÉÍÓÚ]+)\s+de\s+"
        r"(\d{4})"
        r"\s*-\s*"
        r"(\d{1,2}):(\d{2})\s*"
        r"([ap])\.?\s*m\.?",
        texto,
        re.IGNORECASE,
    )

    if patron_bancolombia:

        dia = int(patron_bancolombia.group(1))
        nombre_mes = patron_bancolombia.group(2).lower()
        anio = int(patron_bancolombia.group(3))

        hora = int(patron_bancolombia.group(4))
        minuto = int(patron_bancolombia.group(5))

        am_pm = patron_bancolombia.group(6).lower()

        mes = meses.get(nombre_mes)

        if mes:

            if am_pm == "p" and hora != 12:
                hora += 12

            if am_pm == "a" and hora == 12:
                hora = 0

            return datetime(
                anio,
                mes,
                dia,
                hora,
                minuto,
            )

    return None


# ============================================================
# EXTRAER DATOS DEL COMPROBANTE
# ============================================================

def extraer_datos_comprobante(
    ruta_imagen: str,
) -> dict:

    texto = extraer_texto_ocr(
        ruta_imagen
    )

    texto_normalizado = texto.replace(
        "\r",
        "",
    )

    # ========================================================
    # BANCO / CANAL
    # ========================================================

    banco_detectado = None

    # Bancolombia
    if re.search(
        r"\bBancolombia\b",
        texto_normalizado,
        re.IGNORECASE,
    ):
        banco_detectado = "Bancolombia"

    # Nequi
    elif re.search(
        r"\bNequi\b",
        texto_normalizado,
        re.IGNORECASE,
    ):
        banco_detectado = "Nequi"

    # ========================================================
    # REFERENCIA BANCARIA
    # ========================================================

    referencia_detectada = None

    # Bancolombia:
    # Comprobante No.
    coincidencia_bancolombia = re.search(
        r"Comprobante\s+No\.?"
        r"\s*\n?\s*"
        r"([A-Za-z0-9]{6,30})",
        texto_normalizado,
        re.IGNORECASE,
    )

    if coincidencia_bancolombia:

        referencia_detectada = (
            coincidencia_bancolombia.group(1)
        )

    # Nequi:
    # Referencia
    if not referencia_detectada:

        coincidencia_nequi = re.search(
            r"Referencia"
            r"\s*\n\s*"
            r"([A-Za-z0-9]{5,30})",
            texto_normalizado,
            re.IGNORECASE,
        )

        if coincidencia_nequi:

            referencia_detectada = (
                coincidencia_nequi.group(1)
            )

    # ========================================================
    # DESTINATARIO
    # ========================================================

    destinatario_detectado = None

    # --------------------------------------------------------
    # Bancolombia
    # Destinatario
    # OPTIRAPIDO.NET SAS
    # --------------------------------------------------------

    coincidencia_destinatario = re.search(
        r"Destinatario"
        r"\s*\n\s*"
        r"(.+)",
        texto_normalizado,
        re.IGNORECASE,
    )

    if coincidencia_destinatario:

        destinatario_detectado = (
            coincidencia_destinatario.group(1).strip()
        )

    # --------------------------------------------------------
    # Nequi
    # Para
    # Opt******** Net
    # --------------------------------------------------------

    if not destinatario_detectado:

        coincidencia_para = re.search(
            r"\bPara\b"
            r"\s*\n\s*"
            r"(.+)",
            texto_normalizado,
            re.IGNORECASE,
        )

        if coincidencia_para:

            destinatario_detectado = (
                coincidencia_para.group(1).strip()
            )

    # --------------------------------------------------------
    # Detectar nombre parcialmente oculto de OPTIRAPIDO
    #
    # Tesseract puede leer:
    # Optrreerer Net
    # Opt******* Net
    # Opt******* Net
    # --------------------------------------------------------

    if destinatario_detectado:

        texto_destinatario = (
            destinatario_detectado
            .strip()
            .upper()
        )

        if (
            "OPT" in texto_destinatario
            and "NET" in texto_destinatario
        ):
            destinatario_detectado = (
                "OPT******** NET"
            )

    # ========================================================
    # MONTO
    # ========================================================

    monto_detectado = None

    # --------------------------------------------------------
    # Bancolombia
    #
    # Valor
    # $ 80.000,00
    # --------------------------------------------------------

    coincidencia_valor = re.search(
        r"Valor"
        r"\s*\n\s*"
        r"\$?\s*"
        r"([\d\.,]+)",
        texto_normalizado,
        re.IGNORECASE,
    )

    if coincidencia_valor:

        monto_detectado = convertir_monto(
            coincidencia_valor.group(1)
        )

    # --------------------------------------------------------
    # Nequi
    #
    # ¿Cuánto?
    #
    # $ 49.000,00
    # --------------------------------------------------------

    if monto_detectado is None:

        coincidencia_cuanto = re.search(
            r"[¿?]?\s*Cu[aá]nto\s*[?]?"
            r"\s*\n\s*"
            r"\$?\s*"
            r"([\d\.,]+)",
            texto_normalizado,
            re.IGNORECASE,
        )

        if coincidencia_cuanto:

            monto_detectado = convertir_monto(
                coincidencia_cuanto.group(1)
            )

    # --------------------------------------------------------
    # Último respaldo: buscar cualquier valor con $
    # --------------------------------------------------------

    if monto_detectado is None:

        coincidencia_generica = re.search(
            r"\$\s*([\d\.,]+)",
            texto_normalizado,
        )

        if coincidencia_generica:

            monto_detectado = convertir_monto(
                coincidencia_generica.group(1)
            )

    # ========================================================
    # FECHA
    # ========================================================

    fecha_detectada = extraer_fecha(
        texto_normalizado
    )

    # ========================================================
    # RESULTADO
    # ========================================================

    return {
        "texto_ocr": texto,

        "monto_detectado": (
            monto_detectado
        ),

        "fecha_detectada": (
            fecha_detectada
        ),

        "banco_detectado": (
            banco_detectado
        ),

        "destinatario_detectado": (
            destinatario_detectado
        ),

        "referencia_detectada": (
            referencia_detectada
        ),
    }