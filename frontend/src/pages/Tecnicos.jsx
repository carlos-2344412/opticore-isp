import React, { useEffect, useState } from "react";

const API_URL = "http://127.0.0.1:8001";

function Tecnicos() {
  const [trabajos, setTrabajos] = useState([]);
  const [cargando, setCargando] = useState(true);
  const [error, setError] = useState("");
  const [subiendoEvidencia, setSubiendoEvidencia] = useState(null);

  // ==========================================
  // CARGAR TRABAJOS DEL TÉCNICO
  // ==========================================

  const cargarTrabajos = async () => {
    try {
      setCargando(true);
      setError("");

      const token = localStorage.getItem("access_token");

      const respuesta = await fetch(
        `${API_URL}/soporte/mis-trabajos`,
        {
          headers: {
            Authorization: `Bearer ${token}`,
            Accept: "application/json",
          },
        }
      );

      if (!respuesta.ok) {
        throw new Error(
          "No se pudieron cargar los trabajos"
        );
      }

      const datos = await respuesta.json();

      // ==========================================
      // CARGAR EVIDENCIAS DE CADA TRABAJO
      // ==========================================

      const trabajosConEvidencias =
        await Promise.all(
          datos.map(async (trabajo) => {
            try {
              const respuestaEvidencias =
                await fetch(
                  `${API_URL}/soporte/${trabajo.id}/evidencias`,
                  {
                    headers: {
                      Authorization: `Bearer ${token}`,
                      Accept: "application/json",
                    },
                  }
                );

              if (!respuestaEvidencias.ok) {
                return {
                  ...trabajo,
                  evidencias: [],
                };
              }

              const evidencias =
                await respuestaEvidencias.json();

              return {
                ...trabajo,
                evidencias,
              };
            } catch (error) {
              console.error(
                "Error cargando evidencias:",
                error
              );

              return {
                ...trabajo,
                evidencias: [],
              };
            }
          })
        );

      setTrabajos(trabajosConEvidencias);

    } catch (error) {
      console.error(error);
      setError(error.message);
    } finally {
      setCargando(false);
    }
  };

  // ==========================================
  // CARGAR AL ENTRAR AL PANEL
  // ==========================================

  useEffect(() => {
    cargarTrabajos();
  }, []);

  // ==========================================
  // CAMBIAR ESTADO DEL TRABAJO
  // ==========================================

  const cambiarEstado = async (
    trabajoId,
    nuevoEstado
  ) => {
    try {
      const token =
        localStorage.getItem("access_token");

      const respuesta = await fetch(
        `${API_URL}/soporte/${trabajoId}`,
        {
          method: "PUT",
          headers: {
            Authorization: `Bearer ${token}`,
            "Content-Type": "application/json",
            Accept: "application/json",
          },
          body: JSON.stringify({
            estado: nuevoEstado,
          }),
        }
      );

      if (!respuesta.ok) {
        const resultado =
          await respuesta.json();

        throw new Error(
          resultado.detail ||
            "No se pudo actualizar el trabajo"
        );
      }

      const trabajoActualizado =
        await respuesta.json();

      setTrabajos((trabajosActuales) =>
        trabajosActuales.map((trabajo) =>
          trabajo.id ===
          trabajoActualizado.id
            ? {
                ...trabajoActualizado,
                evidencias:
                  trabajo.evidencias || [],
              }
            : trabajo
        )
      );

    } catch (error) {
      console.error(error);
      alert(error.message);
    }
  };

  // ==========================================
  // SUBIR EVIDENCIA
  // ==========================================

  const subirEvidencia = async (
    trabajoId,
    archivo
  ) => {
    if (!archivo) {
      return;
    }

    try {
      setSubiendoEvidencia(trabajoId);

      const token =
        localStorage.getItem("access_token");

      const formulario = new FormData();

      formulario.append(
        "archivo",
        archivo
      );

      const respuesta = await fetch(
        `${API_URL}/soporte/${trabajoId}/evidencias`,
        {
          method: "POST",
          headers: {
            Authorization: `Bearer ${token}`,
          },
          body: formulario,
        }
      );

      const resultado =
        await respuesta.json();

      if (!respuesta.ok) {
        throw new Error(
          resultado.detail ||
            "No se pudo subir la evidencia"
        );
      }

      alert(
        "📸 Evidencia subida correctamente"
      );

      // ==========================================
      // VOLVER A CARGAR LAS EVIDENCIAS
      // ==========================================

      await cargarTrabajos();

    } catch (error) {
      console.error(error);
      alert(error.message);
    } finally {
      setSubiendoEvidencia(null);
    }
  };

  // ==========================================
  // GENERAR DIRECCIÓN PARA GOOGLE MAPS
  // ==========================================

  const obtenerDireccionMaps = (trabajo) => {
    const partes = [
      trabajo.cliente_direccion,
      trabajo.cliente_barrio,
      trabajo.cliente_ciudad,
    ].filter(Boolean);

    return encodeURIComponent(
      partes.join(", ")
    );
  };

  // ==========================================
  // PANEL DEL TÉCNICO
  // ==========================================

  return (
    <div>
      <h1>Panel del Técnico</h1>

      <p>
        Bienvenido al panel de trabajo técnico
        de OPTIRÁPIDO.
      </p>

      <div>
        <h2>Mis trabajos</h2>

        {cargando && (
          <p>Cargando trabajos...</p>
        )}

        {error && (
          <p>{error}</p>
        )}

        {!cargando &&
          !error &&
          trabajos.length === 0 && (
            <p>
              No tienes trabajos asignados
              actualmente.
            </p>
          )}

        {!cargando &&
          !error &&
          trabajos.length > 0 && (
            <div>
              {trabajos.map((trabajo) => (
                <div
                  key={trabajo.id}
                  style={{
                    border: "1px solid #ddd",
                    borderRadius: "10px",
                    padding: "20px",
                    marginBottom: "20px",
                  }}
                >
                  <h3>
                    🛠️ Trabajo técnico
                  </h3>

                  {/* =================================
                      INFORMACIÓN DEL CLIENTE
                  ================================== */}

                  <h4>
                    👤 Información del cliente
                  </h4>

                  <p>
                    <strong>Nombre:</strong>{" "}
                    {trabajo.cliente_nombre ||
                      "No disponible"}
                  </p>

                  <p>
                    <strong>
                      📞 Teléfono:
                    </strong>{" "}
                    {trabajo.cliente_telefono ||
                      "No disponible"}
                  </p>

                  <p>
                    <strong>
                      📍 Dirección:
                    </strong>{" "}
                    {trabajo.cliente_direccion ||
                      "No disponible"}
                  </p>

                  <p>
                    <strong>
                      🏙️ Ciudad:
                    </strong>{" "}
                    {trabajo.cliente_ciudad ||
                      "No disponible"}
                  </p>

                  <p>
                    <strong>
                      🏘️ Barrio:
                    </strong>{" "}
                    {trabajo.cliente_barrio ||
                      "No disponible"}
                  </p>

                  <p>
                    <strong>
                      📌 Referencia:
                    </strong>{" "}
                    {trabajo.cliente_referencia ||
                      "No disponible"}
                  </p>

                  {/* =================================
                      ACCIONES DEL CLIENTE
                  ================================== */}

                  <div
                    style={{
                      display: "flex",
                      gap: "10px",
                      flexWrap: "wrap",
                      marginTop: "15px",
                      marginBottom: "20px",
                    }}
                  >
                    {trabajo.cliente_telefono && (
                      <a
                        href={`tel:${trabajo.cliente_telefono}`}
                        style={{
                          display: "inline-block",
                          padding: "10px 15px",
                          borderRadius: "8px",
                          textDecoration: "none",
                          background: "#25D366",
                          color: "white",
                        }}
                      >
                        📞 Llamar al cliente
                      </a>
                    )}

                    {trabajo.cliente_direccion && (
                      <a
                        href={`https://www.google.com/maps/search/?api=1&query=${obtenerDireccionMaps(
                          trabajo
                        )}`}
                        target="_blank"
                        rel="noopener noreferrer"
                        style={{
                          display: "inline-block",
                          padding: "10px 15px",
                          borderRadius: "8px",
                          textDecoration: "none",
                          background: "#4285F4",
                          color: "white",
                        }}
                      >
                        📍 Cómo llegar
                      </a>
                    )}
                  </div>

                  {/* =================================
                      INFORMACIÓN DEL TRABAJO
                  ================================== */}

                  <h4>
                    📝 Información del trabajo
                  </h4>

                  <p>
                    <strong>
                      Descripción:
                    </strong>{" "}
                    {trabajo.descripcion}
                  </p>

                  <p>
                    <strong>
                      Prioridad:
                    </strong>{" "}
                    {trabajo.prioridad}
                  </p>

                  <p>
                    <strong>
                      Estado:
                    </strong>{" "}
                    {trabajo.estado}
                  </p>

                  <p>
                    <strong>
                      Origen:
                    </strong>{" "}
                    {trabajo.origen}
                  </p>

                  {/* =================================
                      EVIDENCIA FOTOGRÁFICA
                  ================================== */}

                  <div
                    style={{
                      marginTop: "20px",
                      marginBottom: "20px",
                      padding: "15px",
                      border: "1px solid #ddd",
                      borderRadius: "8px",
                    }}
                  >
                    <h4>
                      📸 Evidencia fotográfica
                    </h4>

                    {/* SUBIR FOTO */}

                    <input
                      type="file"
                      accept="image/jpeg,image/png,image/webp"
                      capture="environment"
                      disabled={
                        subiendoEvidencia ===
                        trabajo.id
                      }
                      onChange={(evento) => {
                        const archivo =
                          evento.target.files?.[0];

                        if (archivo) {
                          subirEvidencia(
                            trabajo.id,
                            archivo
                          );

                          evento.target.value =
                            "";
                        }
                      }}
                    />

                    {subiendoEvidencia ===
                      trabajo.id && (
                      <p>
                        ⏳ Subiendo evidencia...
                      </p>
                    )}

                    <p
                      style={{
                        fontSize: "14px",
                        color: "#666",
                        marginTop: "8px",
                      }}
                    >
                      Puedes tomar una foto con
                      la cámara del teléfono o
                      seleccionar una imagen.
                    </p>

                    {/* =================================
                        FOTOS REGISTRADAS
                    ================================== */}

                    {trabajo.evidencias &&
                      trabajo.evidencias.length >
                        0 && (
                        <div
                          style={{
                            marginTop: "15px",
                          }}
                        >
                          <h5>
                            📷 Fotos registradas
                          </h5>

                          <div
                            style={{
                              display: "flex",
                              gap: "10px",
                              flexWrap: "wrap",
                            }}
                          >
                            {trabajo.evidencias.map(
                              (evidencia) => (
                                <img
                                  key={
                                    evidencia.id
                                  }
                                  src={`${API_URL}${evidencia.archivo_url}`}
                                  alt="Evidencia del trabajo"
                                  style={{
                                    width: "150px",
                                    height: "150px",
                                    objectFit:
                                      "cover",
                                    borderRadius:
                                      "8px",
                                    border:
                                      "1px solid #ddd",
                                    cursor:
                                      "pointer",
                                  }}
                                  onClick={() =>
                                    window.open(
                                      `${API_URL}${evidencia.archivo_url}`,
                                      "_blank"
                                    )
                                  }
                                />
                              )
                            )}
                          </div>
                        </div>
                      )}
                  </div>

                  {/* =================================
                      TRABAJO ASIGNADO
                  ================================== */}

                  {trabajo.estado ===
                    "asignada" && (
                    <button
                      onClick={() =>
                        cambiarEstado(
                          trabajo.id,
                          "en_proceso"
                        )
                      }
                    >
                      🟡 Iniciar trabajo
                    </button>
                  )}

                  {/* =================================
                      TRABAJO EN PROCESO
                  ================================== */}

                  {trabajo.estado ===
                    "en_proceso" && (
                    <div>
                      <p>
                        🟢 Trabajo en proceso
                      </p>

                      <button
                        onClick={() =>
                          cambiarEstado(
                            trabajo.id,
                            "resuelta"
                          )
                        }
                      >
                        ✅ Marcar como resuelto
                      </button>
                    </div>
                  )}

                  {/* =================================
                      TRABAJO RESUELTO
                  ================================== */}

                  {trabajo.estado ===
                    "resuelta" && (
                    <p>
                      ✅ Trabajo resuelto
                    </p>
                  )}
                </div>
              ))}
            </div>
          )}
      </div>
    </div>
  );
}

export default Tecnicos;