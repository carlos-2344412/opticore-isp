import { useEffect, useState } from "react";
import "./Pagos.css";

const API_URL = "http://127.0.0.1:8001";

function Pagos() {
  const [pagos, setPagos] = useState([]);
  const [clientes, setClientes] = useState([]);
  const [servicios, setServicios] = useState([]);

  const [cargando, setCargando] = useState(true);
  const [error, setError] = useState("");

  const [mostrarFormulario, setMostrarFormulario] =
    useState(false);

  const [guardando, setGuardando] = useState(false);

  const [formulario, setFormulario] = useState({
    cliente_id: "",
    servicio_id: "",
    monto: "",
    fecha_pago: new Date()
      .toISOString()
      .slice(0, 16),
    metodo_pago: "transferencia",
    referencia: "",
    estado: "pagado",
    observaciones: "",
  });

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
        pagosRes,
        clientesRes,
        serviciosRes,
      ] = await Promise.all([
        fetch(`${API_URL}/pagos`, {
          headers,
        }),

        fetch(`${API_URL}/clientes`, {
          headers,
        }),

        fetch(`${API_URL}/servicios`, {
          headers,
        }),
      ]);

      if (
        !pagosRes.ok ||
        !clientesRes.ok ||
        !serviciosRes.ok
      ) {
        throw new Error(
          "No se pudieron cargar los datos"
        );
      }

      const pagosData =
        await pagosRes.json();

      const clientesData =
        await clientesRes.json();

      const serviciosData =
        await serviciosRes.json();

      setPagos(pagosData);
      setClientes(clientesData);
      setServicios(serviciosData);

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

  const cambiarCampo = (campo, valor) => {
    setFormulario((actual) => ({
      ...actual,
      [campo]: valor,
    }));
  };

  const registrarPago = async (e) => {
    e.preventDefault();

    try {
      setGuardando(true);
      setError("");

      const respuesta = await fetch(
        `${API_URL}/pagos`,
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

            servicio_id:
              formulario.servicio_id,

            monto: Number(
              formulario.monto
            ),

            fecha_pago:
              formulario.fecha_pago,

            metodo_pago:
              formulario.metodo_pago,

            referencia:
              formulario.referencia ||
              null,

            estado:
              formulario.estado,

            observaciones:
              formulario.observaciones ||
              null,
          }),
        }
      );

      const resultado =
        await respuesta.json();

      if (!respuesta.ok) {
        throw new Error(
          resultado.detail ||
            "No se pudo registrar el pago"
        );
      }

      setFormulario({
        cliente_id: "",
        servicio_id: "",
        monto: "",
        fecha_pago: new Date()
          .toISOString()
          .slice(0, 16),
        metodo_pago: "transferencia",
        referencia: "",
        estado: "pagado",
        observaciones: "",
      });

      setMostrarFormulario(false);

      await cargarDatos();

    } catch (error) {
      console.error(error);
      setError(error.message);

    } finally {
      setGuardando(false);
    }
  };

  const obtenerNombreCliente = (clienteId) => {
    const cliente = clientes.find(
      (item) =>
        item.id === clienteId
    );

    if (!cliente) {
      return "Cliente desconocido";
    }

    return `${cliente.nombre} ${cliente.apellido}`;
  };

  const obtenerServicio = (servicioId) => {
    return servicios.find(
      (item) =>
        item.id === servicioId
    );
  };

  const formatearMonto = (monto) => {
    return new Intl.NumberFormat(
      "es-CO",
      {
        style: "currency",
        currency: "COP",
        maximumFractionDigits: 0,
      }
    ).format(monto);
  };

  const totalRecaudado = pagos
    .filter(
      (pago) =>
        pago.estado === "pagado"
    )
    .reduce(
      (total, pago) =>
        total + Number(pago.monto),
      0
    );

  const pagosPendientes = pagos.filter(
    (pago) =>
      pago.estado === "pendiente"
  ).length;

  const pagosAnulados = pagos.filter(
    (pago) =>
      pago.estado === "anulado"
  ).length;

  const serviciosCliente =
    formulario.cliente_id
      ? servicios.filter(
          (servicio) =>
            servicio.cliente_id ===
            formulario.cliente_id
        )
      : [];

  return (
    <div className="pagos-page">

      <div className="pagos-header">

        <div>
          <h1>Pagos</h1>

          <p>
            Administra los pagos de
            OPTIRÁPIDO
          </p>
        </div>

        <button
          className="primary-button"
          onClick={() =>
            setMostrarFormulario(
              !mostrarFormulario
            )
          }
        >
          + Registrar pago
        </button>

      </div>

      {error && (
        <div className="error-message">
          {error}
        </div>
      )}

      <section className="payment-stats">

        <div className="payment-stat">
          <span>💰</span>

          <div>
            <p>Total recaudado</p>
            <h2>
              {formatearMonto(
                totalRecaudado
              )}
            </h2>
          </div>
        </div>

        <div className="payment-stat">
          <span>💵</span>

          <div>
            <p>Pagos registrados</p>
            <h2>
              {pagos.length}
            </h2>
          </div>
        </div>

        <div className="payment-stat">
          <span>⏳</span>

          <div>
            <p>Pendientes</p>
            <h2>
              {pagosPendientes}
            </h2>
          </div>
        </div>

        <div className="payment-stat">
          <span>❌</span>

          <div>
            <p>Anulados</p>
            <h2>
              {pagosAnulados}
            </h2>
          </div>
        </div>

      </section>

      {mostrarFormulario && (
        <section className="payment-form-card">

          <h2>
            Registrar nuevo pago
          </h2>

          <form
            onSubmit={registrarPago}
          >

            <div className="form-grid">

              <div className="form-group">
                <label>
                  Cliente
                </label>

                <select
                  value={
                    formulario.cliente_id
                  }
                  onChange={(e) => {
                    cambiarCampo(
                      "cliente_id",
                      e.target.value
                    );

                    cambiarCampo(
                      "servicio_id",
                      ""
                    );
                  }}
                  required
                >
                  <option value="">
                    Seleccionar cliente
                  </option>

                  {clientes.map(
                    (cliente) => (
                      <option
                        key={cliente.id}
                        value={
                          cliente.id
                        }
                      >
                        {cliente.nombre}{" "}
                        {cliente.apellido}
                      </option>
                    )
                  )}
                </select>
              </div>

              <div className="form-group">
                <label>
                  Servicio
                </label>

                <select
                  value={
                    formulario.servicio_id
                  }
                  onChange={(e) =>
                    cambiarCampo(
                      "servicio_id",
                      e.target.value
                    )
                  }
                  disabled={
                    !formulario.cliente_id
                  }
                  required
                >
                  <option value="">
                    Seleccionar servicio
                  </option>

                  {serviciosCliente.map(
                    (servicio) => (
                      <option
                        key={servicio.id}
                        value={
                          servicio.id
                        }
                      >
                        {servicio.tipo} ·{" "}
                        {servicio.usuario_pppoe ||
                          "Sin PPPoE"}
                      </option>
                    )
                  )}
                </select>
              </div>

              <div className="form-group">
                <label>
                  Monto
                </label>

                <input
                  type="number"
                  min="1"
                  value={
                    formulario.monto
                  }
                  onChange={(e) =>
                    cambiarCampo(
                      "monto",
                      e.target.value
                    )
                  }
                  placeholder="80000"
                  required
                />
              </div>

              <div className="form-group">
                <label>
                  Fecha de pago
                </label>

                <input
                  type="datetime-local"
                  value={
                    formulario.fecha_pago
                  }
                  onChange={(e) =>
                    cambiarCampo(
                      "fecha_pago",
                      e.target.value
                    )
                  }
                  required
                />
              </div>

              <div className="form-group">
                <label>
                  Método de pago
                </label>

                <select
                  value={
                    formulario.metodo_pago
                  }
                  onChange={(e) =>
                    cambiarCampo(
                      "metodo_pago",
                      e.target.value
                    )
                  }
                >
                  <option value="transferencia">
                    Transferencia
                  </option>

                  <option value="nequi">
                    Nequi
                  </option>

                  <option value="bancolombia">
                    Bancolombia
                  </option>

                  <option value="daviplata">
                    Daviplata
                  </option>

                  <option value="efectivo">
                    Efectivo
                  </option>

                  <option value="tarjeta">
                    Tarjeta
                  </option>

                  <option value="otro">
                    Otro
                  </option>
                </select>
              </div>

              <div className="form-group">
                <label>
                  Referencia
                </label>

                <input
                  type="text"
                  value={
                    formulario.referencia
                  }
                  onChange={(e) =>
                    cambiarCampo(
                      "referencia",
                      e.target.value
                    )
                  }
                  placeholder="Número de referencia"
                />
              </div>

            </div>

            <div className="form-group">
              <label>
                Observaciones
              </label>

              <textarea
                value={
                  formulario.observaciones
                }
                onChange={(e) =>
                  cambiarCampo(
                    "observaciones",
                    e.target.value
                  )
                }
                placeholder="Observaciones del pago..."
              />
            </div>

            <div className="form-actions">

              <button
                type="button"
                className="secondary-button"
                onClick={() =>
                  setMostrarFormulario(
                    false
                  )
                }
              >
                Cancelar
              </button>

              <button
                type="submit"
                className="primary-button"
                disabled={guardando}
              >
                {guardando
                  ? "Registrando..."
                  : "Registrar pago"}
              </button>

            </div>

          </form>

        </section>
      )}

      <section className="payments-table-card">

        <div className="table-header">
          <div>
            <h2>
              Historial de pagos
            </h2>

            <p>
              {pagos.length} pagos registrados
            </p>
          </div>
        </div>

        {cargando ? (
          <div className="empty-state">
            Cargando pagos...
          </div>
        ) : pagos.length === 0 ? (
          <div className="empty-state">
            No hay pagos registrados.
          </div>
        ) : (
          <div className="table-wrapper">

            <table>

              <thead>
                <tr>
                  <th>Cliente</th>
                  <th>Servicio</th>
                  <th>Monto</th>
                  <th>Fecha</th>
                  <th>Método</th>
                  <th>Referencia</th>
                  <th>Estado</th>
                </tr>
              </thead>

              <tbody>

                {pagos.map(
                  (pago) => {
                    const servicio =
                      obtenerServicio(
                        pago.servicio_id
                      );

                    return (
                      <tr
                        key={pago.id}
                      >

                        <td>
                          <strong>
                            {obtenerNombreCliente(
                              pago.cliente_id
                            )}
                          </strong>
                        </td>

                        <td>
                          {servicio?.usuario_pppoe ||
                            "Servicio"}
                        </td>

                        <td>
                          <strong>
                            {formatearMonto(
                              pago.monto
                            )}
                          </strong>
                        </td>

                        <td>
                          {new Date(
                            pago.fecha_pago
                          ).toLocaleDateString(
                            "es-CO"
                          )}
                        </td>

                        <td>
                          {pago.metodo_pago}
                        </td>

                        <td>
                          {pago.referencia ||
                            "-"}
                        </td>

                        <td>
                          <span
                            className={`status ${
                              pago.estado ===
                              "pagado"
                                ? "active"
                                : pago.estado ===
                                  "anulado"
                                ? "inactive"
                                : "pending"
                            }`}
                          >
                            {pago.estado}
                          </span>
                        </td>

                      </tr>
                    );
                  }
                )}

              </tbody>

            </table>

          </div>
        )}

      </section>

    </div>
  );
}

export default Pagos;