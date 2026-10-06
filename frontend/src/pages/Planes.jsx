import { useEffect, useState } from "react";

const API_URL = "http://127.0.0.1:8001";

const formularioInicial = {
  nombre: "",
  velocidad_bajada: "",
  velocidad_subida: "",
  precio_mensual: "",
  descripcion: "",
};

function Planes() {
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

  const [planSeleccionado, setPlanSeleccionado] =
    useState(null);

  const [guardando, setGuardando] =
    useState(false);

  const [formulario, setFormulario] =
    useState(formularioInicial);

  const cargarPlanes = async () => {
    try {
      setCargando(true);
      setError("");

      const token =
        localStorage.getItem("access_token");

      const respuesta = await fetch(
        `${API_URL}/planes`,
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
            "No se pudieron cargar los planes"
        );
      }

      setPlanes(resultado);

    } catch (error) {
      console.error(error);
      setError(error.message);

    } finally {
      setCargando(false);
    }
  };

  useEffect(() => {
    cargarPlanes();
  }, []);

  const cambiarCampo = (e) => {
    const { name, value } = e.target;

    setFormulario((anterior) => ({
      ...anterior,
      [name]: value,
    }));
  };

  const abrirNuevoPlan = () => {
    setFormulario(formularioInicial);
    setModoEdicion(false);
    setPlanSeleccionado(null);
    setMostrarDetalle(false);
    setMostrarFormulario(true);
    setError("");
  };

  const abrirEditar = (plan) => {
    setFormulario({
      nombre: plan.nombre || "",
      velocidad_bajada:
        plan.velocidad_bajada || "",
      velocidad_subida:
        plan.velocidad_subida || "",
      precio_mensual:
        plan.precio_mensual || "",
      descripcion:
        plan.descripcion || "",
    });

    setPlanSeleccionado(plan);
    setModoEdicion(true);
    setMostrarDetalle(false);
    setMostrarFormulario(true);
    setError("");
  };

  const abrirDetalle = (plan) => {
    setPlanSeleccionado(plan);
    setMostrarFormulario(false);
    setMostrarDetalle(true);
    setError("");
  };

  const cerrarVentana = () => {
    setMostrarFormulario(false);
    setMostrarDetalle(false);
    setModoEdicion(false);
    setPlanSeleccionado(null);
    setError("");
  };

  const crearPlan = async (e) => {
    e.preventDefault();

    try {
      setGuardando(true);
      setError("");

      const token =
        localStorage.getItem("access_token");

      const datos = {
        nombre: formulario.nombre,
        velocidad_bajada: Number(
          formulario.velocidad_bajada
        ),
        velocidad_subida: Number(
          formulario.velocidad_subida
        ),
        precio_mensual: Number(
          formulario.precio_mensual
        ),
        descripcion:
          formulario.descripcion || null,
      };

      const respuesta = await fetch(
        `${API_URL}/planes`,
        {
          method: "POST",

          headers: {
            Authorization: `Bearer ${token}`,
            Accept: "application/json",
            "Content-Type": "application/json",
          },

          body: JSON.stringify(datos),
        }
      );

      const resultado = await respuesta.json();

      if (!respuesta.ok) {
        throw new Error(
          resultado.detail ||
            "No se pudo crear el plan"
        );
      }

      cerrarVentana();

      await cargarPlanes();

    } catch (error) {
      console.error(error);
      setError(error.message);

    } finally {
      setGuardando(false);
    }
  };

  const actualizarPlan = async (e) => {
    e.preventDefault();

    if (!planSeleccionado) {
      return;
    }

    try {
      setGuardando(true);
      setError("");

      const token =
        localStorage.getItem("access_token");

      const datos = {
        nombre: formulario.nombre,
        velocidad_bajada: Number(
          formulario.velocidad_bajada
        ),
        velocidad_subida: Number(
          formulario.velocidad_subida
        ),
        precio_mensual: Number(
          formulario.precio_mensual
        ),
        descripcion:
          formulario.descripcion || null,
      };

      const respuesta = await fetch(
        `${API_URL}/planes/${planSeleccionado.id}`,
        {
          method: "PUT",

          headers: {
            Authorization: `Bearer ${token}`,
            Accept: "application/json",
            "Content-Type": "application/json",
          },

          body: JSON.stringify(datos),
        }
      );

      const resultado = await respuesta.json();

      if (!respuesta.ok) {
        throw new Error(
          resultado.detail ||
            "No se pudo actualizar el plan"
        );
      }

      cerrarVentana();

      await cargarPlanes();

    } catch (error) {
      console.error(error);
      setError(error.message);

    } finally {
      setGuardando(false);
    }
  };

  const planesFiltrados = planes.filter(
    (plan) => {
      const texto =
        busqueda.toLowerCase();

      return (
        plan.nombre
          ?.toLowerCase()
          .includes(texto) ||

        plan.descripcion
          ?.toLowerCase()
          .includes(texto)
      );
    }
  );

  const formatearPrecio = (precio) => {
    return new Intl.NumberFormat(
      "es-CO",
      {
        style: "currency",
        currency: "COP",
        maximumFractionDigits: 0,
      }
    ).format(precio);
  };

  return (
    <div className="clientes-page">

      <div className="page-header">

        <div>
          <h1>Planes</h1>

          <p>
            Administra los planes de Internet
            de OPTIRÁPIDO
          </p>
        </div>

        <button
          className="primary-button"
          onClick={abrirNuevoPlan}
        >
          + Nuevo plan
        </button>

      </div>

      {/* FORMULARIO */}

      {mostrarFormulario && (
        <div className="form-card">

          <div className="form-card-header">

            <div>
              <h2>
                {modoEdicion
                  ? "Editar plan"
                  : "Nuevo plan"}
              </h2>

              <p>
                {modoEdicion
                  ? "Modifica la información del plan"
                  : "Crea un nuevo plan de Internet"}
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
                ? actualizarPlan
                : crearPlan
            }
            className="cliente-form"
          >

            <div className="form-grid">

              <div className="form-group">
                <label>
                  Nombre del plan *
                </label>

                <input
                  type="text"
                  name="nombre"
                  value={formulario.nombre}
                  onChange={cambiarCampo}
                  placeholder="Ej: Fibra 300 Mbps"
                  required
                />
              </div>

              <div className="form-group">
                <label>
                  Precio mensual *
                </label>

                <input
                  type="number"
                  name="precio_mensual"
                  value={
                    formulario.precio_mensual
                  }
                  onChange={cambiarCampo}
                  placeholder="80000"
                  min="1"
                  required
                />
              </div>

              <div className="form-group">
                <label>
                  Velocidad de bajada *
                </label>

                <input
                  type="number"
                  name="velocidad_bajada"
                  value={
                    formulario.velocidad_bajada
                  }
                  onChange={cambiarCampo}
                  placeholder="300"
                  min="1"
                  required
                />

                <small>
                  Mbps
                </small>
              </div>

              <div className="form-group">
                <label>
                  Velocidad de subida *
                </label>

                <input
                  type="number"
                  name="velocidad_subida"
                  value={
                    formulario.velocidad_subida
                  }
                  onChange={cambiarCampo}
                  placeholder="100"
                  min="1"
                  required
                />

                <small>
                  Mbps
                </small>
              </div>

              <div className="form-group full-width">
                <label>
                  Descripción
                </label>

                <textarea
                  name="descripcion"
                  value={
                    formulario.descripcion
                  }
                  onChange={cambiarCampo}
                  placeholder="Descripción del plan..."
                  rows="4"
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
                  : "Guardar plan"}
              </button>

            </div>

          </form>

        </div>
      )}

      {/* DETALLE */}

      {mostrarDetalle &&
        planSeleccionado && (
          <div className="form-card">

            <div className="form-card-header">

              <div>
                <h2>
                  {planSeleccionado.nombre}
                </h2>

                <p>
                  Información del plan
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
                  Nombre
                </label>

                <input
                  value={
                    planSeleccionado.nombre
                  }
                  readOnly
                />
              </div>

              <div className="form-group">
                <label>
                  Precio mensual
                </label>

                <input
                  value={formatearPrecio(
                    planSeleccionado.precio_mensual
                  )}
                  readOnly
                />
              </div>

              <div className="form-group">
                <label>
                  Velocidad de bajada
                </label>

                <input
                  value={`${planSeleccionado.velocidad_bajada} Mbps`}
                  readOnly
                />
              </div>

              <div className="form-group">
                <label>
                  Velocidad de subida
                </label>

                <input
                  value={`${planSeleccionado.velocidad_subida} Mbps`}
                  readOnly
                />
              </div>

              <div className="form-group full-width">
                <label>
                  Descripción
                </label>

                <textarea
                  value={
                    planSeleccionado.descripcion ||
                    "Sin descripción"
                  }
                  readOnly
                  rows="4"
                />
              </div>

              <div className="form-group">
                <label>
                  Estado
                </label>

                <input
                  value={
                    planSeleccionado.estado
                      ? "Activo"
                      : "Inactivo"
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
                    planSeleccionado
                  )
                }
              >
                Editar plan
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
                placeholder="Buscar por nombre de plan..."
                value={busqueda}
                onChange={(e) =>
                  setBusqueda(e.target.value)
                }
              />

              <div className="clientes-count">
                {planesFiltrados.length} planes
              </div>

            </div>

            {cargando && (
              <div className="loading">
                Cargando planes...
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
                        <th>Plan</th>
                        <th>Descarga</th>
                        <th>Subida</th>
                        <th>Precio</th>
                        <th>Estado</th>
                        <th>Acciones</th>
                      </tr>
                    </thead>

                    <tbody>

                      {planesFiltrados.map(
                        (plan) => (
                          <tr key={plan.id}>

                            <td>
                              <div className="cliente-name">

                                <strong>
                                  {plan.nombre}
                                </strong>

                                <span>
                                  {plan.descripcion ||
                                    "Sin descripción"}
                                </span>

                              </div>
                            </td>

                            <td>
                              {plan.velocidad_bajada} Mbps
                            </td>

                            <td>
                              {plan.velocidad_subida} Mbps
                            </td>

                            <td>
                              {formatearPrecio(
                                plan.precio_mensual
                              )}
                            </td>

                            <td>
                              <span
                                className={
                                  plan.estado
                                    ? "status active"
                                    : "status inactive"
                                }
                              >
                                {plan.estado
                                  ? "Activo"
                                  : "Inactivo"}
                              </span>
                            </td>

                            <td>

                              <button
                                className="action-button"
                                onClick={() =>
                                  abrirDetalle(plan)
                                }
                              >
                                Ver
                              </button>

                              <button
                                className="action-button"
                                onClick={() =>
                                  abrirEditar(plan)
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

                  {planesFiltrados.length ===
                    0 && (
                    <div className="empty-state">
                      No se encontraron planes.
                    </div>
                  )}

                </div>
              )}

          </>
        )}

    </div>
  );
}

export default Planes;