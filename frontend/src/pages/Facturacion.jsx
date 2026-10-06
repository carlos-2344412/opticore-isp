import { useEffect, useState } from "react";
import "./Facturacion.css";

const API_URL = "http://127.0.0.1:8001";

function Facturacion() {
  const [facturas, setFacturas] = useState([]);
  const [clientes, setClientes] = useState([]);
  const [servicios, setServicios] = useState([]);

  const [cargando, setCargando] = useState(true);
  const [guardando, setGuardando] = useState(false);
  const [error, setError] = useState("");
  const [descargandoMasivo, setDescargandoMasivo] =
    useState(false);

  const fechaActual = new Date();

  const [mesDescarga, setMesDescarga] = useState(
    fechaActual.getMonth() + 1
  );

  const [anioDescarga, setAnioDescarga] = useState(
    fechaActual.getFullYear()
  );

  const [mostrarFormulario, setMostrarFormulario] =
    useState(false);

  const [formulario, setFormulario] = useState({
    cliente_id: "",
    servicio_id: "",
    numero: "",
    concepto: "Servicio de Internet",
    subtotal: "",
    descuento: 0,
    total: "",
    fecha_emision: new Date()
      .toISOString()
      .slice(0, 16),
    fecha_vencimiento: "",
    estado: "pendiente",
    observaciones: "",
  });

  const headers = () => ({
    Authorization: `Bearer ${localStorage.getItem(
      "access_token"
    )}`,
    Accept: "application/json",
  });

  const cargarDatos = async () => {
    try {
      setCargando(true);
      setError("");

      const [facturasRes, clientesRes, serviciosRes] =
        await Promise.all([
          fetch(`${API_URL}/facturas`, {
            headers: headers(),
          }),
          fetch(`${API_URL}/clientes`, {
            headers: headers(),
          }),
          fetch(`${API_URL}/servicios`, {
            headers: headers(),
          }),
        ]);

      if (
        !facturasRes.ok ||
        !clientesRes.ok ||
        !serviciosRes.ok
      ) {
        throw new Error(
          "No se pudieron cargar los datos"
        );
      }

      setFacturas(await facturasRes.json());
      setClientes(await clientesRes.json());
      setServicios(await serviciosRes.json());
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

  const cambiarMonto = (campo, valor) => {
    const subtotal =
      campo === "subtotal"
        ? Number(valor) || 0
        : Number(formulario.subtotal) || 0;

    const descuento =
      campo === "descuento"
        ? Number(valor) || 0
        : Number(formulario.descuento) || 0;

    const total = Math.max(
      0,
      subtotal - descuento
    );

    setFormulario((actual) => ({
      ...actual,
      [campo]: valor,
      total,
    }));
  };

  const crearFactura = async (e) => {
    e.preventDefault();

    try {
      setGuardando(true);
      setError("");

      const respuesta = await fetch(
        `${API_URL}/facturas`,
        {
          method: "POST",
          headers: {
            ...headers(),
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            empresa_id:
              "29241149-5806-4f7d-bf31-13041f187799",

            cliente_id:
              formulario.cliente_id,

            servicio_id:
              formulario.servicio_id || null,

            numero:
              formulario.numero,

            concepto:
              formulario.concepto,

            subtotal:
              Number(formulario.subtotal),

            descuento:
              Number(formulario.descuento),

            total:
              Number(formulario.total),

            fecha_emision:
              formulario.fecha_emision,

            fecha_vencimiento:
              formulario.fecha_vencimiento ||
              null,

            estado:
              formulario.estado,

            observaciones:
              formulario.observaciones || null,
          }),
        }
      );

      const resultado =
        await respuesta.json();

      if (!respuesta.ok) {
        throw new Error(
          resultado.detail ||
            "No se pudo crear la factura"
        );
      }

      setMostrarFormulario(false);

      setFormulario({
        cliente_id: "",
        servicio_id: "",
        numero: "",
        concepto: "Servicio de Internet",
        subtotal: "",
        descuento: 0,
        total: "",
        fecha_emision: new Date()
          .toISOString()
          .slice(0, 16),
        fecha_vencimiento: "",
        estado: "pendiente",
        observaciones: "",
      });

      await cargarDatos();
    } catch (error) {
      console.error(error);
      setError(error.message);
    } finally {
      setGuardando(false);
    }
  };

  const obtenerCliente = (id) => {
    return clientes.find(
      (cliente) => cliente.id === id
    );
  };

  const obtenerServicio = (id) => {
    return servicios.find(
      (servicio) => servicio.id === id
    );
  };

  const formatearMonto = (monto) => {
    return new Intl.NumberFormat("es-CO", {
      style: "currency",
      currency: "COP",
      maximumFractionDigits: 0,
    }).format(Number(monto) || 0);
  };

  const pendientes = facturas.filter(
    (factura) =>
      factura.estado === "pendiente"
  ).length;

  const pagadas = facturas.filter(
    (factura) =>
      factura.estado === "pagada"
  ).length;

  const anuladas = facturas.filter(
    (factura) =>
      factura.estado === "anulada"
  ).length;

  const totalFacturado = facturas
    .filter(
      (factura) =>
        factura.estado !== "anulada"
    )
    .reduce(
      (total, factura) =>
        total + Number(factura.total || 0),
      0
    );

   const serviciosCliente =
    formulario.cliente_id
      ? servicios.filter(
          (servicio) =>
            servicio.cliente_id ===
            formulario.cliente_id
        )
      : [];
  
   const verFacturaPDF = (facturaId) => {
     window.open(
    `   ${API_URL}/facturas/${facturaId}/pdf`,
       "_blank"
     );
   };

   const descargarFacturaPDF = async (factura) => {
     try {
       setError("");

       const respuesta = await fetch(
         `${API_URL}/facturas/${factura.id}/pdf`,
         {
           headers: headers(),
         }
       );

       if (!respuesta.ok) {
         throw new Error(
           "No se pudo descargar la factura"
         );
       }

       const archivo = await respuesta.blob();

       const url = window.URL.createObjectURL(
         archivo
       );

    const enlace =
      document.createElement("a");

    enlace.href = url;

    enlace.download =
      `${factura.numero || "factura"}.pdf`;

    document.body.appendChild(enlace);

    enlace.click();

    enlace.remove();

    window.URL.revokeObjectURL(url);

  } catch (error) {
    console.error(error);
    setError(error.message);
  }
};

  const descargarFacturasMes = async (estado) => {
    try {
      setDescargandoMasivo(true);
      setError("");

      const respuesta = await fetch(
        `${API_URL}/facturas/descargar-mes/zip?mes=${mesDescarga}&anio=${anioDescarga}&estado=${estado}`,
        {
          headers: headers(),
        }
      );

      if (!respuesta.ok) {
        let mensaje =
          "No se pudieron descargar las facturas";

        try {
          const resultado = await respuesta.json();
          mensaje =
            resultado.detail || mensaje;
        } catch {
          // Si la respuesta no viene en JSON,
          // mantenemos el mensaje general.
        }

        throw new Error(mensaje);
      }

      const archivo = await respuesta.blob();

      const url =
        window.URL.createObjectURL(archivo);

      const enlace =
        document.createElement("a");

      const nombres = {
        todas: "TODAS",
        pendiente: "PENDIENTES",
        pagada: "PAGADAS",
      };

      enlace.href = url;
      enlace.download =
        `FACTURAS_${anioDescarga}_${String(
          mesDescarga
        ).padStart(2, "0")}_${nombres[estado]}.zip`;

      document.body.appendChild(enlace);
      enlace.click();
      enlace.remove();

      window.URL.revokeObjectURL(url);
    } catch (error) {
      console.error(error);
      setError(error.message);
    } finally {
      setDescargandoMasivo(false);
    }
  };

  return (
    <div className="facturacion-page">

      <div className="facturacion-header">

        <div>
          <h1>Facturación</h1>

          <p>
            Administra las facturas de
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
          + Nueva factura
        </button>

      </div>

      {error && (
        <div className="error-message">
          {error}
        </div>
      )}


      <section className="facturas-download-card">
        <div className="download-card-header">
          <div>
            <h2>Descargar facturas por mes</h2>
            <p>
              Genera un archivo ZIP con las facturas
              correspondientes al mes seleccionado.
            </p>
          </div>

          <span className="download-icon">
            📦
          </span>
        </div>

        <div className="download-controls">
          <div className="download-select-group">
            <label>Mes</label>

            <select
              value={mesDescarga}
              onChange={(e) =>
                setMesDescarga(
                  Number(e.target.value)
                )
              }
              disabled={descargandoMasivo}
            >
              <option value={1}>Enero</option>
              <option value={2}>Febrero</option>
              <option value={3}>Marzo</option>
              <option value={4}>Abril</option>
              <option value={5}>Mayo</option>
              <option value={6}>Junio</option>
              <option value={7}>Julio</option>
              <option value={8}>Agosto</option>
              <option value={9}>Septiembre</option>
              <option value={10}>Octubre</option>
              <option value={11}>Noviembre</option>
              <option value={12}>Diciembre</option>
            </select>
          </div>

          <div className="download-select-group">
            <label>Año</label>

            <select
              value={anioDescarga}
              onChange={(e) =>
                setAnioDescarga(
                  Number(e.target.value)
                )
              }
              disabled={descargandoMasivo}
            >
              {[2025, 2026, 2027, 2028, 2029, 2030].map(
                (anio) => (
                  <option
                    key={anio}
                    value={anio}
                  >
                    {anio}
                  </option>
                )
              )}
            </select>
          </div>
        </div>

        <div className="download-buttons">
          <button
            className="download-all-button"
            onClick={() =>
              descargarFacturasMes("todas")
            }
            disabled={descargandoMasivo}
          >
            📦 {descargandoMasivo
              ? "Generando ZIP..."
              : "Todas las facturas"}
          </button>

          <button
            className="download-pending-button"
            onClick={() =>
              descargarFacturasMes("pendiente")
            }
            disabled={descargandoMasivo}
          >
            🟡 Solo pendientes
          </button>

          <button
            className="download-paid-button"
            onClick={() =>
              descargarFacturasMes("pagada")
            }
            disabled={descargandoMasivo}
          >
            🟢 Solo pagadas
          </button>
        </div>
      </section>

      <section className="facturacion-stats">

        <div className="factura-stat">
          <span>🧾</span>

          <div>
            <p>Total facturado</p>
            <h2>
              {formatearMonto(
                totalFacturado
              )}
            </h2>
          </div>
        </div>

        <div className="factura-stat">
          <span>⏳</span>

          <div>
            <p>Pendientes</p>
            <h2>{pendientes}</h2>
          </div>
        </div>

        <div className="factura-stat">
          <span>✅</span>

          <div>
            <p>Pagadas</p>
            <h2>{pagadas}</h2>
          </div>
        </div>

        <div className="factura-stat">
          <span>❌</span>

          <div>
            <p>Anuladas</p>
            <h2>{anuladas}</h2>
          </div>
        </div>

      </section>

      {mostrarFormulario && (
        <section className="factura-form-card">

          <h2>Nueva factura</h2>

          <form onSubmit={crearFactura}>

            <div className="form-grid">

              <div className="form-group">
                <label>Cliente</label>

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
                        value={cliente.id}
                      >
                        {cliente.nombre}{" "}
                        {cliente.apellido}
                      </option>
                    )
                  )}
                </select>
              </div>

              <div className="form-group">
                <label>Servicio</label>

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
                        value={servicio.id}
                      >
                        {servicio.tipo} -{" "}
                        {servicio.usuario_pppoe ||
                          "Sin PPPoE"}
                      </option>
                    )
                  )}
                </select>
              </div>

              <div className="form-group">
                <label>Número de factura</label>

                <input
                  type="text"
                  value={
                    formulario.numero
                  }
                  onChange={(e) =>
                    cambiarCampo(
                      "numero",
                      e.target.value
                    )
                  }
                  placeholder="FAC-000002"
                  required
                />
              </div>

              <div className="form-group">
                <label>Concepto</label>

                <input
                  type="text"
                  value={
                    formulario.concepto
                  }
                  onChange={(e) =>
                    cambiarCampo(
                      "concepto",
                      e.target.value
                    )
                  }
                  required
                />
              </div>

              <div className="form-group">
                <label>Subtotal</label>

                <input
                  type="number"
                  min="0"
                  value={
                    formulario.subtotal
                  }
                  onChange={(e) =>
                    cambiarMonto(
                      "subtotal",
                      e.target.value
                    )
                  }
                  placeholder="80000"
                  required
                />
              </div>

              <div className="form-group">
                <label>Descuento</label>

                <input
                  type="number"
                  min="0"
                  value={
                    formulario.descuento
                  }
                  onChange={(e) =>
                    cambiarMonto(
                      "descuento",
                      e.target.value
                    )
                  }
                />
              </div>

              <div className="form-group">
                <label>Total</label>

                <input
                  type="number"
                  value={
                    formulario.total
                  }
                  readOnly
                />
              </div>

              <div className="form-group">
                <label>Fecha de emisión</label>

                <input
                  type="datetime-local"
                  value={
                    formulario.fecha_emision
                  }
                  onChange={(e) =>
                    cambiarCampo(
                      "fecha_emision",
                      e.target.value
                    )
                  }
                  required
                />
              </div>

              <div className="form-group">
                <label>
                  Fecha de vencimiento
                </label>

                <input
                  type="datetime-local"
                  value={
                    formulario.fecha_vencimiento
                  }
                  onChange={(e) =>
                    cambiarCampo(
                      "fecha_vencimiento",
                      e.target.value
                    )
                  }
                  required
                />
              </div>

            </div>

            <div className="form-group">
              <label>Observaciones</label>

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
                placeholder="Observaciones..."
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
                  ? "Creando..."
                  : "Crear factura"}
              </button>

            </div>

          </form>

        </section>
      )}

      <section className="facturas-table-card">

        <div className="table-header">
          <div>
            <h2>Facturas</h2>

            <p>
              {facturas.length} facturas
              registradas
            </p>
          </div>
        </div>

        {cargando ? (
          <div className="empty-state">
            Cargando facturas...
          </div>
        ) : facturas.length === 0 ? (
          <div className="empty-state">
            No hay facturas registradas.
          </div>
        ) : (
          <div className="table-wrapper">

            <table>

              <thead>
                <tr>
                  <th>Número</th>
                  <th>Cliente</th>
                  <th>Servicio</th>
                  <th>Concepto</th>
                  <th>Total</th>
                  <th>Vencimiento</th>
                  <th>Estado</th>
                  <th>Acciones</th>
                </tr>
              </thead>

              <tbody>

                {facturas.map(
                  (factura) => {
                    const cliente =
                      obtenerCliente(
                        factura.cliente_id
                      );

                    const servicio =
                      obtenerServicio(
                        factura.servicio_id
                      );

                    return (
                      <tr
                        key={factura.id}
                      >

                        <td>
                          <strong>
                            {factura.numero}
                          </strong>
                        </td>

                        <td>
                          {cliente
                            ? `${cliente.nombre} ${cliente.apellido || ""}`
                            : "Cliente desconocido"}
                        </td>

                        <td>
                          {servicio
                            ? servicio.usuario_pppoe ||
                              servicio.tipo
                            : "-"}
                        </td>

                        <td>
                          {factura.concepto}
                        </td>

                        <td>
                          <strong>
                            {formatearMonto(
                              factura.total
                            )}
                          </strong>
                        </td>

                        <td>
                          {factura.fecha_vencimiento
                            ? new Date(
                                factura.fecha_vencimiento
                              ).toLocaleDateString(
                                "es-CO"
                              )
                            : "-"}
                        </td>

                        <td>
                          <span
                            className={`status ${
                              factura.estado ===
                              "pagada"
                                ? "active"
                                : factura.estado ===
                                  "anulada"
                                ? "inactive"
                                : "pending"
                            }`}
                          >
                            {factura.estado}
                          </span>
                        </td>

                        <td>
                          <div className="factura-actions">

                           <button
                             className="pdf-view-button"
                             onClick={() =>
                               verFacturaPDF(factura.id)
                             }
                           >
                             👁️ Ver PDF
                           </button>

                           <button
                             className="pdf-download-button"
                             onClick={() =>
                               descargarFacturaPDF(factura)
                             }
                           >
                             ⬇️ Descargar
                           </button>

                         </div>
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

export default Facturacion;