import { useEffect, useState } from "react";

const API_URL = "http://127.0.0.1:8001";

const formularioInicial = {
  documento: "",
  nombre: "",
  apellido: "",
  telefono: "",
  correo: "",
  direccion: "",
  ciudad: "",
  barrio: "",
  referencia_direccion: "",
};

function Clientes() {
  const [clientes, setClientes] = useState([]);
  const [cargando, setCargando] = useState(true);
  const [error, setError] = useState("");
  const [busqueda, setBusqueda] = useState("");

  const [mostrarFormulario, setMostrarFormulario] =
    useState(false);

  const [modoEdicion, setModoEdicion] =
    useState(false);

  const [mostrarDetalle, setMostrarDetalle] =
    useState(false);

  const [clienteSeleccionado, setClienteSeleccionado] =
    useState(null);

  const [guardando, setGuardando] =
    useState(false);

  const [formulario, setFormulario] =
    useState(formularioInicial);

  const cargarClientes = async () => {
    try {
      setCargando(true);
      setError("");

      const token =
        localStorage.getItem("access_token");

      const respuesta = await fetch(
        `${API_URL}/clientes`,
        {
          headers: {
            Authorization: `Bearer ${token}`,
            Accept: "application/json",
          },
        }
      );

      const resultado = await respuesta.json();

      if (!respuesta.ok) {
        throw new Error(
          resultado.detail ||
            "No se pudieron cargar los clientes"
        );
      }

      setClientes(resultado);

    } catch (error) {
      console.error(error);
      setError(error.message);

    } finally {
      setCargando(false);
    }
  };

  useEffect(() => {
    cargarClientes();
  }, []);

  const cambiarCampo = (e) => {
    const { name, value } = e.target;

    setFormulario((anterior) => ({
      ...anterior,
      [name]: value,
    }));
  };

  const abrirNuevoCliente = () => {
    setFormulario(formularioInicial);
    setModoEdicion(false);
    setClienteSeleccionado(null);
    setMostrarDetalle(false);
    setMostrarFormulario(true);
    setError("");
  };

  const abrirEditar = (cliente) => {
    setFormulario({
      documento: cliente.documento || "",
      nombre: cliente.nombre || "",
      apellido: cliente.apellido || "",
      telefono: cliente.telefono || "",
      correo: cliente.correo || "",
      direccion: cliente.direccion || "",
      ciudad: cliente.ciudad || "",
      barrio: cliente.barrio || "",
      referencia_direccion:
        cliente.referencia_direccion || "",
    });

    setClienteSeleccionado(cliente);
    setModoEdicion(true);
    setMostrarDetalle(false);
    setMostrarFormulario(true);
    setError("");
  };

  const abrirDetalle = (cliente) => {
    setClienteSeleccionado(cliente);
    setMostrarFormulario(false);
    setMostrarDetalle(true);
    setError("");
  };

  const cerrarVentana = () => {
    setMostrarFormulario(false);
    setMostrarDetalle(false);
    setModoEdicion(false);
    setClienteSeleccionado(null);
    setError("");
  };

  const crearCliente = async (e) => {
    e.preventDefault();

    try {
      setGuardando(true);
      setError("");

      const token =
        localStorage.getItem("access_token");

      const respuesta = await fetch(
        `${API_URL}/clientes`,
        {
          method: "POST",

          headers: {
            Authorization: `Bearer ${token}`,
            Accept: "application/json",
            "Content-Type": "application/json",
          },

          body: JSON.stringify(formulario),
        }
      );

      const resultado = await respuesta.json();

      if (!respuesta.ok) {
        throw new Error(
          resultado.detail ||
            "No se pudo crear el cliente"
        );
      }

      cerrarVentana();

      await cargarClientes();

    } catch (error) {
      console.error(error);
      setError(error.message);

    } finally {
      setGuardando(false);
    }
  };

  const actualizarCliente = async (e) => {
    e.preventDefault();

    if (!clienteSeleccionado) {
      return;
    }

    try {
      setGuardando(true);
      setError("");

      const token =
        localStorage.getItem("access_token");

      const respuesta = await fetch(
        `${API_URL}/clientes/${clienteSeleccionado.id}`,
        {
          method: "PUT",

          headers: {
            Authorization: `Bearer ${token}`,
            Accept: "application/json",
            "Content-Type": "application/json",
          },

          body: JSON.stringify(formulario),
        }
      );

      const resultado = await respuesta.json();

      if (!respuesta.ok) {
        throw new Error(
          resultado.detail ||
            "No se pudo actualizar el cliente"
        );
      }

      cerrarVentana();

      await cargarClientes();

    } catch (error) {
      console.error(error);
      setError(error.message);

    } finally {
      setGuardando(false);
    }
  };

  const clientesFiltrados = clientes.filter(
    (cliente) => {
      const texto =
        busqueda.toLowerCase();

      return (
        cliente.nombre
          ?.toLowerCase()
          .includes(texto) ||

        cliente.apellido
          ?.toLowerCase()
          .includes(texto) ||

        cliente.documento
          ?.toLowerCase()
          .includes(texto) ||

        cliente.telefono
          ?.toLowerCase()
          .includes(texto)
      );
    }
  );

  return (
    <div className="clientes-page">

      <div className="page-header">

        <div>
          <h1>Clientes</h1>

          <p>
            Administra los clientes de OPTIRÁPIDO
          </p>
        </div>

        <button
          className="primary-button"
          onClick={abrirNuevoCliente}
        >
          + Nuevo cliente
        </button>

      </div>

      {/* FORMULARIO */}

      {mostrarFormulario && (
        <div className="form-card">

          <div className="form-card-header">

            <div>
              <h2>
                {modoEdicion
                  ? "Editar cliente"
                  : "Nuevo cliente"}
              </h2>

              <p>
                {modoEdicion
                  ? "Modifica los datos del cliente"
                  : "Registra un nuevo cliente en OPTIRÁPIDO"}
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
                ? actualizarCliente
                : crearCliente
            }
            className="cliente-form"
          >

            <div className="form-grid">

              <div className="form-group">
                <label>Documento</label>

                <input
                  type="text"
                  name="documento"
                  value={formulario.documento}
                  onChange={cambiarCampo}
                  placeholder="Ej: 1044001784"
                />
              </div>

              <div className="form-group">
                <label>Nombre *</label>

                <input
                  type="text"
                  name="nombre"
                  value={formulario.nombre}
                  onChange={cambiarCampo}
                  required
                />
              </div>

              <div className="form-group">
                <label>Apellido</label>

                <input
                  type="text"
                  name="apellido"
                  value={formulario.apellido}
                  onChange={cambiarCampo}
                />
              </div>

              <div className="form-group">
                <label>Teléfono *</label>

                <input
                  type="text"
                  name="telefono"
                  value={formulario.telefono}
                  onChange={cambiarCampo}
                  required
                />
              </div>

              <div className="form-group">
                <label>Correo electrónico</label>

                <input
                  type="email"
                  name="correo"
                  value={formulario.correo}
                  onChange={cambiarCampo}
                />
              </div>

              <div className="form-group">
                <label>Ciudad</label>

                <input
                  type="text"
                  name="ciudad"
                  value={formulario.ciudad}
                  onChange={cambiarCampo}
                />
              </div>

              <div className="form-group">
                <label>Barrio</label>

                <input
                  type="text"
                  name="barrio"
                  value={formulario.barrio}
                  onChange={cambiarCampo}
                />
              </div>

              <div className="form-group full-width">
                <label>Dirección *</label>

                <input
                  type="text"
                  name="direccion"
                  value={formulario.direccion}
                  onChange={cambiarCampo}
                  required
                />
              </div>

              <div className="form-group full-width">
                <label>
                  Referencia de dirección
                </label>

                <textarea
                  name="referencia_direccion"
                  value={
                    formulario.referencia_direccion
                  }
                  onChange={cambiarCampo}
                  rows="3"
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
                  : "Guardar cliente"}
              </button>

            </div>

          </form>

        </div>
      )}

      {/* DETALLE DEL CLIENTE */}

      {mostrarDetalle &&
        clienteSeleccionado && (
          <div className="form-card">

            <div className="form-card-header">

              <div>
                <h2>
                  {clienteSeleccionado.nombre}{" "}
                  {clienteSeleccionado.apellido || ""}
                </h2>

                <p>
                  Información del cliente
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
                <label>Documento</label>

                <input
                  value={
                    clienteSeleccionado.documento ||
                    "-"
                  }
                  readOnly
                />
              </div>

              <div className="form-group">
                <label>Teléfono</label>

                <input
                  value={
                    clienteSeleccionado.telefono ||
                    "-"
                  }
                  readOnly
                />
              </div>

              <div className="form-group">
                <label>Correo</label>

                <input
                  value={
                    clienteSeleccionado.correo ||
                    "-"
                  }
                  readOnly
                />
              </div>

              <div className="form-group">
                <label>Ciudad</label>

                <input
                  value={
                    clienteSeleccionado.ciudad ||
                    "-"
                  }
                  readOnly
                />
              </div>

              <div className="form-group">
                <label>Barrio</label>

                <input
                  value={
                    clienteSeleccionado.barrio ||
                    "-"
                  }
                  readOnly
                />
              </div>

              <div className="form-group">
                <label>Estado</label>

                <input
                  value={
                    clienteSeleccionado.estado ||
                    "-"
                  }
                  readOnly
                />
              </div>

              <div className="form-group full-width">
                <label>Dirección</label>

                <input
                  value={
                    clienteSeleccionado.direccion ||
                    "-"
                  }
                  readOnly
                />
              </div>

              <div className="form-group full-width">
                <label>
                  Referencia
                </label>

                <textarea
                  value={
                    clienteSeleccionado
                      .referencia_direccion ||
                    "-"
                  }
                  readOnly
                  rows="3"
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
                    clienteSeleccionado
                  )
                }
              >
                Editar cliente
              </button>

            </div>

          </div>
        )}

      {/* TABLA */}

      {!mostrarFormulario &&
        !mostrarDetalle && (
          <>
            <div className="clientes-toolbar">

              <input
                type="text"
                placeholder="Buscar por nombre, documento o teléfono..."
                value={busqueda}
                onChange={(e) =>
                  setBusqueda(e.target.value)
                }
              />

              <div className="clientes-count">
                {clientesFiltrados.length} clientes
              </div>

            </div>

            {cargando && (
              <div className="loading">
                Cargando clientes...
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
                        <th>Documento</th>
                        <th>Teléfono</th>
                        <th>Ciudad</th>
                        <th>Estado</th>
                        <th>Acciones</th>
                      </tr>
                    </thead>

                    <tbody>

                      {clientesFiltrados.map(
                        (cliente) => (
                          <tr key={cliente.id}>

                            <td>
                              <div className="cliente-name">

                                <strong>
                                  {cliente.nombre}{" "}
                                  {cliente.apellido ||
                                    ""}
                                </strong>

                                <span>
                                  {cliente.correo ||
                                    "Sin correo"}
                                </span>

                              </div>
                            </td>

                            <td>
                              {cliente.documento ||
                                "-"}
                            </td>

                            <td>
                              {cliente.telefono}
                            </td>

                            <td>
                              {cliente.ciudad ||
                                "-"}
                            </td>

                            <td>
                              <span
                                className={
                                  cliente.estado ===
                                  "activo"
                                    ? "status active"
                                    : "status inactive"
                                }
                              >
                                {cliente.estado}
                              </span>
                            </td>

                            <td>

                              <button
                                className="action-button"
                                onClick={() =>
                                  abrirDetalle(
                                    cliente
                                  )
                                }
                              >
                                Ver
                              </button>

                              <button
                                className="action-button"
                                onClick={() =>
                                  abrirEditar(
                                    cliente
                                  )
                                }
                              >
                                Editar
                              </button>

                            </td>

                          </tr>
                        )
                      )}

                    </tbody>

                  </table>

                  {clientesFiltrados.length ===
                    0 && (
                    <div className="empty-state">
                      No se encontraron clientes.
                    </div>
                  )}

                </div>
              )}

          </>
        )}

    </div>
  );
}

export default Clientes;