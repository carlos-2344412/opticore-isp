import re

from sqlmodel import Session, select

from app.models.cliente import Cliente
from app.models.servicio import Servicio
from app.models.factura import Factura
from app.models.plan import Plan
from app.models.pago import Pago
from app.models.soporte import SolicitudSoporte
from app.models.conversacion_chatbot import ConversacionChatbot


# =========================================================
# MEMORIA TEMPORAL DE CONVERSACIONES
# =========================================================

# Por ahora utilizaremos memoria en Python para probar
# el funcionamiento del chatbot.
#
# Más adelante podemos mover esta información a Redis
# cuando conectemos WhatsApp.

conversaciones = {}


# =========================================================
# FUNCIONES GENERALES
# =========================================================

def normalizar_texto(texto: str) -> str:
    """
    Convierte el mensaje a minúsculas y elimina
    espacios innecesarios.
    """

    texto = texto.lower().strip()
    texto = re.sub(r"\s+", " ", texto)

    return texto


def obtener_clave_conversacion(
    empresa_id,
    telefono=None,
    cliente_id=None,
):
    """
    Genera una clave única para identificar
    una conversación.
    """

    if telefono:
        return f"{empresa_id}:telefono:{telefono}"

    if cliente_id:
        return f"{empresa_id}:cliente:{cliente_id}"

    return f"{empresa_id}:anonimo"


def es_documento(mensaje: str) -> bool:
    """
    Detecta si el mensaje parece ser un número de documento.

    Se aceptan entre 6 y 15 dígitos.
    """

    mensaje = mensaje.strip()

    return bool(re.fullmatch(r"\d{6,15}", mensaje))


# =========================================================
# BÚSQUEDA DE CLIENTES
# =========================================================

def buscar_cliente(
    session: Session,
    empresa_id,
    cliente_id=None,
    telefono=None,
):
    """
    Busca un cliente mediante su ID o teléfono.
    """

    if cliente_id:

        cliente = session.exec(
            select(Cliente).where(
                Cliente.id == cliente_id,
                Cliente.empresa_id == empresa_id,
            )
        ).first()

        if cliente:
            return cliente

    if telefono:

        cliente = session.exec(
            select(Cliente).where(
                Cliente.telefono == telefono,
                Cliente.empresa_id == empresa_id,
            )
        ).first()

        if cliente:
            return cliente

    return None


def buscar_cliente_por_documento(
    session: Session,
    empresa_id,
    documento: str,
):
    """
    Busca un cliente mediante su número de cédula
    o documento.
    """

    return session.exec(
        select(Cliente).where(
            Cliente.documento == documento,
            Cliente.empresa_id == empresa_id,
        )
    ).first()


# =========================================================
# INFORMACIÓN DEL CLIENTE
# =========================================================

def obtener_nombre_cliente(cliente: Cliente) -> str:

    partes = [cliente.nombre]

    if cliente.apellido:
        partes.append(cliente.apellido)

    return " ".join(partes)


def obtener_servicios_cliente(
    session: Session,
    empresa_id,
    cliente_id,
):

    return session.exec(
        select(Servicio).where(
            Servicio.empresa_id == empresa_id,
            Servicio.cliente_id == cliente_id,
        )
    ).all()


def obtener_facturas_cliente(
    session: Session,
    empresa_id,
    cliente_id,
):

    return session.exec(
        select(Factura).where(
            Factura.empresa_id == empresa_id,
            Factura.cliente_id == cliente_id,
        )
    ).all()


def obtener_pagos_cliente(
    session: Session,
    empresa_id,
    cliente_id,
):

    return session.exec(
        select(Pago).where(
            Pago.empresa_id == empresa_id,
            Pago.cliente_id == cliente_id,
        )
    ).all()

# =========================================================
# SOPORTE TÉCNICO
# =========================================================

def buscar_solicitud_pendiente(
    session: Session,
    empresa_id,
    cliente_id,
):
    """
    Busca si el cliente ya tiene una solicitud
    de soporte que todavía está pendiente.
    """

    return session.exec(
        select(SolicitudSoporte).where(
            SolicitudSoporte.empresa_id == empresa_id,
            SolicitudSoporte.cliente_id == cliente_id,
            SolicitudSoporte.estado.in_([
                "pendiente",
                "asignada",
                "en_proceso",
            ]),
        )
    ).first()
# =========================================================
# DETECCIÓN DE INTENCIONES
# =========================================================

def detectar_intencion(mensaje: str) -> str:

    mensaje = normalizar_texto(mensaje)

    if any(
        palabra in mensaje
        for palabra in [
            "hola",
            "buenos dias",
            "buenas tardes",
            "buenas noches",
            "hey",
            "saludos",
        ]
    ):
        return "saludo"

    if any(
        palabra in mensaje
        for palabra in [
            "factura",
            "facturas",
            "debo",
            "deuda",
            "saldo",
            "pendiente",
            "vencida",
        ]
    ):
        return "facturas"

    if any(
        palabra in mensaje
        for palabra in [
            "pago",
            "pague",
            "pagado",
            "transferencia",
            "consignacion",
            "consignación",
        ]
    ):
        return "pagos"

    if any(
        palabra in mensaje
        for palabra in [
            "no tengo internet",
            "sin internet",
            "internet lento",
            "internet esta lento",
            "internet está lento",
            "conexion",
            "conexión",
            "servicio activo",
            "mi servicio",
        ]
    ):
        return "servicio"

    if any(
        palabra in mensaje
        for palabra in [
            "tecnico",
            "técnico",
            "soporte",
            "visita",
            "reparacion",
            "reparación",
        ]
    ):
        return "soporte"

    if any(
        palabra in mensaje
        for palabra in [
            "quiero instalar",
            "quiero contratar",
            "quiero internet",
            "quiero adquirir",
            "deseo instalar",
            "deseo contratar",
            "deseo internet",
            "necesito instalar",
            "necesito internet",
            "contratar internet",
            "instalar internet",
        ]
    ):
        return "contratacion"

    if any(
        palabra in mensaje
        for palabra in [
            "plan",
            "planes",
            "instalacion",
            "instalación",
            "informacion",
            "información",
        ]
    ):
        return "informacion"

    return "general"


# =========================================================
# IDENTIFICACIÓN DEL CLIENTE
# =========================================================

def requiere_identificacion(intencion: str) -> bool:
    """
    Determina qué consultas requieren conocer
    la identidad del cliente.
    """

    return intencion in [
        "facturas",
        "pagos",
        "servicio",
        "soporte",
    ]


# =========================================================
# CONVERSACIONES DEL CHATBOT
# =========================================================

def obtener_conversacion_chatbot(
    session: Session,
    empresa_id,
    telefono=None,
    cliente_id=None,
):
    """
    Busca una conversación existente en PostgreSQL.

    Se intenta identificar primero mediante el teléfono.
    Si no existe teléfono, se utiliza el cliente_id.
    """

    consulta = select(ConversacionChatbot).where(
        ConversacionChatbot.empresa_id == empresa_id
    )

    if telefono:
        consulta = consulta.where(
            ConversacionChatbot.telefono == telefono
        )

    elif cliente_id:
        consulta = consulta.where(
            ConversacionChatbot.cliente_id == cliente_id
        )

    else:
        return None

    return session.exec(consulta).first()


def obtener_o_crear_conversacion(
    session: Session,
    empresa_id,
    telefono=None,
    cliente_id=None,
):
    """
    Obtiene una conversación existente.

    Si no existe, crea una nueva conversación
    en PostgreSQL.
    """

    conversacion = obtener_conversacion_chatbot(
        session=session,
        empresa_id=empresa_id,
        telefono=telefono,
        cliente_id=cliente_id,
    )

    if conversacion:
        return conversacion

    conversacion = ConversacionChatbot(
        empresa_id=empresa_id,
        telefono=telefono,
        cliente_id=cliente_id,
        esperando_documento=False,
        esperando_descripcion_soporte=False,
    )

    session.add(conversacion)
    session.commit()
    session.refresh(conversacion)

    return conversacion


def guardar_conversacion(
    session: Session,
    conversacion: ConversacionChatbot,
):
    """
    Guarda los cambios realizados en una conversación.
    """

    session.add(conversacion)
    session.commit()
    session.refresh(conversacion)

# =========================================================
# PROCESAMIENTO PRINCIPAL DEL CHATBOT
# =========================================================

def procesar_mensaje(
    session: Session,
    empresa_id,
    mensaje: str,
    cliente_id=None,
    telefono=None,
):

   

    # =====================================================
    # OBTENER CONVERSACIÓN DESDE POSTGRESQL
    # =====================================================

    conversacion = obtener_o_crear_conversacion(
        session=session,
        empresa_id=empresa_id,
        telefono=telefono,
        cliente_id=cliente_id,
    )

    # =====================================================
    # IDENTIFICAR CLIENTE PREVIAMENTE GUARDADO
    # =====================================================

    cliente = None

    if conversacion.cliente_id:

        cliente = buscar_cliente(
            session=session,
            empresa_id=empresa_id,
            cliente_id=conversacion.cliente_id,
        )

    # =====================================================
    # CONTRATACIÓN - CAPTURAR DOCUMENTO
    # =====================================================

    if (
        conversacion.esperando_datos_contratacion
        and conversacion.paso_contratacion == "documento"
        and not cliente
    ):

        documento = mensaje.strip()

        if not es_documento(documento):
            return {
                "respuesta": (
                    "Por favor, escribe un número de cédula válido. "
                    "Solo necesito los números, sin puntos ni espacios."
                ),
                "intencion": "contratacion",
                "requiere_tecnico": False,
                "datos": {
                    "cliente_nuevo": True,
                    "paso": "documento",
                },
            }

        cliente_existente = buscar_cliente_por_documento(
            session=session,
            empresa_id=empresa_id,
            documento=documento,
        )

        if cliente_existente:
            return {
                "respuesta": (
                    "La cédula que ingresaste ya aparece registrada "
                    "en OPTIRÁPIDO. 🔐\n\n"
                    "Si ya eres cliente, puedo ayudarte con tu "
                    "servicio, factura, pago o soporte técnico."
                ),
                "intencion": "contratacion",
                "requiere_tecnico": False,
                "datos": {
                    "cliente_nuevo": False,
                    "cliente_id": str(cliente_existente.id),
                },
            }

        conversacion.documento_contratacion = documento
        conversacion.paso_contratacion = "direccion"

        guardar_conversacion(
            session,
            conversacion,
        )

        return {
            "respuesta": (
                "Perfecto. ✅\n\n"
                "Ahora necesito la dirección donde deseas "
                "instalar el servicio."
            ),
            "intencion": "contratacion",
            "requiere_tecnico": False,
            "datos": {
                "cliente_nuevo": True,
                "paso": "direccion",
                "documento": documento,
            },
        }
    # =====================================================
    # CLIENTE ENVIÓ UN DOCUMENTO
    # =====================================================

    if es_documento(mensaje):

        cliente_documento = buscar_cliente_por_documento(
            session=session,
            empresa_id=empresa_id,
            documento=mensaje.strip(),
        )

        if cliente_documento:

            nombre = obtener_nombre_cliente(cliente_documento)

            conversacion.cliente_id = cliente_documento.id
            conversacion.esperando_documento = False

            guardar_conversacion(session, conversacion)

            return {
                "respuesta": (
                    f"¡Perfecto, {nombre}! ✅ "
                    "He identificado correctamente tu cuenta. "
                    "Ahora puedes consultarme sobre tus facturas, "
                    "pagos, servicio de internet o soporte técnico."
                ),
                "intencion": "identificacion",
                "requiere_tecnico": False,
                "datos": {
                    "cliente_id": str(cliente_documento.id),
                    "cliente_identificado": True,
                },
            }

        return {
            "respuesta": (
                "No encontré ningún cliente registrado con ese "
                "número de documento. Por favor verifica tu cédula "
                "e inténtalo nuevamente."
            ),
            "intencion": "identificacion",
            "requiere_tecnico": False,
            "datos": {
                "cliente_identificado": False,
            },
        }

    # =====================================================
    # BUSCAR CLIENTE POR ID O TELÉFONO
    # =====================================================

    if not cliente:

        cliente = buscar_cliente(
            session=session,
            empresa_id=empresa_id,
            cliente_id=cliente_id,
            telefono=telefono,
        )

        # Si encontramos el cliente, guardamos su ID
        # en la conversación.

        if cliente:

             conversacion.cliente_id = cliente.id
             guardar_conversacion(
                 session,
                 conversacion,
             )

    # =====================================================
    # CLIENTE ESTÁ DESCRIBIENDO UN PROBLEMA DE SOPORTE
    # =====================================================

    if (
        conversacion.esperando_descripcion_soporte
        and cliente
    ):

        # Evitar mensajes demasiado cortos

        if len(mensaje.strip()) < 5:

            return {
                "respuesta": (
                    "Por favor, descríbeme un poco mejor el "
                    "problema que estás presentando. 🔧"
                ),
                "intencion": "soporte",
                "requiere_tecnico": True,
                "datos": {},
            }

        # Buscar solicitudes abiertas del cliente

        solicitud_existente = buscar_solicitud_pendiente(
            session=session,
            empresa_id=empresa_id,
            cliente_id=cliente.id,
        )

        if solicitud_existente:

            conversacion.esperando_descripcion_soporte = False

            guardar_conversacion(session, conversacion)

            return {
                "respuesta": (
                    "Ya tienes una solicitud de soporte en proceso. 🔧\n\n"
                    f"Problema reportado: "
                    f"{solicitud_existente.descripcion}\n\n"
                    "Un miembro de nuestro equipo la revisará "
                    "lo antes posible."
                ),
                "intencion": "soporte",
                "requiere_tecnico": True,
                "datos": {
                    "solicitud_id": str(solicitud_existente.id),
                    "estado": solicitud_existente.estado,
                    "solicitud_existente": True,
                },
            }

        # Crear nueva solicitud

        solicitud = SolicitudSoporte(
            empresa_id=empresa_id,
            cliente_id=cliente.id,
            descripcion=mensaje.strip(),
            estado="pendiente",
            prioridad="normal",
            origen="whatsapp",
        )

        session.add(solicitud)

        session.commit()

        session.refresh(solicitud)

        conversacion["esperando_descripcion_soporte"] = False

        return {
            "respuesta": (
                "¡Listo! ✅ Tu solicitud de soporte técnico fue "
                "registrada correctamente.\n\n"
                "Un técnico o miembro de nuestro equipo revisará "
                "tu caso lo antes posible. 🔧"
            ),
            "intencion": "soporte",
            "requiere_tecnico": True,
            "datos": {
                "solicitud_id": str(solicitud.id),
                "estado": solicitud.estado,
                "solicitud_creada": True,
            },
        }
    # =====================================================
    # CONTRATACIÓN - CAPTURAR DATOS
    # =====================================================

    if (
        conversacion.esperando_datos_contratacion
        and conversacion.paso_contratacion == "nombre"
        and not cliente
    ):

        nombre = mensaje.strip()

        if len(nombre) < 3:
            return {
                "respuesta": (
                    "Por favor, dime tu nombre completo. 😊"
                ),
                "intencion": "contratacion",
                "requiere_tecnico": False,
                "datos": {
                    "cliente_nuevo": True,
                    "paso": "nombre",
                },
            }

        conversacion.nombre_contratacion = nombre
        conversacion.paso_contratacion = "documento"

        guardar_conversacion(
            session,
            conversacion,
        )

        return {
            "respuesta": (
                f"Perfecto, {nombre}. 😊\n\n"
                "Ahora necesito tu número de cédula."
            ),
            "intencion": "contratacion",
            "requiere_tecnico": False,
            "datos": {
                "cliente_nuevo": True,
                "paso": "documento",
                "nombre": nombre,
            },
        }

    # =====================================================
    # CONTRATACIÓN - CAPTURAR DOCUMENTO
    # =====================================================

    if (
        conversacion.esperando_datos_contratacion
        and conversacion.paso_contratacion == "documento"
        and not cliente
    ):

        documento = mensaje.strip()

        if not es_documento(documento):
            return {
                "respuesta": (
                    "Por favor, escribe un número de cédula válido. "
                    "Solo necesito los números, sin puntos ni espacios."
                ),
                "intencion": "contratacion",
                "requiere_tecnico": False,
                "datos": {
                    "cliente_nuevo": True,
                    "paso": "documento",
                },
            }

        cliente_existente = buscar_cliente_por_documento(
            session=session,
            empresa_id=empresa_id,
            documento=documento,
        )

        if cliente_existente:
            return {
                "respuesta": (
                    "La cédula que ingresaste ya aparece registrada "
                    "en OPTIRÁPIDO. 🔐\n\n"
                    "Si ya eres cliente, puedo ayudarte con tu "
                    "servicio, factura, pago o soporte técnico."
                ),
                "intencion": "contratacion",
                "requiere_tecnico": False,
                "datos": {
                    "cliente_nuevo": False,
                    "cliente_id": str(cliente_existente.id),
                },
            }

        conversacion.documento_contratacion = documento
        conversacion.paso_contratacion = "direccion"

        guardar_conversacion(
            session,
            conversacion,
        )

        return {
            "respuesta": (
                "Perfecto. ✅\n\n"
                "Ahora necesito la dirección donde deseas "
                "instalar el servicio."
            ),
            "intencion": "contratacion",
            "requiere_tecnico": False,
            "datos": {
                "cliente_nuevo": True,
                "paso": "direccion",
                "documento": documento,
            },
        }
   
    # =====================================================
    # CONTRATACIÓN - CAPTURAR DIRECCIÓN
    # =====================================================

    if (
        conversacion.esperando_datos_contratacion
        and conversacion.paso_contratacion == "direccion"
        and not cliente
    ):

        direccion = mensaje.strip()

        if len(direccion) < 5:
            return {
                "respuesta": (
                    "Por favor, escribe la dirección completa "
                    "donde deseas instalar el servicio. 📍"
                ),
                "intencion": "contratacion",
                "requiere_tecnico": False,
                "datos": {
                    "cliente_nuevo": True,
                    "paso": "direccion",
                },
            }

        conversacion.direccion_contratacion = direccion
        conversacion.paso_contratacion = "plan"

        guardar_conversacion(
            session,
            conversacion,
        )

        return {
            "respuesta": (
                "Perfecto. 📍\n\n"
                f"Dirección de instalación: {direccion}\n\n"
                "Ahora voy a mostrarte los planes disponibles "
                "para que puedas elegir el que deseas contratar."
            ),
            "intencion": "contratacion",
            "requiere_tecnico": False,
            "datos": {
                "cliente_nuevo": True,
                "paso": "plan",
                "direccion": direccion,
            },
        }

    # =====================================================
    # CONTRATACIÓN - MOSTRAR PLANES
    # =====================================================

    if (
        conversacion.esperando_datos_contratacion
        and conversacion.paso_contratacion == "plan"
        and not cliente
    ):


        planes = session.exec(
            select(Plan).where(
                Plan.empresa_id == empresa_id,
                Plan.estado == True,
            )
        ).all()

        if not planes:
            return {
                "respuesta": (
                    "En este momento no hay planes disponibles "
                    "para contratar. 😔\n\n"
                    "Por favor, comunícate con nuestro equipo "
                    "para continuar con la instalación."
                ),
                "intencion": "contratacion",
                "requiere_tecnico": False,
                "datos": {
                    "cliente_nuevo": True,
                    "paso": "plan",
                    "planes_disponibles": 0,
                },
            }

        respuesta_planes = (
            "Estos son los planes disponibles en OPTIRÁPIDO: 🌐\n\n"
        )

        for indice, plan in enumerate(planes, start=1):
            respuesta_planes += (
                f"{indice}. {plan.nombre}\n"
                f"   Velocidad: {plan.velocidad_bajada} Mbps "
                f"de bajada / {plan.velocidad_subida} Mbps de subida\n"
                f"   Precio: ${plan.precio_mensual:,.0f} mensuales\n\n"
            )

        respuesta_planes += (
            "Escribe el número del plan que deseas contratar."
        )

        conversacion.paso_contratacion = "seleccionar_plan"

        guardar_conversacion(
            session,
            conversacion,
        )

        return {
            "respuesta": respuesta_planes,
            "intencion": "contratacion",
            "requiere_tecnico": False,
            "datos": {
                "cliente_nuevo": True,
                "paso": "seleccionar_plan",
                "planes_disponibles": len(planes),
            },
        }

    # =====================================================
    # CONTRATACIÓN - SELECCIONAR PLAN
    # =====================================================

    if (
        conversacion.esperando_datos_contratacion
        and conversacion.paso_contratacion == "seleccionar_plan"
        and not cliente
    ):

        respuesta_plan = mensaje.strip()

        # Aceptar respuestas como "1", "2", ",1", ",2", etc.
        numeros = re.findall(r"\d+", respuesta_plan)

        if not numeros:
            return {
                "respuesta": (
                    "Por favor, escribe el número del plan que deseas "
                    "contratar. 😊"
                ),
                "intencion": "contratacion",
                "requiere_tecnico": False,
                "datos": {
                    "cliente_nuevo": True,
                    "paso": "seleccionar_plan",
                },
            }

        indice_plan = int(numeros[0])

        planes = session.exec(
            select(Plan).where(
                Plan.empresa_id == empresa_id,
                Plan.estado == True,
            )
        ).all()

        if indice_plan < 1 or indice_plan > len(planes):
            return {
                "respuesta": (
                    "El número de plan que seleccionaste no es válido. "
                    "Por favor, elige uno de los planes disponibles."
                ),
                "intencion": "contratacion",
                "requiere_tecnico": False,
                "datos": {
                    "cliente_nuevo": True,
                    "paso": "seleccionar_plan",
                    "planes_disponibles": len(planes),
                },
            }

        plan = planes[indice_plan - 1]

        conversacion.plan_contratacion = plan.id
        conversacion.paso_contratacion = "confirmacion"

        guardar_conversacion(
            session,
            conversacion,
        )

        return {
            "respuesta": (
                "¡Perfecto! ✅\n\n"
                f"Has seleccionado el plan: {plan.nombre}\n"
                f"Velocidad: {plan.velocidad_bajada} Mbps de bajada / "
                f"{plan.velocidad_subida} Mbps de subida\n"
                f"Precio mensual: ${plan.precio_mensual:,.0f}\n\n"
                "Ahora vamos a confirmar tus datos antes de continuar "
                "con la instalación.\n\n"
                "Responde *SI* para confirmar o *NO* para cancelar."
            ),
            "intencion": "contratacion",
            "requiere_tecnico": False,
            "datos": {
                "cliente_nuevo": True,
                "paso": "confirmacion",
                "plan_id": str(plan.id),
                "plan": plan.nombre,
                "precio": plan.precio_mensual,
            },
        }

    # =====================================================
    # CONTRATACIÓN - CONFIRMAR DATOS
    # =====================================================

    if (
        conversacion.esperando_datos_contratacion
        and conversacion.paso_contratacion == "confirmacion"
        and not cliente
    ):

        respuesta_confirmacion = mensaje.strip().lower()

        # CONFIRMAR
        if respuesta_confirmacion in ["si", "sí", "s", "confirmar"]:

            conversacion.paso_contratacion = "programacion"
            guardar_conversacion(
                session,
                conversacion,
            )

            return {
                "respuesta": (
                    "¡Perfecto! ✅ Tus datos han sido confirmados.\n\n"
                    "Ahora vamos a continuar con la programación de la "
                    "instalación de tu servicio.\n\n"
                    "En el siguiente paso te mostraré los horarios "
                    "disponibles para realizar la instalación."
                ),
                "intencion": "contratacion",
                "requiere_tecnico": True,
                "datos": {
                    "cliente_nuevo": True,
                    "paso": "programacion",
                    "nombre": conversacion.nombre_contratacion,
                    "documento": conversacion.documento_contratacion,
                    "direccion": conversacion.direccion_contratacion,
                    "plan_id": (
                        str(conversacion.plan_contratacion)
                        if conversacion.plan_contratacion
                        else None
                    ),
                },
            }

        # CANCELAR
        if respuesta_confirmacion in ["no", "n", "cancelar"]:

            conversacion.esperando_datos_contratacion = False
            conversacion.paso_contratacion = None
            conversacion.nombre_contratacion = None
            conversacion.documento_contratacion = None
            conversacion.direccion_contratacion = None
            conversacion.plan_contratacion = None

            guardar_conversacion(
                session,
                conversacion,
            )

            return {
                "respuesta": (
                    "Entendido. ❌ La contratación ha sido cancelada.\n\n"
                    "Si deseas contratar el servicio más adelante, "
                    "solo escribe *quiero contratar internet*."
                ),
                "intencion": "contratacion",
                "requiere_tecnico": False,
                "datos": {
                    "cliente_nuevo": True,
                    "paso": "cancelado",
                },
            }

        # RESPUESTA NO RECONOCIDA
        return {
            "respuesta": (
                "Por favor, responde *SI* para confirmar tus datos "
                "o *NO* para cancelar la contratación."
            ),
            "intencion": "contratacion",
            "requiere_tecnico": False,
            "datos": {
                "cliente_nuevo": True,
                "paso": "confirmacion",
            },
        }
    # =====================================================
    # DETECTAR INTENCIÓN
    # =====================================================

    intencion = detectar_intencion(mensaje)
    
    # =====================================================
    # NUEVO CLIENTE - CONTRATACIÓN
    # =====================================================

    if intencion == "contratacion" and not cliente:

        conversacion.esperando_datos_contratacion = True
        conversacion.paso_contratacion = "nombre"

        guardar_conversacion(
            session,
            conversacion,
        )

        return {
            "respuesta": (
                "¡Excelente! 😊 Me alegra que quieras contratar "
                "internet con OPTIRÁPIDO.\n\n"
                "Para comenzar con tu instalación necesito algunos "
                "datos.\n\n"
                "Por favor, dime tu nombre completo."
            ),
            "intencion": "contratacion",
            "requiere_tecnico": False,
            "datos": {
                "cliente_nuevo": True,
                "paso": "nombre",
            },
        }
    # =====================================================
    # SOLICITAR IDENTIFICACIÓN
    # =====================================================

    if requiere_identificacion(intencion) and not cliente:

        conversacion.esperando_documento = True

        guardar_conversacion(session, conversacion)

        return {
            "respuesta": (
                "Para consultar información de tu cuenta necesito "
                "identificarte. 🔐\n\n"
                "Por favor, escribe tu número de cédula."
            ),
            "intencion": intencion,
            "requiere_tecnico": False,
            "datos": {
                "requiere_identificacion": True,
            },
        }

    # =====================================================
    # SALUDO
    # =====================================================

    if intencion == "saludo":

        if cliente:

            nombre = obtener_nombre_cliente(cliente)

            return {
                "respuesta": (
                    f"¡Hola, {nombre}! 👋 "
                    "Bienvenido al asistente virtual de OPTIRÁPIDO. "
                    "¿En qué puedo ayudarte hoy?"
                ),
                "intencion": intencion,
                "requiere_tecnico": False,
                "datos": {
                    "cliente_identificado": True,
                },
            }

        return {
            "respuesta": (
                "¡Hola! 👋 Bienvenido al asistente virtual de "
                "OPTIRÁPIDO.\n\n"
                "Puedo ayudarte con información sobre planes, "
                "facturas, pagos, servicios y soporte técnico.\n\n"
                "¿En qué puedo ayudarte?"
            ),
            "intencion": intencion,
            "requiere_tecnico": False,
            "datos": {
                "cliente_identificado": False,
            },
        }

    # =====================================================
    # FACTURAS
    # =====================================================

    if intencion == "facturas":

        facturas = obtener_facturas_cliente(
            session,
            empresa_id,
            cliente.id,
        )

        pendientes = [
            factura
            for factura in facturas
            if factura.estado.lower() == "pendiente"
        ]

        nombre = obtener_nombre_cliente(cliente)

        if not pendientes:

            return {
                "respuesta": (
                    f"Hola, {nombre}. 😊 "
                    "No encontré facturas pendientes actualmente."
                ),
                "intencion": intencion,
                "requiere_tecnico": False,
                "datos": {
                    "facturas_pendientes": 0,
                },
            }

        total_deuda = sum(
            factura.total
            for factura in pendientes
        )

        detalles = []

        for factura in pendientes:

            detalles.append({
                "id": str(factura.id),
                "numero": factura.numero,
                "total": factura.total,
                "fecha_vencimiento": (
                    factura.fecha_vencimiento.isoformat()
                    if factura.fecha_vencimiento
                    else None
                ),
            })

        return {
            "respuesta": (
                f"Hola, {nombre}. Encontré "
                f"{len(pendientes)} factura(s) pendiente(s) "
                f"por un total de ${total_deuda:,.0f}."
            ),
            "intencion": intencion,
            "requiere_tecnico": False,
            "datos": {
                "facturas_pendientes": len(pendientes),
                "total_deuda": total_deuda,
                "facturas": detalles,
            },
        }

    # =====================================================
    # PAGOS
    # =====================================================

    if intencion == "pagos":

        pagos = obtener_pagos_cliente(
            session,
            empresa_id,
            cliente.id,
        )

        if not pagos:

            return {
                "respuesta": (
                    "No encontré pagos registrados en tu cuenta."
                ),
                "intencion": intencion,
                "requiere_tecnico": False,
                "datos": {},
            }

        ultimo_pago = max(
            pagos,
            key=lambda pago: pago.fecha_pago,
        )

        return {
            "respuesta": (
                f"El último pago registrado es de "
                f"${ultimo_pago.monto:,.0f}, "
                f"realizado mediante {ultimo_pago.metodo_pago}."
            ),
            "intencion": intencion,
            "requiere_tecnico": False,
            "datos": {
                "ultimo_pago": {
                    "monto": ultimo_pago.monto,
                    "fecha_pago": ultimo_pago.fecha_pago.isoformat(),
                    "metodo_pago": ultimo_pago.metodo_pago,
                    "estado": ultimo_pago.estado,
                }
            },
        }

    # =====================================================
    # SERVICIO
    # =====================================================

    if intencion == "servicio":

        servicios = obtener_servicios_cliente(
            session,
            empresa_id,
            cliente.id,
        )

        if not servicios:

            return {
                "respuesta": (
                    "No encontré servicios asociados a tu cuenta."
                ),
                "intencion": intencion,
                "requiere_tecnico": False,
                "datos": {},
            }

        servicio = servicios[0]

        if servicio.suspendido:

            return {
                "respuesta": (
                    "Tu servicio aparece suspendido actualmente. "
                    "Podemos revisar la causa de la suspensión."
                ),
                "intencion": intencion,
                "requiere_tecnico": False,
                "datos": {
                    "estado": servicio.estado,
                    "suspendido": servicio.suspendido,
                    "motivo_suspension": servicio.motivo_suspension,
                },
            }

        return {
            "respuesta": (
                "Tu servicio aparece registrado como activo. "
                "Si actualmente tienes problemas de conexión, "
                "puedo ayudarte a solicitar soporte técnico."
            ),
            "intencion": intencion,
            "requiere_tecnico": False,
            "datos": {
                "estado": servicio.estado,
                "suspendido": servicio.suspendido,
                "tipo": servicio.tipo,
            },
        }

    # =====================================================
    # SOPORTE TÉCNICO
    # =====================================================

    if intencion == "soporte":
    
        conversacion.esperando_descripcion_soporte = True

        guardar_conversacion(session, conversacion)

        return {
            "respuesta": (
                "Entiendo que necesitas soporte técnico. 🔧\n\n"
                "Cuéntame brevemente cuál es el problema que "
                "presentas para ayudarte."
            ),
            "intencion": intencion,
            "requiere_tecnico": True,
            "datos": {
                "cliente_identificado": True,
                "cliente_id": str(cliente.id),
            },
        }

    # =====================================================
    # INFORMACIÓN GENERAL
    # =====================================================

    if intencion == "informacion":

        return {
            "respuesta": (
                "En OPTIRÁPIDO ofrecemos servicios de conectividad "
                "a internet. 🌐\n\n"
                "Puedo ayudarte con información sobre nuestros "
                "servicios, facturas, pagos y soporte técnico.\n\n"
                "Cuéntame qué necesitas."
            ),
            "intencion": intencion,
            "requiere_tecnico": False,
            "datos": {},
        }

    # =====================================================
    # RESPUESTA GENERAL
    # =====================================================

    return {
        "respuesta": (
            "Estoy aquí para ayudarte. 😊\n\n"
            "Puedes preguntarme sobre nuestros servicios, "
            "consultar facturas, pagos o solicitar soporte técnico."
        ),
        "intencion": "general",
        "requiere_tecnico": False,
        "datos": {},
    }


