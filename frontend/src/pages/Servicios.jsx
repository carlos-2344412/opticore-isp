import { useEffect, useState } from "react";

const API_URL = "http://127.0.0.1:8001";

const formularioInicial = {
  cliente_id: "",
  plan_id: "",
  tipo: "internet",
  usuario_pppoe: "",
  fecha_instalacion: "",
  fecha_vencimiento: "",
};

function Servicios() {
  const [servicios, setServicios] = useState([]);
  const [clientes, setClientes] = useState([]);
  const [planes, setPlanes] = useState([]);

  const [cargando, setCargando] = useState(true);
  const [error, setError] = useState("");
  const [busqueda, setBusqueda] = useState("");

  const [mostrarFormulario, setMostrarFormulario] =
    useState(false);

  const [modoEdicion, setModoEdicion] =
    useState(false);

  const [mostrarDetalle, setMostrarDetalle] =
    useState(false);

  const [servicioSeleccionado, setServicioSeleccionado] =
    useState(null);

  const [guardando, setGuardando] =
    useState(false);

  const [mostrarSuspension, setMostrarSuspension] =
    useState(false);

  const [motivoSuspension, setMotivoSuspension] =
    useState("");

  const [formulario, setFormulario] =
    useState(formularioInicial);

  const obtenerHeaders = () => {
    const token =
      localStorage.getItem("access_token");

    return {
      Authorization: `Bearer ${token}`,
      Accept: "application/json",
    };
  };

  const cargarDatos = async () => {
    try {
      setCargando(true);
      setError("");

      const headers = obtenerHeaders();

      const [
        serviciosRes,
        clientesRes,
        planesRes,
      ] = await Promise.all([
        fetch(`${API_URL}/servicios`, {
          headers,
        }),

        fetch(`${API_URL}/clientes`, {
          headers,
        }),

        fetch(`${API_URL}/planes`, {
          headers,
        }),
      ]);

      const serviciosData =
        await serviciosRes.json();

      const clientesData =
        await clientesRes.json();

      const planesData =
        await planesRes.json();

      if (!serviciosRes.ok) {
        throw new Error(
          serviciosData.detail ||
            "No se pudieron cargar los servicios"
        );
      }

      if (!clientesRes.ok) {
        throw new Error(
          clientesData.detail ||
            "No se pudieron cargar los clientes"
        );
      }

      if (!planesRes.ok) {
        throw new Error(
          planesData.detail ||
            "No se pudieron cargar los planes"
        );
      }

      setServicios(serviciosData);
      setClientes(clientesData);
      setPlanes(planesData);

    } catch (error) {
      console.error(error);
      setError(error.message);

    } finally {
      setCargando(false);
    }
  };

  useEffect(() => {
    cargarDatos();
  }, []);

  const cambiarCampo = (e) => {
    const { name, value } = e.target;

    setFormulario((anterior) => ({
      ...anterior,
      [name]: value,
    }));
  };

  const abrirNuevoServicio = () => {
    setFormulario(formularioInicial);
    setModoEdicion(false);
    setServicioSeleccionado(null);
    setMostrarDetalle(false);
    setMostrarFormulario(true);
    setError("");
  };

  const abrirEditar = (servicio) => {
    setFormulario({
      cliente_id: servicio.cliente_id || "",
      plan_id: servicio.plan_id || "",
      tipo: servicio.tipo || "internet",
      usuario_pppoe:
        servicio.usuario_pppoe || "",
      fecha_instalacion:
        servicio.fecha_instalacion || "",
      fecha_vencimiento:
        servicio.fecha_vencimiento || "",
    });

    setServicioSeleccionado(servicio);
    setModoEdicion(true);
    setMostrarDetalle(false);
    setMostrarFormulario(true);
    setError("");
  };

  const abrirDetalle = (servicio) => {
    setServicioSeleccionado(servicio);
    setMostrarFormulario(false);
    setMostrarDetalle(true);
    setError("");
  };

  const cerrarVentana = () => {
    setMostrarFormulario(false);
    setMostrarDetalle(false);
    setModoEdicion(false);
    setServicioSeleccionado(null);
    setError("");
  };

  const obtenerCliente = (clienteId) => {
    return clientes.find(
      (cliente) => cliente.id === clienteId
    );
  };

  const obtenerPlan = (planId) => {
    return planes.find(
      (plan) => plan.id === planId
    );
  };

  const nombreCliente = (clienteId) => {
    const cliente =
      obtenerCliente(clienteId);

    if (!cliente) {
      return "Cliente desconocido";
    }

    return `${cliente.nombre} ${
      cliente.apellido || ""
    }`.trim();
  };

  const crearServicio = async (e) => {
    e.preventDefault();

    try {
      setGuardando(true);
      setError("");

      const respuesta = await fetch(
        `${API_URL}/servicios`,
        {
          method: "POST",

          headers: {
            ...obtenerHeaders(),
            "Content-Type":
              "application/json",
          },

          body: JSON.stringify({
            cliente_id:
              formulario.cliente_id,

            plan_id:
              formulario.plan_id,

            tipo:
              formulario.tipo,

            usuario_pppoe:
              formulario.usuario_pppoe ||
              null,

            fecha_instalacion:
              formulario.fecha_instalacion ||
              null,

            fecha_vencimiento:
              formulario.fecha_vencimiento ||
              null,
          }),
        }
      );

      const resultado =
        await respuesta.json();

      if (!respuesta.ok) {
        throw new Error(
          resultado.detail ||
            "No se pudo crear el servicio"
        );
      }

      cerrarVentana();

      await cargarDatos();

    } catch (error) {
      console.error(error);
      setError(error.message);

    } finally {
      setGuardando(false);
    }
  };

  const actualizarServicio = async (e) => {
    e.preventDefault();

    if (!servicioSeleccionado) {
      return;
    }

    try {
      setGuardando(true);
      setError("");

      const respuesta = await fetch(
        `${API_URL}/servicios/${servicioSeleccionado.id}`,
        {
          method: "PUT",

          headers: {
            ...obtenerHeaders(),
            "Content-Type":
              "application/json",
          },

          body: JSON.stringify({
            cliente_id:
              formulario.cliente_id,

            plan_id:
              formulario.plan_id,

            tipo:
              formulario.tipo,

            usuario_pppoe:
              formulario.usuario_pppoe ||
              null,

            fecha_instalacion:
              formulario.fecha_instalacion ||
              null,

            fecha_vencimiento:
              formulario.fecha_vencimiento ||
              null,
          }),
        }
      );

      const resultado =
        await respuesta.json();

      if (!respuesta.ok) {
        throw new Error(
          resultado.detail ||
            "No se pudo actualizar el servicio"
        );
      }

      cerrarVentana();

      await cargarDatos();

    } catch (error) {
      console.error(error);
      setError(error.message);

    } finally {
      setGuardando(false);
    }
  };

const suspenderServicio = async () => {
  if (!servicioSeleccionado) {
    return;
  }

  if (!motivoSuspension.trim()) {
    setError(
      "Debes indicar el motivo de la suspensión"
    );
    return;
  }

  try {
    setGuardando(true);
    setError("");

    const respuesta = await fetch(
      `${API_URL}/servicios/${servicioSeleccionado.id}`,
      {
        method: "DELETE",

        headers: {
          ...obtenerHeaders(),
          Accept: "application/json",
        },
      }
    );

    const resultado =
      await respuesta.json();

    if (!respuesta.ok) {
      throw new Error(
        resultado.detail ||
          "No se pudo suspender el servicio"
      );
    }

    setMostrarSuspension(false);
    setMotivoSuspension("");

    setMostrarDetalle(false);
    setServicioSeleccionado(null);

    await cargarDatos();

  } catch (error) {
    console.error(error);
    setError(error.message);

  } finally {
    setGuardando(false);
  }
};

const reactivarServicio = async (servicio) => {
  try {
    setGuardando(true);
    setError("");

    const respuesta = await fetch(
      `${API_URL}/servicios/${servicio.id}`,
      {
        method: "PUT",

        headers: {
          ...obtenerHeaders(),
          "Content-Type": "application/json",
          Accept: "application/json",
        },

        body: JSON.stringify({
          plan_id: servicio.plan_id,
          tipo: servicio.tipo,
          usuario_pppoe: servicio.usuario_pppoe,
          estado: "activo",
          fecha_instalacion:
            servicio.fecha_instalacion,
          fecha_vencimiento:
            servicio.fecha_vencimiento,
          suspendido: false,
          motivo_suspension: null,
        }),
      }
    );

    const resultado =
      await respuesta.json();

    if (!respuesta.ok) {
      throw new Error(
        resultado.detail ||
          "No se pudo reactivar el servicio"
      );
    }

    await cargarDatos();

  } catch (error) {
    console.error(error);
    setError(error.message);

  } finally {
    setGuardando(false);
  }
};

  const serviciosFiltrados =
    servicios.filter((servicio) => {
      const cliente =
        obtenerCliente(servicio.cliente_id);

      const texto =
        busqueda.toLowerCase();

      const nombre =
        cliente
          ? `${cliente.nombre} ${
              cliente.apellido || ""
            }`.toLowerCase()
          : "";

      const documento =
        cliente?.documento
          ?.toLowerCase() || "";

      const usuario =
        servicio.usuario_pppoe
          ?.toLowerCase() || "";

      return (
        nombre.includes(texto) ||
        documento.includes(texto) ||
        usuario.includes(texto)
      );
    });

  return (
    <div className="clientes-page">

      <div className="page-header">

        <div>
          <h1>Servicios</h1>

          <p>
            Administra los servicios de
            Internet de OPTIRÁPIDO
          </p>
        </div>

        <button
          className="primary-button"
          onClick={abrirNuevoServicio}
        >
          + Nuevo servicio
        </button>

      </div>

      {mostrarFormulario && (
        <div className="form-card">

          <div className="form-card-header">

            <div>
              <h2>
                {modoEdicion
                  ? "Editar servicio"
                  : "Nuevo servicio"}
              </h2>

              <p>
                {modoEdicion
                  ? "Modifica la información del servicio"
                  : "Asigna un servicio de Internet a un cliente"}
              </p>
            </div>

            <button
              className="close-button"
              onClick={cerrarVentana}
            >
              ✕
            </button>

          </div>

          <form
            onSubmit={
              modoEdicion
                ? actualizarServicio
                : crearServicio
            }
            className="cliente-form"
          >

            <div className="form-grid">

              <div className="form-group">
                <label>
                  Cliente *
                </label>

                <select
                  name="cliente_id"
                  value={formulario.cliente_id}
                  onChange={cambiarCampo}
                  required
                >
                  <option value="">
                    Selecciona un cliente
                  </option>

                  {clientes.map(
                    (cliente) => (
                      <option
                        key={cliente.id}
                        value={cliente.id}
                      >
                        {cliente.nombre}{" "}
                        {cliente.apellido || ""}
                        {cliente.documento
                          ? ` - ${cliente.documento}`
                          : ""}
                      </option>
                    )
                  )}

                </select>
              </div>

              <div className="form-group">
                <label>
                  Plan *
                </label>

                <select
                  name="plan_id"
                  value={formulario.plan_id}
                  onChange={cambiarCampo}
                  required
                >
                  <option value="">
                    Selecciona un plan
                  </option>

                  {planes.map(
                    (plan) => (
                      <option
                        key={plan.id}
                        value={plan.id}
                      >
                        {plan.nombre} -{" "}
                        {plan.velocidad_bajada}
                        /
                        {plan.velocidad_subida}
                        Mbps
                      </option>
                    )
                  )}

                </select>
              </div>

              <div className="form-group">
                <label>
                  Tipo de servicio *
                </label>

                <select
                  name="tipo"
                  value={formulario.tipo}
                  onChange={cambiarCampo}
                  required
                >
                  <option value="internet">
                    Internet
                  </option>

                  <option value="fibra">
                    Fibra óptica
                  </option>
                </select>
              </div>

              <div className="form-group">
                <label>
                  Usuario PPPoE
                </label>

                <input
                  type="text"
                  name="usuario_pppoe"
                  value={
                    formulario.usuario_pppoe
                  }
                  onChange={cambiarCampo}
                  placeholder="Ej: carlos.trillos"
                />
              </div>

              <div className="form-group">
                <label>
                  Fecha de instalación
                </label>

                <input
                  type="date"
                  name="fecha_instalacion"
                  value={
                    formulario.fecha_instalacion
                  }
                  onChange={cambiarCampo}
                />
              </div>

              <div className="form-group">
                <label>
                  Fecha de vencimiento
                </label>

                <input
                  type="date"
                  name="fecha_vencimiento"
                  value={
                    formulario.fecha_vencimiento
                  }
                  onChange={cambiarCampo}
                />
              </div>

            </div>

            {error && (
              <div className="error-message">
                {error}
              </div>
            )}

            <div className="form-actions">

              <button
                type="button"
                className="secondary-button"
                onClick={cerrarVentana}
              >
                Cancelar
              </button>

              <button
                type="submit"
                className="primary-button"
                disabled={guardando}
              >
                {guardando
                  ? "Guardando..."
                  : modoEdicion
                  ? "Guardar cambios"
                  : "Crear servicio"}
              </button>

            </div>

          </form>

        </div>
      )}

{mostrarSuspension &&
  servicioSeleccionado && (
    <div className="form-card">

      <div className="form-card-header">

        <div>
          <h2>Suspender servicio</h2>

          <p>
            Servicio de{" "}
            {nombreCliente(
              servicioSeleccionado.cliente_id
            )}
          </p>
        </div>

        <button
          className="close-button"
          onClick={() => {
            setMostrarSuspension(false);
            setMotivoSuspension("");
            setError("");
          }}
        >
          ✕
        </button>

      </div>

      <div className="form-group">

        <label>
          Motivo de suspensión *
        </label>

        <textarea
          value={motivoSuspension}
          onChange={(e) =>
            setMotivoSuspension(
              e.target.value
            )
          }
          placeholder="Ej: Falta de pago"
          rows="4"
        />

      </div>

      {error && (
        <div className="error-message">
          {error}
        </div>
      )}

      <div className="form-actions">

        <button
          type="button"
          className="secondary-button"
          onClick={() => {
            setMostrarSuspension(false);
            setMotivoSuspension("");
            setError("");
          }}
        >
          Cancelar
        </button>

        <button
          type="button"
          className="primary-button"
          onClick={suspenderServicio}
          disabled={guardando}
        >
          {guardando
            ? "Suspendiendo..."
            : "Suspender servicio"}
        </button>

      </div>

    </div>
  )}

      {mostrarDetalle &&
        servicioSeleccionado && (
          <div className="form-card">

            <div className="form-card-header">

              <div>
                <h2>
                  Servicio de{" "}
                  {nombreCliente(
                    servicioSeleccionado.cliente_id
                  )}
                </h2>

                <p>
                  Información del servicio
                </p>
              </div>

              <button
                className="close-button"
                onClick={cerrarVentana}
              >
                ✕
              </button>

            </div>

            <div className="form-grid">

              <div className="form-group">
                <label>
                  Cliente
                </label>

                <input
                  value={nombreCliente(
                    servicioSeleccionado.cliente_id
                  )}
                  readOnly
                />
              </div>

              <div className="form-group">
                <label>
                  Plan
                </label>

                <input
                  value={
                    obtenerPlan(
                      servicioSeleccionado.plan_id
                    )?.nombre ||
                    "Plan desconocido"
                  }
                  readOnly
                />
              </div>

              <div className="form-group">
                <label>
                  Usuario PPPoE
                </label>

                <input
                  value={
                    servicioSeleccionado
                      .usuario_pppoe ||
                    "-"
                  }
                  readOnly
                />
              </div>

              <div className="form-group">
                <label>
                  Tipo
                </label>

                <input
                  value={
                    servicioSeleccionado.tipo ||
                    "-"
                  }
                  readOnly
                />
              </div>

              <div className="form-group">
                <label>
                  Fecha instalación
                </label>

                <input
                  value={
                    servicioSeleccionado
                      .fecha_instalacion ||
                    "-"
                  }
                  readOnly
                />
              </div>

              <div className="form-group">
                <label>
                  Fecha vencimiento
                </label>

                <input
                  value={
                    servicioSeleccionado
                      .fecha_vencimiento ||
                    "-"
                  }
                  readOnly
                />
              </div>

              <div className="form-group">
                <label>
                  Estado
                </label>

                <input
                  value={
                    servicioSeleccionado
                      .estado || "-"
                  }
                  readOnly
                />
              </div>

              <div className="form-group">
                <label>
                  Suspendido
                </label>

                <input
                  value={
                    servicioSeleccionado
                      .suspendido
                      ? "Sí"
                      : "No"
                  }
                  readOnly
                />
              </div>

            </div>

            <div className="form-actions">

              <button
                className="secondary-button"
                onClick={cerrarVentana}
              >
                Cerrar
              </button>

              <button
                className="primary-button"
                onClick={() =>
                  abrirEditar(
                    servicioSeleccionado
                  )
                }
              >
                Editar servicio
              </button>

            </div>

          </div>
        )}

      {!mostrarFormulario &&
        !mostrarDetalle && (
          <>
            <div className="clientes-toolbar">

              <input
                type="text"
                placeholder="Buscar por cliente, documento o usuario PPPoE..."
                value={busqueda}
                onChange={(e) =>
                  setBusqueda(e.target.value)
                }
              />

              <div className="clientes-count">
                {serviciosFiltrados.length} servicios
              </div>

            </div>

            {cargando && (
              <div className="loading">
                Cargando servicios...
              </div>
            )}

            {error && (
              <div className="error-message">
                {error}
              </div>
            )}

            {!cargando &&
              !error && (
                <div className="table-card">

                  <table>

                    <thead>
                      <tr>
                        <th>Cliente</th>
                        <th>Plan</th>
                        <th>PPPoE</th>
                        <th>Vencimiento</th>
                        <th>Estado</th>
                        <th>Acciones</th>
                      </tr>
                    </thead>

                    <tbody>

                      {serviciosFiltrados.map(
                        (servicio) => {
                          const plan =
                            obtenerPlan(
                              servicio.plan_id
                            );

                          return (
                            <tr
                              key={
                                servicio.id
                              }
                            >

                              <td>
                                <div className="cliente-name">

                                  <strong>
                                    {nombreCliente(
                                      servicio.cliente_id
                                    )}
                                  </strong>

                                  <span>
                                    {
                                      obtenerCliente(
                                        servicio.cliente_id
                                      )?.documento ||
                                      "Sin documento"
                                    }
                                  </span>

                                </div>
                              </td>

                              <td>
                                <strong>
                                  {plan?.nombre ||
                                    "Plan desconocido"}
                                </strong>

                                {plan && (
                                  <span
                                    style={{
                                      display:
                                        "block",
                                      fontSize:
                                        "12px",
                                      color:
                                        "#777",
                                    }}
                                  >
                                    {
                                      plan.velocidad_bajada
                                    }{" "}
                                    /{" "}
                                    {
                                      plan.velocidad_subida
                                    }{" "}
                                    Mbps
                                  </span>
                                )}
                              </td>

                              <td>
                                {servicio.usuario_pppoe ||
                                  "-"}
                              </td>

                              <td>
                                {servicio.fecha_vencimiento ||
                                  "-"}
                              </td>

                              <td>
                                <span
                                  className={
                                    servicio.estado ===
                                      "activo" &&
                                    !servicio.suspendido
                                      ? "status active"
                                      : "status inactive"
                                  }
                                >
                                  {servicio.suspendido
                                    ? "Suspendido"
                                    : servicio.estado}
                                </span>
                              </td>

                              <td>

                                <button
                                  className="action-button"
                                  onClick={() =>
                                    abrirDetalle(servicio)
                                  }
                                >
                                  Ver
                                </button>

                                <button
                                  className="action-button"
                                  onClick={() =>
                                    abrirEditar(servicio)
                                  }
                                >
                                  Editar
                                </button>

                                {servicio.suspendido ? (
                                  <button
                                    className="action-button"
                                    onClick={() =>
                                      reactivarServicio(
                                        servicio
                                      )
                                    }
                                    disabled={guardando}
                                  >
                                    Reactivar
                                  </button>
                                ) : (
                                  <button
                                    className="action-button"
                                    onClick={() => {
                                      setServicioSeleccionado(
                                        servicio
                                      );

                                      setMostrarSuspension(
                                        true
                                      );

                                      setError("");
                                    }}
                                  >
                                    Suspender
                                  </button>
                                )}

                              </td>

                            </tr>
                          );
                        }
                      )}

                    </tbody>

                  </table>

                  {serviciosFiltrados.length ===
                    0 && (
                    <div className="empty-state">
                      No se encontraron servicios.
                    </div>
                  )}

                </div>
              )}

          </>
        )}

    </div>
  );
}

export default Servicios;